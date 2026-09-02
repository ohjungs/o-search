"""수집 페이지를 FTS5 역색인에 넣고 질의한다.

재실행은 증분이다 — 새 문서만 색인한다. 다만 색인 거부(meta robots noindex)를
뒤늦게 선언한 문서를 빼기 위해 매 실행 색인 전체를 한 번 훑는다.
"""
import os
import re
import sqlite3
import sys
import urllib.request

from . import extract

SCHEMA = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS docs "
    "USING fts5(title, body, title_ng, body_ng, url UNINDEXED, "
    "tokenize='porter unicode61', prefix='2 3')"
)

# 한글 런의 문자 2-gram 을 담는 보조 열이 `*_ng` 다. `unicode61` 은 복합어를 한 토큰으로
# 보므로 접두 매치가 뒷부분(`김치찌개보관법` ← `보관법`)에 닿지 못한다.
# **제목과 본문을 따로 담는 것이 핵심이다** — 한 열로 합치면 정답이 꼴찌로 밀린다
# (`docs/design_tokenizer.md` `## 계약` 1). `porter` 는 영어 굴절(tuples ← tuple)용이다.
# `prefix='2 3'` 은 테이블 단위라 `*_ng` 열에도 붙는다 — 2-gram 토큰은 길이가 전부 2 라
# `prefix=2` 는 토큰 자체의 사본이고 `prefix=3` 은 영영 매치되지 않는다. 열별로 끌 수
# 없어서 지불하는 값이고, 색인이 커진 원인 중 하나다 (2026-08-27 리뷰)
_HANGUL_RUN = re.compile(r"[가-힣]+")
# ponytail: 완성형 음절만 본다. 천장 — 옛한글·자모 분리 표기는 잡지 않는다
_HANGUL_GAP = re.compile(r"(?<=[가-힣])\s+(?=[가-힣])")
# ponytail: 공백을 **전부** 지우므로 문장·문단 경계도 넘는다 — `먹는다 물을` 이
# `다물` 이라는 없던 이웃을 만든다(2026-08-27 리뷰 실측). 띄어쓰기 변형(`올레 길`
# ↔ `올레길`)을 잡으려면 어차피 지워야 해서 감수한 값이다. 실제 크롤 산문에서
# 오탐이 보이면 `extract` 가 블록 경계에 한글 아닌 표식을 넣는 쪽으로 올린다
_MARK = "\x02"  # 스니펫이 어느 열에서 왔는지 표시. extract._normalize 가 제어문자를
#                 지우므로 색인 텍스트에는 절대 들어 있지 않다 (extract.py:16,60)
# passages() 가 다시 파싱하는 원문의 상한. serve 의 MAX_QUERY·MAX_PAGE·MAX_PASSAGE 와
# 같은 종류의 자원 상한인데 **자르는 쪽이 여기**라 여기 산다 — serve 는 indexer 를
# import 하므로 반대는 순환이고, `-m websearch.indexer --query` 는 serve 를 안 지난다.
# 단위는 **문자**다: 이 문자열은 sqlite 에서 str 로 나오고, 바이트로 재려면 encode 가
# 한 벌 더 드는 데다(막으려던 그 비용) 코드포인트 중간에서 잘린다. 형제 MAX_PASSAGE
# 도 문자다. 값의 근거 — **숫자 옆에 그 숫자를 낸 입력의 모양을 적는다**(계획 48
# 리뷰 2: 앞의 10만자는 «한글·태그 촘촘» 한 벌에서만 재서 3배 틀렸다). 1,000자당
# 파싱 비용은 모양에 붙는다: 태그 성긴 영문 0.07ms · 한글·태그 촘촘 0.28ms ·
# 낱말마다 <b>/<i>/<em> 이 낀 위키·CMS 출력 0.33~0.35ms. 최악을 0.352 로 잡고 한
# 요청이 문서 PASSAGE_LIMIT(10)건을 재파싱하니 35,000자면 123ms, 500ms 예산의 25%다
# (10만자는 352ms, 70%라 안 쓴다 — 프로세스 밖 HTTP p95 가 실제로 790ms 였다).
# ponytail: 앞에서부터 자른다 — 천장은 «잘린 뒤의 문단은 근거로 못 나온다» 이고,
# 색인은 통짜 본문을 보므로 그 문서는 검색에는 그대로 나온다. 실물에서 긴 문서의
# 뒷부분 근거가 아쉬우면 블록 단위 스트리밍 파서로 올린다(그때 이 값은 지운다).
MAX_PASSAGE_HTML = 35_000


