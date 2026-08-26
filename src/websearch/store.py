"""수집 페이지 저장. 스키마는 코드가 만든다 (설계 계약: pages 테이블)."""
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url        TEXT PRIMARY KEY,
    html       TEXT,
    status     INTEGER NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


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
            (url, html, status),
        )
        self._db.commit()

    def has(self, url):
        return self._db.execute("SELECT 1 FROM pages WHERE url=?", (url,)).fetchone() is not None

    def get_html(self, url):
        row = self._db.execute("SELECT html FROM pages WHERE url=?", (url,)).fetchone()
        return row[0] if row else None

    def count(self):
        return self._db.execute("SELECT count(*) FROM pages").fetchone()[0]
