"""non-ascii-url e2e — plan_history_007.md 의 `## e2e 시나리오` 그대로.

로컬 서버(한글 경로 페이지 1개 + ASCII 페이지 1개)에 시드 2개로 진짜 crawl() 을 돌린다.
검증: ① 한글 링크를 따라가 저장되고 크롤이 죽지 않는다 (종료 0)
② 한글 표기·퍼센트 표기 두 링크가 pages 1행으로 합쳐진다 (서버 요청도 1건)
③ 살릴 수 없는 시드(서로게이트)만 건너뛰고 나머지는 전부 수집된다

실행: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 e2e/non_ascii_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUEST_LOG = []  # 경로 (서버가 받은 raw 표기 — 퍼센트 인코딩된 채로 온다)
KO_PATH = "/%EA%B0%80.html"  # 서버가 실제로 받는 "가.html" 의 표기


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        REQUEST_LOG.append(self.path)
        if self.path == "/robots.txt":
            body, ctype = b"User-agent: *\nDisallow:\n", "text/plain"
        elif self.path == "/":
            # 같은 페이지를 한글 표기와 퍼센트 표기 두 링크로 건다 (시나리오 2)
            body = ('<html><a href="/가.html">ko</a>'
                    '<a href="%s">pct</a>'
                    '<a href="/ok.html">ascii</a></html>' % KO_PATH).encode()
            ctype = "text/html"
        elif self.path in (KO_PATH, "/ok.html"):
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


# 서로게이트는 argv 로 넘길 수 없다(로케일 인코딩이 거부한다) — 자식 안에서 만든다
CHILD = """
import sys
from websearch.crawl import crawl
base = sys.argv[1]
seeds = [base + "/", base + "/" + chr(0xD800) + ".html"]
print('수집 %d 페이지' % crawl(seeds, 10, db_path=sys.argv[2]))
"""


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % server.server_address[1]
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"),
                   PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run([sys.executable, "-c", CHILD, base, db],
                              env=env, capture_output=True, text=True, timeout=120)
        server.shutdown()

        # 시나리오 1·3 — 크롤이 죽지 않는다. 살릴 수 없는 시드 하나만 빠진다
        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        assert "수집 3 페이지" in proc.stdout, "stdout: %r\nstderr: %s" % (proc.stdout, proc.stderr)
        assert "건너뛴다" in proc.stderr, "건너뛴 시드 보고 없음 — stderr: %r" % proc.stderr

        saved = [r[0] for r in sqlite3.connect(db).execute(
            "SELECT url FROM pages WHERE html IS NOT NULL AND status=200")]

    # 시나리오 1 — 한글 경로 페이지가 ASCII 표기로 저장됐다
    korean = [u for u in saved if u.endswith(KO_PATH)]
    assert len(korean) == 1, "한글 경로 페이지 %d행 != 1: %s" % (len(korean), saved)
    raw = [u for u in saved if not u.isascii()]
    assert not raw, "DB 에 비ASCII URL 이 그대로 들어갔다: %s" % raw

    # 시나리오 2 — 두 표기가 1행. DB 만이 아니라 서버 수신도 1건이어야 진짜 합쳐진 것이다
    assert len(saved) == 3, "수집 %d행 != 3: %s" % (len(saved), saved)
    hits = [p for p in REQUEST_LOG if p == KO_PATH]
    assert len(hits) == 1, "한글 페이지를 %d번 요청했다 (중복 제거 실패)" % len(hits)

    # 시나리오 3 — 건너뛴 시드는 네트워크까지 가지 않았다
    assert set(REQUEST_LOG) == {"/robots.txt", "/", KO_PATH, "/ok.html"}, \
        "예상 밖 요청: %s" % sorted(set(REQUEST_LOG))

    print("e2e 통과 — 수집 3행(한글 경로 %s), 한글 페이지 요청 1건, 서로게이트 시드 1개 건너뜀"
          % korean[0].rsplit("/", 1)[1])


if __name__ == "__main__":
    main()
