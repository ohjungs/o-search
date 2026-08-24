"""수집 페이지를 FTS5 역색인에 넣고 질의한다. 재실행은 증분 — 새 문서만 색인한다."""
import os
import sqlite3
import sys

from . import extract

SCHEMA = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS docs "
    "USING fts5(title, body, url UNINDEXED, tokenize='unicode61', prefix='2 3')"
)


def index_pages(db_path):
    """미색인 pages 행을 추출·삽입하고 색인한 문서 수를 돌려준다."""
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
        for url, html in rows:
            title, body = extract.extract_text(html)
            db.execute(
                "INSERT INTO docs(title, body, url) VALUES (?, ?, ?)", (title, body, url)
            )
        db.commit()
        return len(rows)
    finally:
        db.close()


def _fts_query(query):
    """어절마다 접두 매치로 재작성한다. 큰따옴표로 감싸 FTS5 문법 문자를 무력화한다."""
    return " ".join('"%s"*' % term.replace('"', '""') for term in query.split())


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
            "SELECT url, title, snippet(docs, 1, '', '', '…', 20) FROM docs "
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
            print("%d 문서 색인" % index_pages(db_path))
        else:
            for url, title, text in search(db_path, query, limit=10):
                print("%s\n  %s\n  %s" % (title or "(제목 없음)", url, text))
    except FileNotFoundError:
        print("DB 파일이 없다: %s" % db_path, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
