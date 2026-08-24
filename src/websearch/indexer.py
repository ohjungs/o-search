"""수집 페이지를 FTS5 역색인에 넣고 질의한다.

재실행은 증분이다 — 새 문서만 색인한다. 다만 색인 거부(meta robots noindex)를
뒤늦게 선언한 문서를 빼기 위해 매 실행 색인 전체를 한 번 훑는다.
"""
import os
import sqlite3
import sys

from . import extract

SCHEMA = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS docs "
    "USING fts5(title, body, url UNINDEXED, tokenize='unicode61', prefix='2 3')"
)


def index_pages(db_path):
    """미색인 pages 행을 추출·삽입하고 넣은 문서 수를 돌려준다.

    meta robots 가 noindex·none 인 문서는 넣지 않고, 이미 색인돼 있으면 뺀다.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)
    db = sqlite3.connect(db_path)
    try:
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
                "INSERT INTO docs(title, body, url) VALUES (?, ?, ?)", (title, body, url)
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
    """색인된 문서 수. DB 가 없거나 색인 전이면 0 (DB 파일을 만들지 않는다)."""
    if not os.path.exists(db_path):
        return 0
    db = sqlite3.connect(db_path)
    try:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='docs'").fetchone():
            return 0
        return db.execute("SELECT count(*) FROM docs").fetchone()[0]
    finally:
        db.close()


def _fts_query(query):
    """어절마다 접두 매치로 재작성한다. 큰따옴표로 감싸 FTS5 문법 문자를 무력화한다."""
    # 제어문자는 먼저 지운다 — NUL 은 큰따옴표 이스케이프를 통과해 FTS5 문자열을 조기 종료시킨다
    terms = query.translate(extract._CONTROL).split()
    return " ".join('"%s"*' % term.replace('"', '""') for term in terms)


def search(db_path, query, limit=10):
    """(url, title, snippet) 목록을 bm25 관련도순으로 돌려준다. 매치가 없으면 빈 목록."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)
    match = _fts_query(query)
    if not match:
        return []
    db = sqlite3.connect(db_path)
    try:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='docs'").fetchone():
            return []  # 아직 색인 전
        return db.execute(
            # -1: 질의어가 실제로 매치된 열에서 스니펫을 뽑는다 (제목만 매치되는 경우)
            "SELECT url, title, snippet(docs, -1, '', '', '…', 20) FROM docs "
            "WHERE docs MATCH ? ORDER BY bm25(docs) LIMIT ?",
            (match, limit),
        ).fetchall()
    finally:
        db.close()


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
        print("DB 파일이 없다: %s" % db_path, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