def _bigrams(text):
    """한글 런의 문자 2-gram 을 공백으로 이어 붙인다. 한글이 없으면 빈 문자열.

    한글 **사이의 공백만** 지운다 — `올레 길` 과 `올레길` 이 같은 2-gram 을 내야
    띄어쓰기 변형이 매치된다. 다른 문자를 사이에 두고는 잇지 않는다.
    """
    grams = []
    for run in _HANGUL_RUN.findall(_HANGUL_GAP.sub("", text)):
        grams += [run[i:i + 2] for i in range(len(run) - 1)]
    return " ".join(grams)

# sqlite_master 는 IF NOT EXISTS 를 지우고 나머지를 원문 그대로 보관한다.
# 문자열을 따로 적지 않고 SCHEMA 에서 만든다 — 두 벌이면 언젠가 갈라진다.
_CURRENT_SQL = SCHEMA.replace(" IF NOT EXISTS", "")


class StaleIndexError(RuntimeError):
    """색인이 옛 SCHEMA 로 만들어져 있다. `index_pages()` 를 돌리면 재구축된다."""


class NoCrawlDataError(RuntimeError):
    """`pages` 가 없다 — 크롤한 적 없는 DB 이거나 남의 DB 다.

    "크롤 데이터가 없다" 와 "크롤했는데 색인할 게 0건" 은 다른 상태라 0 으로
    합치지 않는다. 합치면 DB 경로를 잘못 준 것이 조용한 성공으로 보인다.
    """


def _connect(db_path):
    """있는 DB 만 연다. 없으면 FileNotFoundError — 빈 파일을 절대 만들지 않는다.

    `sqlite3.connect(path)` 의 기본값은 `rwc` 라 없는 파일을 만든다. 그래서 예전에는
    `os.path.exists` 로 먼저 보고 열었는데, 그 둘 사이의 창에서 파일이 사라지면 크기 0 의
    빈 DB 가 생겼다 — 그 뒤로는 `exists` 가 참이라 "없다"(503)를 영영 못 낸다.
    `?mode=rw` URI 는 보는 것과 여는 것을 open(2) 한 번으로 합친다.

    **경로는 `pathname2url` 로 인용한다.** 날것으로 끼우면 `a b#c?d.db` 의 `#` 뒤가
    프래그먼트로 잘려 `a b` 라는 **다른 파일**이 열리고, 함께 잘린 `?mode=rw` 가
    기본값 `rwc` 로 떨어져 고치려던 버그가 그대로 부활한다.
    """
    # **빈 경로는 URI 의 특례라 먼저 거른다.** SQLite 는 `file:?mode=rw` 를 "없는 파일" 이
    # 아니라 **이름 없는 임시 DB** 로 읽어 조용히 성공한다 — `mode` 도 안 본다. 그러면
    # `DB_PATH` 가 안 채워진 서버가 503 대신 **200 + 결과 0건**을 낸다(리뷰 실측).
    # `os.path.exists("")` 가 거짓이던 예전 코드에는 이 구멍이 없었다.
    if not db_path:
        raise FileNotFoundError(db_path)
    uri = "file:" + urllib.request.pathname2url(db_path) + "?mode=rw"
    try:
        return sqlite3.connect(uri, timeout=30, uri=True)
    except sqlite3.OperationalError:
        # 없는 파일·권한 거부·디렉터리가 메시지까지 똑같고(`unable to open database file`)
        # `e.sqlite_errorcode` 는 3.11+ 다 — 여기는 3.9 라 파일이 있나로만 가른다.
        # 이 `exists` 는 TOCTOU 가 아니다: 열기는 이미 원자적으로 **실패**했고 남은 일은
        # 그 실패를 어느 칸으로 부를지 분류뿐이다. 오분류해도 파일이 생기지는 않는다.
        if os.path.exists(db_path):
            raise  # 권한·디렉터리·락 — 기다린다고 안 낫는다. serve 가 500 으로 옮긴다
        raise FileNotFoundError(db_path) from None


