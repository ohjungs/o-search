"""search-api e2e — plan_search-api.md 의 시나리오 그대로.

로컬 서버 페이지를 crawl 로 수집·색인한 뒤, **사용자가 하는 그대로**
`python3 -m websearch.serve <db> --port 0` 로 API 를 띄우고 HTTP 로 때린다.
단위 테스트는 make_server() 를 스레드로 부르므로 CLI 진입점과 crawl→색인→서빙
전체 경로는 여기서만 통째로 돈다.

검증: ① q=김치 200·정답 URL ② page=2 가 1페이지와 안 겹치고 has_next 가 맞다
③ q 없음 400 / 없는 경로 404 / POST 501 ④ 어느 응답에도 트레이스백이 없다

실행: PYTHONPATH=src python3 e2e/search_api_e2e.py
"""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = 14  # 목차 + 14 = 15문서. 2페이지가 나오되 딱 떨어지지 않는다

PAGES = {
    "/": '<html><title>목차</title><body><p>김치 문서 목록</p>'
         + "".join('<a href="/doc%02d">%d</a>' % (i, i) for i in range(DOCS))
         + '</body></html>',
}
PAGES.update({
    "/doc%02d" % i: '<html><title>김치 %02d</title><body>'
                    '<p>%s 배추를 절여 담근다.</p></body></html>' % (i, "김치 " * (i + 1))
    for i in range(DOCS)
})


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


def request(url, method="GET"):
    """(상태코드, 본문 문자열). 4xx·5xx 도 예외 대신 값으로 돌려준다."""
    req = urllib.request.Request(url, method=method,
                                 data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def main():
    origin = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=origin.serve_forever, daemon=True).start()
    site = "http://127.0.0.1:%d" % origin.server_address[1]
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))

    def run(*args):
        proc = subprocess.run([sys.executable] + list(args), env=env,
                              capture_output=True, text=True, timeout=180)
        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        return proc.stdout

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        # crawl CLI 는 db 경로 인자가 없어 -c 로 감싼다 (indexer_e2e.py 와 같은 이유)
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], %d, db_path=sys.argv[2])" % (DOCS + 1), site + "/", db)
        origin.shutdown()

        indexed = run("-m", "websearch.indexer", db)
        assert "%d 문서 색인" % (DOCS + 1) in indexed, "색인 stdout: %r" % indexed

        # 사용자가 하는 그대로 — CLI 로 띄우고 stdout 에서 실제 포트를 읽는다
        server = subprocess.Popen([sys.executable, "-m", "websearch.serve", db, "--port", "0"],
                                  env=env, stdout=subprocess.PIPE, text=True)
        try:
            line = server.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            api = line.split("/search")[0]

            q = urllib.parse.quote("김치")
            status, raw = request("%s/search?q=%s" % (api, q))
            assert status == 200, "q=김치 → %d" % status
            assert "김치" in raw and "\\u" not in raw, "한국어가 이스케이프됐다: %r" % raw[:120]
            first = json.loads(raw)
            assert len(first["results"]) == 10, "1페이지 %d건" % len(first["results"])
            assert first["has_next"] is True, "15문서인데 has_next 가 거짓이다"
            assert any(site + "/doc" in r["url"] for r in first["results"]), first["results"]

            second = json.loads(request("%s/search?q=%s&page=2" % (api, q))[1])
            assert second["page"] == 2 and second["has_next"] is False, second
            assert len(second["results"]) == 5, "2페이지 %d건" % len(second["results"])
            overlap = {r["url"] for r in first["results"]} & {r["url"] for r in second["results"]}
            assert not overlap, "페이지가 겹친다: %s" % overlap

            for path, expect, method in [("/search", 400, "GET"),
                                         ("/search?q=%s&page=0" % q, 400, "GET"),
                                         ("/search?q=%s&page=101" % q, 400, "GET"),
                                         (urllib.parse.quote("/없는경로"), 404, "GET"),
                                         ("/search?q=%s" % q, 501, "POST")]:
                status, raw = request(api + path, method)
                assert status == expect, "%s %s → %d (기대 %d)" % (method, path, status, expect)
                assert "Traceback" not in raw, "%s 응답에 트레이스백: %r" % (path, raw[:200])
        finally:
            server.terminate()
            server.wait(timeout=20)

    perf = run(os.path.join(ROOT, "e2e", "perf_search.py"), "500", "30")
    assert "p95" in perf, "측정이 숫자를 안 냈다: %r" % perf

    print("e2e 통과 — %d문서 색인, CLI 로 띄운 API 가 1페이지 10건(has_next 참)·"
          "2페이지 5건(거짓)·겹침 0, 400/404/501 이 트레이스백 없이 나온다" % (DOCS + 1))
    print(perf.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
