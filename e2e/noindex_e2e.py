"""noindex-respect e2e — plan_noindex-respect.md 의 시나리오 그대로.

로컬 서버에 일반 페이지 / `<meta name="robots" content="noindex">` / `content="none"`
셋을 띄우고(본문은 셋 다 같은 낱말 pyeongsan), crawl 로 수집한 뒤 사용자가 하는 그대로
`python3 -m websearch.indexer` 로 색인·질의한다.
검증: ① noindex·none 페이지는 색인되지 않음 ② 질의 결과에 일반 페이지만
③ 이미 색인된 문서가 뒤늦게 noindex 를 달면 색인에서 빠지고, 그 사실이 출력됨

실행: PYTHONPATH=src python3 e2e/noindex_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOINDEX_HTML = ('<html><head><title>거부</title>'
                '<meta name="robots" content="noindex"></head>'
                '<body><p>pyeongsan 색인 거부 문서</p></body></html>')

PAGES = {
    "/": '<html><title>목차</title><body><p>문서 목록</p>'
         '<a href="/open">1</a><a href="/noindex">2</a><a href="/none">3</a></body></html>',
    "/open": '<html><title>공개 문서</title><body>'
             '<p>pyeongsan 은 색인해도 되는 문서다.</p></body></html>',
    "/noindex": NOINDEX_HTML,
    "/none": '<html><head><title>거부2</title>'
             '<meta name="robots" content="none"></head>'
             '<body><p>pyeongsan 도 색인 거부다.</p></body></html>',
}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            body, ctype = b"User-agent: *\n", "text/plain"
        elif self.path in PAGES:
            body, ctype = PAGES[self.path].encode(), "text/html"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % server.server_address[1]
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))

    def run(*args):
        proc = subprocess.run([sys.executable] + list(args), env=env,
                              capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        return proc.stdout

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        # crawl CLI 는 db 경로 인자가 없어 -c 로 감싼다 (indexer_e2e.py 와 같은 이유)
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], 4, db_path=sys.argv[2])", base + "/", db)
        server.shutdown()

        pages = sqlite3.connect(db).execute("SELECT count(*) FROM pages").fetchone()[0]
        assert pages == 4, "4페이지를 수집해야 한다 — 수집 %d" % pages

        first = run("-m", "websearch.indexer", db)
        # 목차와 /open 만 색인된다. /noindex 와 /none 은 수집돼 있어도 색인 대상이 아니다
        assert "2 문서 색인" in first, "1회차 stdout: %r" % first

        hits = run("-m", "websearch.indexer", db, "--query", "pyeongsan")
        assert base + "/open" in hits, "일반 문서가 안 나왔다: %r" % hits
        assert "/noindex" not in hits, "noindex 문서가 검색됐다: %r" % hits
        assert "/none" not in hits, "none 문서가 검색됐다: %r" % hits

        # 이미 색인된 /open 이 뒤늦게 noindex 를 달았다. CLI 재크롤은 기수집 URL 을
        # 건너뛰므로(digest [5], 별도 사안) pages.html 을 직접 갱신해 상황만 만든다.
        conn = sqlite3.connect(db)
        conn.execute("UPDATE pages SET html=? WHERE url=?", (NOINDEX_HTML, base + "/open"))
        conn.commit()
        conn.close()

        second = run("-m", "websearch.indexer", db)
        assert "0 문서 색인" in second, "2회차 stdout: %r" % second
        assert "1 문서 색인 제외" in second, "제거를 알리지 않았다: %r" % second

        gone = run("-m", "websearch.indexer", db, "--query", "pyeongsan")
        assert base not in gone, "색인에서 빠졌어야 하는데 검색됐다: %r" % gone
        assert gone.strip(), "무결과인데 아무것도 출력하지 않았다"

    print("e2e 통과 — 수집 4페이지 중 2문서 색인(noindex·none 제외), "
          "질의는 공개 문서만, 뒤늦은 noindex 는 색인에서 제거되고 출력으로 알림")


if __name__ == "__main__":
    main()