def _docs_sql(db):
    """`docs` 의 정의 원문. 아직 색인 전이면 None."""
    row = db.execute("SELECT sql FROM sqlite_master WHERE name = 'docs'").fetchone()
    return row[0] if row else None


def index_pages(db_path):
    """미색인 pages 행을 추출·삽입하고 넣은 문서 수를 돌려준다.

    meta robots 가 noindex·none 인 문서는 넣지 않고, 이미 색인돼 있으면 뺀다.
    """
    db = _connect(db_path)
    try:
        # pages 가 없으면 아래 SELECT 가 sqlite3.OperationalError 를 흘려 CLI 가
        # 트레이스백을 낸다. 읽기 직전 한 번만 본다 — 만들지는 않는다(store 몫).
        if not db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'pages'"
        ).fetchone():
            raise NoCrawlDataError(db_path)
        # SCHEMA 는 IF NOT EXISTS 라 정의를 바꿔도 옛 DB 는 옛 정의로 조용히 남는다.
        # docs 는 pages 에서 파생된 색인이므로 버리고 다시 만들어도 원본이 사라지지 않는다.
        if _docs_sql(db) not in (None, _CURRENT_SQL):
            # sqlite3 는 DDL 을 암묵 트랜잭션에 넣지 않는다 — 명시로 열지 않으면 중단 시
            # DROP/CREATE 만 커밋되고 INSERT 만 롤백돼 옛 색인이 0행으로 남는다.
            # DROP **앞**이어야 한다. 뒤면 DROP 은 이미 커밋된 뒤다.
            db.execute("BEGIN")
            db.execute("DROP TABLE docs")
        db.execute(SCHEMA)
        # ponytail: 전표 스캔. 10만 문서에서 느려지면 pages 에 색인 상태 컬럼을 둔다
        rows = db.execute(
            "SELECT url, html FROM pages "
            "WHERE html IS NOT NULL AND url NOT IN (SELECT url FROM docs)"
        ).fetchall()
        indexed = 0
        for url, html in rows:
            if extract.is_noindex(html):
                continue  # 색인 거부 선언 — 크롤 윤리 축, robots.txt 와 같다
            title, body = extract.extract_text(html)
            db.execute(
                "INSERT INTO docs(title, body, title_ng, body_ng, url) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, body, _bigrams(title), _bigrams(body), url),
            )
            indexed += 1
        # 이미 색인된 문서가 뒤늦게 noindex 를 선언했으면 뺀다. 위 증분 조건이
        # 기색인 문서를 아예 쳐다보지 않으므로 경로가 따로 필요하다.
        # ponytail: 매 실행 색인 전수 조인. LIKE 로 후보를 SQLite 안에서 걸러 두었고,
        #           색인 상태 컬럼이 생기는 recrawl 계획에서 증분으로 바꾼다
        for url, html in db.execute(
            "SELECT d.url, p.html FROM docs d JOIN pages p ON p.url = d.url "
            "WHERE p.html LIKE '%robots%'"
        ).fetchall():
            if extract.is_noindex(html):
                db.execute("DELETE FROM docs WHERE url = ?", (url,))
        db.commit()
        return indexed
    finally:
        db.close()


