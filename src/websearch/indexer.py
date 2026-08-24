"""수집 페이지를 FTS5 역색인에 넣는다. 재실행은 증분 — 새 문서만 색인한다."""
import os
import sqlite3

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
