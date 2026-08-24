"""crawler-core e2e — plan_crawler-core.md 의 시나리오 그대로.

로컬 서버(페이지 20개, /secret robots 차단)에 시드 1개로 CLI 를 실제 실행한다.
검증: ① 15페이지 수집(stdout·exit code·DB) ② 차단 URL 요청 0건
③ 같은 도메인 페이지 요청 간격 ≥ 1초 (robots.txt 는 도메인당 1회의 메타 요청이라 제외)

실행: PYTHONPATH=src python3 e2e/crawl_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUEST_LOG = []  # (시각, 경로)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        REQUEST_LOG.append((time.monotonic(), self.path))
        if self.path == "/robots.txt":
            body = b"User-agent: *\nDisallow: /secret\n"
            ctype = "text/plain"
        elif self.path.startswith("/secret"):
            body, ctype = b"blocked", "text/html"
        elif self.path == "/":
            anchors = "".join('<a href="/p%d">%d</a>' % (i, i) for i in range(1, 20))
            body = ('<html>%s<a href="/secret/x">s</a></html>' % anchors).encode()
            ctype = "text/html"
        elif self.path.startswith("/p"):
            body, ctype = b"<html>leaf</html>", "text/html"
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
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"), WEBSEARCH_DB=db)
        # CLI 는 db 경로 인자가 없어 crawl() 을 -c 로 감싼다 — 사용자 실행 형태(모듈 실행) 유지
        proc = subprocess.run(
            [sys.executable, "-c",
             "import sys; from websearch.crawl import crawl; "
             "print('수집 %d 페이지' % crawl([sys.argv[1]], 15, db_path=sys.argv[2]))",
             base + "/", db],
            env=env, capture_output=True, text=True, timeout=120)
        server.shutdown()

        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        assert "수집 15 페이지" in proc.stdout, "stdout: %r" % proc.stdout
        rows = sqlite3.connect(db).execute(
            "SELECT count(*) FROM pages WHERE html IS NOT NULL").fetchone()[0]
        assert rows == 15, "DB 성공 행 %d != 15" % rows

    secret_hits = [p for _, p in REQUEST_LOG if p.startswith("/secret")]
    assert not secret_hits, "robots 차단 URL 요청됨: %s" % secret_hits

    page_times = [t for t, p in REQUEST_LOG if p != "/robots.txt"]
    gaps = [b - a for a, b in zip(page_times, page_times[1:])]
    # 간격 보장은 클라이언트 팝 시점 기준 — 서버 수신 시각에는 왕복 지터가 실려
    # 0.05s 여유를 둔다. 하한을 더 내리면 시나리오를 낮추는 것이다.
    bad = [g for g in gaps if g < 0.95]
    assert not bad, "1초 미만 간격 %d건: %s" % (len(bad), ["%.3f" % g for g in bad])

    print("e2e 통과 — 수집 15, 차단 요청 0, 페이지 요청 %d건 최소 간격 %.3fs"
          % (len(page_times), min(gaps)))


if __name__ == "__main__":
    main()