def _doc_count(db_path):
    """쓸 수 있는 색인의 문서 수. DB 가 없거나 색인 전이면 0 (DB 파일을 만들지 않는다).

    **옛 정의로 남은 docs 도 0 이다** — index_pages() 가 통째로 버릴 것이고,
    세어 두면 재구축이 `before + indexed - after` 에서 제거로 둔갑한다.
    `search()` 도 옛 색인은 쓸 수 없는 것으로 본다(StaleIndexError) — 같은 기준이다.
    """
    try:
        db = _connect(db_path)
    except FileNotFoundError:
        return 0  # "아직 크롤 전" 은 이 함수에서 오류가 아니다 — CLI 가 before 로 쓴다
    try:
        if _docs_sql(db) != _CURRENT_SQL:
            return 0
        return db.execute("SELECT count(*) FROM docs").fetchone()[0]
    finally:
        db.close()


def _fts_query(query):
    """어절마다 (접두 매치 OR 2-gram 구절) 을 만들고 AND 로 잇는다.

    **어절 단위인 것이 핵심이다.** 질의를 통째로 이어 붙여 하나의 구절로 만들면
    2-gram 분기가 어절이 문서 안에 **그 순서로 붙어 있을 때만** 살아서, `냉장 보관법`
    처럼 어순만 다른 질의가 0건이 된다 (2026-08-27 리뷰). 어절마다 갈라 두면
    AND 계약이 구조적으로 유지되므로 "질의가 전부 한글일 때만" 이라는 조건도 필요 없다 —
    한글이 없는 어절은 자기 접두 분기만 낸다.
    """
    # 제어문자는 먼저 지운다 — NUL 은 큰따옴표 이스케이프를 통과해 FTS5 문자열을 조기 종료시킨다
    parts = []
    for term in query.translate(extract._CONTROL).split():
        plain = '"%s"*' % term.replace('"', '""')
        grams = _bigrams(term).split()  # 한 글자·비한글 어절은 비어 있다
        if not grams:
            parts.append(plain)
            continue
        phrase = " + ".join('"%s"' % gram for gram in grams)
        # 두 열을 `{title_ng body_ng}` 하나로 묶으면 안 된다 — 한국어 포함률이
        # 20/20 에서 17/20 으로 떨어진다(정답이 13위로 밀린다). 설계가 열을 나눈
        # 이유가 질의 쪽에도 그대로 걸린다 (`docs/design_tokenizer.md` `## 계약` 1)
        parts.append("(%s OR {title_ng} : %s OR {body_ng} : %s)"
                     % (plain, phrase, phrase))
    return " AND ".join(parts)


