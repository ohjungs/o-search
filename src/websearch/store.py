"""수집 페이지 저장. 스키마는 코드가 만든다 (설계 계약: pages 테이블)."""
import os
import sqlite3
import zlib

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url        TEXT PRIMARY KEY,
    html       TEXT,
    status     INTEGER NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

# 재방문 주기. 사양 기능 5 (`docs/specs/concept.md:31` "30일 이내에 재방문")가 이 숫자다.
# **실패를 절반으로 가른 이유**는 4xx·5xx·`status 0` 이 「없는 문서」가 아니라 「그때
# 못 받은 문서」이기 때문이다 — 성공과 같은 30일로 두면 일시 장애가 그만큼 오래
# 결손으로 남고, 더 짧게 두면 죽은 URL 을 성공과 같은 빈도로 두드린다.
# ponytail: 연속 실패 백오프는 안 한다. `pages` 에 실패 횟수를 둘 열이 없고 실물
# 코퍼스에 실패 행이 0건이라 지금 정하면 숫자를 지어내는 것이다 — 실패가 쌓이면 그때 연다.
FRESH_DAYS = 30
RETRY_DAYS = 15


# 원본 HTML 은 DB 의 **78.6%** 였다 (실물 400문서 · 문서당 191KB · 파일 전체 250KB/문서).
# 컨셉 1단계 10만 문서면 25GB, 2단계 100만이면 250GB 라 「2단계까지 단일 머신」
# (`docs/specs/concept.md` 경량 1)이 여기서 깨진다. 되풀이되는 마크업이라 zlib 이 잘 접힌다.
#
#   level   크기     배수    압축      해제
#     1    15.4MB   5.1배   0.7ms   0.13ms
#     6    12.6MB   6.2배   1.7ms   0.11ms   ← 여기
#     9    12.5MB   6.3배   2.5ms   0.10ms
#
# **6 을 고른 이유**는 9 가 0.1배를 더 얻자고 압축을 1.5배 치르기 때문이다. 값은 양쪽 다
# 없다시피 하다 — 질의 시점 해제는 `/passages` 가 읽는 10건 최악이 4.8ms 로 예산 500ms 의
# 1% 미만이고(p95 138ms), 크롤 시점 압축 1.7ms 는 3.67문서/초(272ms/문서) 네트워크
# 바운드의 0.6% 다. 환산: 250KB/문서 → 85KB/문서 (10만 = 8.5GB · 100만 = 85GB).
_LEVEL = 6


def page_html(value):
    """저장된 값을 HTML 문자열로 되돌린다. 없으면 `None`.

    **두 꼴을 다 받는 이유는 마이그레이션을 안 만들기 위해서다.** 압축 이전 행은
    `html` 이 TEXT(`str`) 고 이후 행은 BLOB(`bytes`) 인데, `sqlite3` 가 타입으로
    갈라 주므로 판별 열을 더할 필요가 없다. 덕분에 기존 코퍼스를 변환하지도 버리지도
    않고 그대로 읽고, 재크롤이 자연히 갈아 끼운다.

    **읽는 자리마다 흩어 놓지 않고 여기 하나만 둔다** — `pages.html` 을 읽는 곳이
    `store` 하나가 아니라 `indexer` 의 색인·근거 문단·단건 조회까지 넷이라,
    한 곳이라도 빠뜨리면 그 경로만 조용히 압축분을 원문이라 부른다.
    """
    if isinstance(value, bytes):
        return zlib.decompress(value).decode("utf-8")
    return value


class Store:
    def __init__(self, path):
        parent = os.path.dirname(path)
        if path != ":memory:" and parent:
            os.makedirs(parent, exist_ok=True)
        # WAL: 읽는 연결(indexer)이 쓰는 연결(crawl)을 막지 않는다. timeout: 쓰기끼리
        # 부딪히면 죽는 대신 기다린다. 실측에서 1,700문서째에 크롤을 죽인 게 이거다
        self._db = sqlite3.connect(path, timeout=30)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(SCHEMA)

    def upsert(self, url, html, status):
        self._db.execute(
            "INSERT INTO pages(url, html, status) VALUES (?, ?, ?) "
            "ON CONFLICT(url) DO UPDATE SET html=excluded.html, "
            "status=excluded.status, fetched_at=datetime('now')",
            (url, zlib.compress(html.encode("utf-8"), _LEVEL) if html is not None else None,
             status),
        )
        self._db.commit()

    def has(self, url):
        return self._db.execute("SELECT 1 FROM pages WHERE url=?", (url,)).fetchone() is not None

    def is_fresh(self, url):
        """이 URL 을 **지금 다시 받을 필요가 없나**. 없는 URL 은 신선하지 않다.

        **시각 비교를 SQLite 가 한다** — `upsert` 가 `datetime('now')`(UTC)로 박으므로
        읽는 쪽이 파이썬 시계를 쓰면 타임존·해상도가 어긋나 비교가 조용히 틀린다
        (계획 78 이 `indexer.py:201` 에서 실제로 겪었다). 질의 하나·왕복 하나·시계 하나다.

        `has` 와 합치지 않은 이유는 호출자 둘의 뜻이 다르기 때문이다 — 리다이렉트
        도착지 중복 검사(`crawl.py`)는 「이번 실행에서 이미 저장됐나」라, 신선도를
        섞으면 그 의미가 조용히 바뀐다.
        """
        row = self._db.execute(
            "SELECT 1 FROM pages WHERE url=? AND fetched_at >= datetime("
            "    'now', CASE WHEN status BETWEEN 200 AND 299 THEN ? ELSE ? END)",
            (url, "-%d days" % FRESH_DAYS, "-%d days" % RETRY_DAYS),
        ).fetchone()
        return row is not None

    def get_html(self, url):
        row = self._db.execute("SELECT html FROM pages WHERE url=?", (url,)).fetchone()
        return page_html(row[0]) if row else None

    def count(self):
        return self._db.execute("SELECT count(*) FROM pages").fetchone()[0]
