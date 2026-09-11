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

# **발견 큐.** `pages` 와 다른 표인 이유는 그 표가 「받아 본 것」이기 때문이다 —
# 발견은 수집이 아니다. 안 받은 URL 을 `pages` 에 넣으면 계획 84·86 이 429 에서 닫은
# 거짓(「안 받은 것을 받았다고 적는다」)을 다시 여는 것이다.
#
# **이 표가 있어야 규모가 열린다**: 프런티어가 메모리라 매 실행이 시드에서 다시 자라고,
# `--max` 로 끊긴 크롤이 다음 실행에 그 지점을 못 이어받았다. 컨셉 1단계(10만 문서)는
# 한 번에 도는 크기가 아니다. 계획 88 이 `pages` 에 **이미 있는** 미완 URL 만 되찾았고,
# 큐에만 있다가 종료된 URL 은 여전히 잃었다 — 그 절반을 여기서 닫는다.
QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS discovered (
    url  TEXT PRIMARY KEY,
    seen TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

# 재방문 주기. 사양 기능 5 (`docs/specs/concept.md:31` "30일 이내에 재방문")가 이 숫자다.
# **실패를 절반으로 가른 이유**는 4xx·5xx·`status 0` 이 「없는 문서」가 아니라 「그때
# 못 받은 문서」이기 때문이다 — 성공과 같은 30일로 두면 일시 장애가 그만큼 오래
# 결손으로 남는다.
#
# **대가를 정직하게 적는다: 15 < 30 이라 확정적으로 없어진 URL(404·410)을 살아 있는
# URL 의 두 배 빈도로 두드린다.** 크롤 윤리가 갈림길 1순위인데 이 방향은 그 축에
# 역행한다. 그래도 15로 둔 것은 사용자가 위임한 정책(`plan_recrawl.md` 2절 정책 1)이
# 「실패도 다시 받는다」였고, 실물 코퍼스에 실패 행이 **0건**이라 오늘 두드릴 죽은 URL
# 자체가 없어서다. 404·410 만 주기를 따로 둘지는 **사람이 정할 몫으로 남긴다** —
# `_GONE`(`indexer.py`)이 그 둘을 영구 삭제로 보는 것과 방향이 어긋나 있다.
#
# ponytail: 연속 실패 백오프는 안 한다. `pages` 에 실패 횟수를 둘 열이 없고 실물
# 코퍼스에 실패 행이 0건이라 지금 정하면 숫자를 지어내는 것이다 — 실패가 쌓이면 그때 연다.
# ponytail: **`RETRY_DAYS` 는 오늘 시드에서만 닿는다.** 프런티어가 메모리라 매 실행
#           시드에서 다시 자라는데, 부모가 신선하면 팝 지점에서 스킵돼 링크 추출조차
#           안 일어나 자식이 큐에 못 들어온다(반복 474 탐침: 시드 1일·자식 16일 →
#           나간 요청 0건, 시드를 31일로 바꾸면 둘 다 나간다). 자식의 실패 회복은
#           실질적으로 부모의 30일 주기에 묶인다. 여는 조건은 프런티어 영속화다.
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
        self._db.execute(QUEUE_SCHEMA)

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

        **경계는 신선한 쪽이다** — `>=` 라 정확히 30일(15일) 된 문서는 아직 안 받는다.
        사양의 「30일 이내에 재방문」은 30일째를 어느 쪽으로도 읽을 수 있고, 하루의
        차이가 사는 축(크롤 윤리)은 **덜 두드리는 쪽**이라 그쪽을 골랐다.

        **`has` 는 이제 이 술어의 옛 이름이 아니다.** 계획 80 설계는 리다이렉트 도착지
        중복 검사가 「이번 실행에서 이미 저장됐나」라 갈라 뒀는데, `has` 는 실은
        「**언제든** 저장된 적 있나」다 — 재크롤 전에는 둘이 같았고 지금은 갈린다.
        그래서 그 자리도 이 술어를 묻는다(반복 474 리뷰). 「방금 저장한 것」은 여전히
        신선해서 막히므로 한 실행 안의 중복 방지는 그대로다.
        """
        # **429 는 「받은 적 없다」로 읽는다.** 계획 84 가 429 를 더 이상 저장하지
        # 않게 했지만 그 전에 박힌 행이 실물에 **3,686개** 있다(2026-09-09 1만 크롤).
        # 그 행들이 `RETRY_DAYS` 동안 신선하게 읽히면 **받은 적 없는 문서를 15일간
        # 「받았다」로 취급**하는 것이다.
        #
        # **묘비와 다르다**: 404·410 은 「그 자리에 문서가 없다」는 **사실**이라 15일을
        # 지킬 값이 있고, 429 는 「지금은 안 된다」는 **그 시각의 사정**이다. 사정을
        # 사실처럼 붙들 이유가 없다. 그래서 실패 전체를 여는 것이 아니라 429 만 연다 —
        # 전체를 열면 없는 URL 을 매 실행 두드려 고치려던 것과 **반대 방향의** 윤리
        # 문제가 된다(`RejectedIsNotAFetchTest` 의 404 단언이 그 문을 닫는다).
        row = self._db.execute(
            "SELECT 1 FROM pages WHERE url=? AND status != 429 AND fetched_at >= datetime("
            "    'now', CASE WHEN status BETWEEN 200 AND 299 THEN ? ELSE ? END)",
            (url, "-%d days" % FRESH_DAYS, "-%d days" % RETRY_DAYS),
        ).fetchone()
        return row is not None

    def remember(self, urls):
        """발견한 URL 을 큐에 남긴다. 이미 있으면 아무 일도 안 한다.

        **받았다는 뜻이 아니다** — 「이런 URL 이 있더라」까지다. 받고 나면
        `pages` 에 행이 생겨 `unfinished()` 가 알아서 뺀다. 여기서 지우지 않는 이유는
        지우는 자리가 둘이면 한쪽만 고쳐지기 때문이다(판정은 `unfinished` 한 곳).
        """
        self._db.executemany(
            "INSERT OR IGNORE INTO discovered(url) VALUES (?)", [(u,) for u in urls])
        self._db.commit()

    def stored_pages(self, limit=2000):
        """받아 둔 `(url, html)` — 오래 안 본 것부터. 링크를 되살리는 데 쓴다.

        **네트워크를 한 건도 안 쓴다.** 원문이 이미 우리 손에 있으므로 `links.extract`
        를 다시 돌리면 된다(실측 20.8ms/장 · 200장에서 링크 38,794개).
        """
        rows = self._db.execute(
            "SELECT url, html FROM pages WHERE html IS NOT NULL "
            "ORDER BY fetched_at LIMIT ?", (limit,)).fetchall()
        return [(u, page_html(h)) for u, h in rows]

    def unfinished(self, limit=1000, accept=None):
        """다시 받아야 하는데 **큐에 들어올 길이 없는** URL 들. 오래된 순.

        **왜 필요한가**: 프런티어가 메모리라 매 실행 시드에서 다시 자란다. 부모가
        신선하면 팝 지점에서 스킵돼 링크 추출조차 안 일어나고, 그러면 자식은 영영
        큐에 못 들어온다 — 계획 87 이 실물에서 잡은 자리다(429 행 3,807개가 그 상태).
        계획 86 이 「안 신선」으로 읽게 만든 것만으로는 **아무 일도 안 일어났다.**

        **새 표를 안 만드는 이유**: 그 URL 들은 이미 `pages` 에 있고 「다시 받아야
        하나」의 판정자도 이미 있다(`is_fresh`). 없던 것은 그 판정을 **거꾸로 물어보는
        길**뿐이라, 술어를 한 벌 더 쓰지 않고 같은 조건을 부정해서 쓴다 — 두 벌이면
        언젠가 갈린다.

        **상한이 있다.** 미완이 10만이면 프런티어를 그것으로 채우는 것은 크롤이 아니라
        재시도 배치다. 기본 1,000 은 시드가 자라는 속도를 안 덮을 만큼 작다.

        **오래된 순인 이유**: 가장 오래 못 받은 것이 가장 오래 기다린 것이다.
        """
        # 두 갈래를 합친다 — **받았는데 낡은 것**(`pages`)과 **발견만 하고 못 받은 것**
        # (`discovered`). 둘 다 「다시(또는 처음) 받아야 하는데 큐에 들어올 길이 없다」는
        # 같은 상태이고, 부르는 쪽이 둘을 구분할 이유가 없다.
        #
        # `discovered` 쪽은 **신선한 `pages` 행이 있으면 뺀다** — 받고 난 URL 은 더 이상
        # 미완이 아니다. 판정을 `is_fresh` 와 같은 식으로 쓴다(술어 두 벌이면 갈린다).
        # **`accept` 는 상한보다 «먼저» 걸린다.** 안 그러면 범위 밖 URL 이 상한을 다 먹고
        # 정작 일감이 한 건도 안 나온다 — 2026-09-11 실측: 큐 253,026개 중 범위 안 일감이
        # **148,000개**인데 돌려준 1,000개가 전부 범위 밖이라 크롤이 **0장**으로 끝났다.
        # **자르고 거르면 거른 것이 남지 않는다.**
        #
        # **SQL 로 안 거르는 이유**는 범위 판정이 `Frontier.add` 한 곳에 있어야 하기
        # 때문이다(계획 88·91 이 계약으로 못박았다). 여기서 `LIKE` 로 다시 쓰면 판정이
        # 두 벌이 되고 한쪽만 고쳐진다. 대신 **같은 판정식을 받아서** 쓴다.
        rows = self._db.execute(
            "SELECT url FROM pages WHERE status = 429 OR fetched_at < datetime("
            "    'now', CASE WHEN status BETWEEN 200 AND 299 THEN ? ELSE ? END) "
            "UNION "
            "SELECT d.url FROM discovered d LEFT JOIN pages p ON p.url = d.url "
            "WHERE p.url IS NULL OR p.status = 429 OR p.fetched_at < datetime("
            "    'now', CASE WHEN p.status BETWEEN 200 AND 299 THEN ? ELSE ? END) "
            "LIMIT ?",
            ("-%d days" % FRESH_DAYS, "-%d days" % RETRY_DAYS,
             "-%d days" % FRESH_DAYS, "-%d days" % RETRY_DAYS,
             # **거른 뒤에 상한을 걸려면 넉넉히 읽어야 한다.** 범위가 좁으면 앞쪽이
             # 전부 밖일 수 있다 — 실측 64% 가 범위 밖이었고, 앞 1,000개는 **100%** 가
             # 밖이라 일감이 한 건도 안 나왔다. `accept` 가 없으면 옛 동작 그대로다.
             limit if accept is None else limit * 100),
        )
        out = []
        for (url,) in rows:
            if accept is not None and not accept(url):
                continue
            out.append(url)
            if len(out) >= limit:
                break
        return out

    def get_html(self, url):
        row = self._db.execute("SELECT html FROM pages WHERE url=?", (url,)).fetchone()
        return page_html(row[0]) if row else None

    def count(self):
        return self._db.execute("SELECT count(*) FROM pages").fetchone()[0]

    def domains(self):
        """수집된 URL 의 서로 다른 호스트 수.

        **처리량의 천장이 이 수다** — 도메인당 `DOMAIN_INTERVAL`(1초)을 지키므로
        초당 문서 수는 도메인 수를 못 넘는다(2026-09-09 실측: 1·2·4·8 도메인 →
        1.03·2.08·4.40·9.86 문서/초). 크롤 요약이 이것을 같이 말해 주지 않으면
        느린 처리량이 코드 결함으로 오인되고, **그때 손이 가는 곳이 윤리 상수다.**

        SQL 로 호스트를 자른다 — `urls.domain_key` 를 쓰려면 전 행을 파이썬으로
        끌어와야 하고, 여기서 필요한 것은 **정확한 정규화가 아니라 자릿수**다.
        스킴 대소문자나 `www.` 차이로 한둘 갈리는 것은 천장 안내에 무해하다.
        """
        return self._db.execute(
            "SELECT count(DISTINCT substr(url, 1, instr(substr(url, 9), '/') + 7)) "
            "FROM pages"
        ).fetchone()[0]