def search(db_path, query, limit=10, offset=0):
    """(url, title, snippet) 목록을 bm25 관련도순으로 돌려준다. 매치가 없으면 빈 목록.

    offset 은 앞에서 건너뛸 개수다 — 기본값이 있어 기존 호출부는 그대로 돈다.
    """
    match = _fts_query(query)
    db = _connect(db_path)
    try:
        sql = _docs_sql(db)
        if sql is None:
            return []  # 아직 색인 전
        if sql != _CURRENT_SQL:
            # 빈 목록을 내면 "결과 0건" 과 구분되지 않는다 — 원인이 다르니 소리를 낸다
            raise StaleIndexError(db_path)
        # 무토큰 질의(제어문자·따옴표만)의 조기 반환은 **DB 상태 판정 뒤**다.
        # 앞에 두면 판정이 질의 내용에 달린다 — 같은 고장난 DB 가 `q=김치` 면 500,
        # `q=%01` 이면 200 으로 갈린다. 옛 색인 검사 뒤인 것도 같은 이유다(변이 M6).
        # 비용은 무토큰 질의가 연결 하나를 여는 것뿐이다(실측 0.066ms/회).
        if not match:
            return []
        rows = db.execute(
            # 스니펫은 title(0)·body(1) 에서만 뽑는다. `-1` 은 **매치된 열 중 가장 왼쪽**을
            # 고르는데, 2-gram 으로만 매치된 문서는 title_ng 가 뽑혀 화면에
            # `김치 치찌 찌개` 가 나온다 (`docs/design_tokenizer.md` `## 가정`).
            # rowid 로 동점을 가른다 — 같은 틀로 찍힌 페이지들은 bm25 가 정확히 같고,
            # 2차 키가 없으면 페이지 사이 순서가 정해지지 않아 결과가 겹치거나 빠질 수 있다.
            # **url 이 아니라 rowid 인 이유는 값이다**: 2만 문서에서 url 은 p50 을 13→27ms 로
            # 두 배로 만들고(정렬을 새로 한다), rowid 는 12.8ms — 어차피 나오던 순서라 공짜다.
            "SELECT url, title, snippet(docs, 0, ?, '', '…', 20), "
            "snippet(docs, 1, ?, '', '…', 20) FROM docs "
            "WHERE docs MATCH ? ORDER BY bm25(docs), rowid LIMIT ? OFFSET ?",
            (_MARK, _MARK, match, limit, offset),
        ).fetchall()
        # 제목이 매치됐으면 제목에서, 아니면 본문에서. 둘 다 아니면(2-gram 전용 매치)
        # 본문 앞부분이 나온다 — 사람이 읽을 수 있는 원문이라는 것이 요점이다.
        # 본문이 아예 없는 문서(링크 페이지)는 빈 문자열이 되므로 제목으로 떨어진다.
        return [(url, title, (t_sn if _MARK in t_sn else b_sn or t_sn).replace(_MARK, ""))
                for url, title, t_sn, b_sn in rows]
    finally:
        db.close()


def passages(db_path, query, limit=10):
    """(url, title, position, text) 목록 — `search()` 문서 순 그대로, 문서당 최대 1문단.

    문단 경계는 색인에 없다(`docs.body` 는 통짜 텍스트다). `pages.html` 을 다시
    파싱해 얻는다 — 색인·스키마·`docs` 는 한 글자도 안 건드린다.

    **`search()` 를 부르는 것이 핵심이다.** 자체 질의를 짜면 503(없는 DB·옛 색인)·
    500(손상) 판정을 한 벌 더 갖게 되고, 계획 47 이 한곳에 모은 것이 다시 흩어진다.
    `pages` 를 읽으려 연결을 하나 더 여는 값(0.04ms)이 그보다 싸다.

    **매치된 블록이 없는 문서는 안 낸다** — 제목만 매치됐거나 2-gram 이 문단 경계를
    넘어 매치된 문서가 그렇다. 첫 블록으로 대신하면 사양 기능 8(근거 정확도)이
    첫 줄에서 무너진다. `position` 은 `extract_blocks()` 결과의 순번(0부터)이다.

    문서당 앞 `MAX_PASSAGE_HTML` 자만 다시 파싱한다 — **그 뒤의 문단은 근거로 안
    나온다**(검색 결과에는 그대로 나온다. 색인은 통짜 본문을 본다).
    """
    hits = search(db_path, query, limit=limit)
    # 고르는 규칙 — 질의어와 그 2-gram(`_bigrams`)을 가장 많이 담은 블록. 색인이
    # 매치에 쓰는 것과 같은 재료라 "왜 이 문서가 나왔나" 와 근거가 갈리지 않는다
    needles = []
    for term in query.lower().translate(extract._CONTROL).split():
        needles.append(term)
        needles += _bigrams(term).split()
    found = []
    db = _connect(db_path)
    try:
        for url, title, _snippet in hits:
            row = db.execute("SELECT html FROM pages WHERE url = ?", (url,)).fetchone()
            if not row or not row[0]:
                continue  # 원본이 사라진 문서 — 지어내지 않고 뺀다
            best = None
            for pos, block in enumerate(
                    extract.extract_blocks(row[0][:MAX_PASSAGE_HTML])):
                low = block.lower()
                score = sum(low.count(n) for n in needles)
                # 등호가 아니라 부등호다 — 동점이면 먼저 나온 블록이 남는다
                if score and (best is None or score > best[0]):
                    best = (score, pos, block)
            if best:
                found.append((url, title, best[1], best[2]))
    finally:
        db.close()
    return found


def main(argv):
    args = list(argv[1:])
    query = None
    if "--query" in args:
        i = args.index("--query")
        if i + 1 >= len(args):
            print("--query 는 질의 문자열 하나를 받는다", file=sys.stderr)
            return 2
        query = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        print("usage: python3 -m websearch.indexer <db> [--query Q]", file=sys.stderr)
        return 2
    db_path = args[0]
    try:
        if query is None:
            before = _doc_count(db_path)
            indexed = index_pages(db_path)
            print("%d 문서 색인" % indexed)
            # 색인이 조용히 줄어들면 "아무 일도 없었음" 과 구분할 수 없다
            removed = before + indexed - _doc_count(db_path)
            if removed:
                print("%d 문서 색인 제외 — noindex 선언" % removed)
        else:
            hits = search(db_path, query, limit=10)
            if not hits:
                print("결과 없음")  # 침묵하면 "결과 0건" 과 "명령이 깨짐" 을 구분할 수 없다
            for url, title, text in hits:
                print("%s\n  %s\n  %s" % (title or "(제목 없음)", url, text))
    except FileNotFoundError:
        # 아래 넷은 **환경이 안 된 것**이라 rc 1 이다(명령줄 오류 2 와 가른다).
        # 안 잡힌 예외를 파이썬이 이미 1 로 끝내므로, 손으로 잡은 갈래만 2 로 갈라
        # 두면 새 `except` 를 안 단 환경 오류마다 계약이 갈린다. 계약표는 `README` 에 있다.
        print("DB 파일이 없다: %s" % db_path, file=sys.stderr)
        return 1
    except NoCrawlDataError:
        # 트레이스백은 복구법을 안 알려 준다 — StaleIndexError 와 같은 관용구다
        print("크롤 데이터가 없다(pages 테이블 없음): %s\n"
              "먼저 크롤한다: python3 -m websearch.crawl <시드 URL>" % db_path,
              file=sys.stderr)
        return 1
    except StaleIndexError:
        # 트레이스백은 복구법을 안 알려 준다 — docstring 에 적어 둔 것을 화면에 낸다
        print("색인이 옛 정의로 남아 있다. 먼저 색인을 다시 돌린다: "
              "python3 -m websearch.indexer %s" % db_path, file=sys.stderr)
        return 1
    except sqlite3.DatabaseError as e:
        # 트레이스백은 복구법을 안 알려 준다 — StaleIndexError 와 같은 관용구다.
        # 락은 안내가 다르다: 30초를 기다리고도 안 풀린 것이라 답이 "나중에 다시" 다.
        # 나머지(손상·비 DB 파일)를 락으로 오인하면 오진이므로 원문을 그대로 보인다
        if "locked" in str(e):
            print("DB 가 잠겨 있다 — 크롤이 끝난 뒤 다시 돌린다: %s" % db_path, file=sys.stderr)
        else:
            print("DB 를 열 수 없다: %s — %s" % (db_path, e), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        # **KeyboardInterrupt 만** 잡는다 — BaseException 으로 넓히면 SystemExit 까지
        # 삼켜 다른 계약이 된다. "색인은 바뀌지 않았다" 는 재구축이 한 트랜잭션이 된
        # 뒤에야 두 갈래(정상 색인·재구축) 모두에서 참이다. rc 는 crawl 과 같은 130
        print("중단 — 색인은 바뀌지 않았다", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
