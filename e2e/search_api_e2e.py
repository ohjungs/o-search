"""search-api e2e — plan_search-api.md 의 시나리오 그대로.

로컬 서버 페이지를 crawl 로 수집·색인한 뒤, **사용자가 하는 그대로**
`python3 -m websearch.serve <db> --port 0` 로 API 를 띄우고 HTTP 로 때린다.
단위 테스트는 make_server() 를 스레드로 부르므로 CLI 진입점과 crawl→색인→서빙
전체 경로는 여기서만 통째로 돈다.

검증: ① q=김치 200·정답 URL ② page=2 가 1페이지와 안 겹치고 has_next 가 맞다
③ q 없음 400 / 없는 경로 404 / POST 501 ④ 어느 응답에도 트레이스백이 없다
⑤ 색인을 치우면 503 이고 되돌리면 200 이다 (계획 46 · 사양 디자인 5)
⑥ 성공 응답과 503 이 스키마 버전을 갖는다 (계획 46 · 사양 기능 9)
⑦ 빈 `DB_PATH` 로 뜬 서버가 200 이 아니라 503 이다 (계획 47 리뷰)
⑧ `/passages` 가 200·문단마다 위치·400·501·치우면 503 (계획 48 · 사양 기능 7·9)
⑨ 손상된 DB 는 503 이 아니라 500 이다 — 두 경로 다 (계획 48 완료 기준)

서버는 **README 그대로 상대 경로**(`data/crawl.db`)로 띄운다 — 단위와 다른 e2e 는 전부
절대 경로라, DB 를 여는 `file:` URI 조립이 상대 경로에서만 깨지는 갈래를 아무도 안 잰다
(계획 47 · db-open-atomic). 위 ①~⑥ 이 통째로 그 형태 위에서 돈다.

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
        os.mkdir(os.path.join(tmp, "data"))  # README 의 `data/crawl.db` 를 그대로 만든다
        db = os.path.join(tmp, "data", "crawl.db")
        # crawl CLI 는 db 경로 인자가 없어 -c 로 감싼다 (indexer_e2e.py 와 같은 이유)
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], %d, db_path=sys.argv[2])" % (DOCS + 1), site + "/", db)
        origin.shutdown()

        indexed = run("-m", "websearch.indexer", db)
        assert "%d 문서 색인" % (DOCS + 1) in indexed, "색인 stdout: %r" % indexed

        # 사용자가 하는 그대로 — CLI 로 띄우고 stdout 에서 실제 포트를 읽는다.
        # 경로도 사용자가 치는 그대로 **상대 경로**다(cwd 를 옮겨 README 명령과 같게 만든다).
        server = subprocess.Popen([sys.executable, "-m", "websearch.serve",
                                   "data/crawl.db", "--port", "0"],
                                  env=env, cwd=tmp, stdout=subprocess.PIPE, text=True)
        try:
            line = server.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            api = line.split("/search")[0]

            q = urllib.parse.quote("김치")
            status, raw = request("%s/search?q=%s" % (api, q))
            assert status == 200, "q=김치 → %d" % status
            assert "김치" in raw and "\\u" not in raw, "한국어가 이스케이프됐다: %r" % raw[:120]
            first = json.loads(raw)
            assert first["version"] == 1, "스키마 버전이 %r 이다" % first.get("version")
            assert len(first["results"]) == 10, "1페이지 %d건" % len(first["results"])
            assert first["has_next"] is True, "15문서인데 has_next 가 거짓이다"
            assert any(site + "/doc" in r["url"] for r in first["results"]), first["results"]

            second = json.loads(request("%s/search?q=%s&page=2" % (api, q))[1])
            assert second["page"] == 2 and second["has_next"] is False, second
            assert len(second["results"]) == 5, "2페이지 %d건" % len(second["results"])
            overlap = {r["url"] for r in first["results"]} & {r["url"] for r in second["results"]}
            assert not overlap, "페이지가 겹친다: %s" % overlap

            # ⑧ 근거 문단(계획 48). 같은 서버·같은 프로세스 경계에서 계약만 잰다 —
            # 정확도(사양 기능 8)와 p95(성능 5)는 `passage_eval.py` 가 따로 판정한다.
            status, raw = request("%s/passages?q=%s" % (api, q))
            assert status == 200, "/passages?q=김치 → %d" % status
            found = json.loads(raw)
            assert found["version"] == 1, "스키마 버전이 %r 이다" % found.get("version")
            assert found["passages"], "문단이 0건이다: %r" % raw[:200]
            for p in found["passages"]:
                assert isinstance(p["position"], int) and p["position"] >= 0, p
                assert p["title"] and p["url"].startswith(site), p
                assert "김치" in p["text"], "질의어가 없는 문단이 나왔다: %r" % p

            for path, expect, method in [("/search", 400, "GET"),
                                         ("/search?q=%s&page=0" % q, 400, "GET"),
                                         ("/search?q=%s&page=101" % q, 400, "GET"),
                                         ("/passages", 400, "GET"),
                                         ("/passages?q=%s&page=2" % q, 400, "GET"),
                                         (urllib.parse.quote("/없는경로"), 404, "GET"),
                                         ("/search?q=%s" % q, 501, "POST"),
                                         ("/passages?q=%s" % q, 501, "POST")]:
                status, raw = request(api + path, method)
                assert status == expect, "%s %s → %d (기대 %d)" % (method, path, status, expect)
                assert "Traceback" not in raw, "%s 응답에 트레이스백: %r" % (path, raw[:200])

            # 「DB 없음 → 503」. 위 표에 한 줄로 못 올리는 이유는 **파일을 치워야**
            # 나기 때문이다 — 서버는 요청마다 DB 를 새로 여니 프로세스는 그대로다.
            # 단위도 같은 값을 재지만 여기서만 진짜 프로세스가 진짜 파일을 잃는다.
            os.rename(db, db + ".moved")
            status, raw = request("%s/search?q=%s" % (api, q))
            assert status == 503, "색인을 치웠는데 %d 다 (기대 503)" % status
            gone = json.loads(raw)
            assert gone["version"] == 1, "503 이 버전을 안 갖는다: %r" % gone
            assert "Traceback" not in raw and tmp not in raw, \
                "503 본문이 경로나 트레이스백을 흘린다: %r" % raw[:200]
            assert request("%s/passages?q=%s" % (api, q))[0] == 503, \
                "색인을 치웠는데 /passages 가 503 이 아니다"
            # 되돌려 200 을 다시 본다 — 안 보면 503 이 «치웠기 때문» 인지 알 수 없다
            os.rename(db + ".moved", db)
            back = request("%s/search?q=%s" % (api, q))[0]
            assert back == 200, "색인을 되돌렸는데 %d 다 (기대 200)" % back

            # 「손상된 DB → 500」. 503(다시 색인하면 낫는다)과 500(안 낫는다)이 갈리는
            # 자리라 프로세스 밖에서 한 번은 재야 한다 — 여태 어느 e2e 도 500 을 본 적이
            # 없었다(계획 47 result.md 5절 «500 은 한 번도 안 났다»).
            os.rename(db, db + ".ok")
            with open(db, "wb") as fp:
                fp.write(b"not a sqlite database")
            for path in ("/search?q=%s" % q, "/passages?q=%s" % q):
                status, raw = request(api + path)
                assert status == 500, "손상 DB 인데 %s → %d (기대 500)" % (path, status)
                assert json.loads(raw)["version"] == 1, "500 이 버전을 안 갖는다: %r" % raw[:200]
                assert "Traceback" not in raw and tmp not in raw, \
                    "500 본문이 경로나 트레이스백을 흘린다: %r" % raw[:200]
            os.remove(db)
            os.rename(db + ".ok", db)
        finally:
            server.terminate()
            server.wait(timeout=20)

        # 빈 DB 경로로 뜬 서버 — `DB_PATH` 를 안 채운 배포가 이 모양이다. SQLite 는
        # `file:?mode=rw` 를 «없는 파일» 이 아니라 **이름 없는 임시 DB** 로 읽어 조용히
        # 성공하므로, 가드가 없으면 503 이 아니라 **200 + 결과 0건**이 나간다(계획 47 리뷰).
        # 단위는 make_server 를 직접 부르니, 인자가 argv 를 지나오는 것은 여기서만 잰다.
        blank = subprocess.Popen([sys.executable, "-m", "websearch.serve", "", "--port", "0"],
                                 env=env, cwd=tmp, stdout=subprocess.PIPE, text=True)
        try:
            line = blank.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            status, raw = request("%s/search?q=%s" % (line.split("/search")[0], q))
            assert status == 503, "빈 DB 경로인데 %d 다 (기대 503)\n%s" % (status, raw[:200])
        finally:
            blank.terminate()
            blank.wait(timeout=20)

    perf = run(os.path.join(ROOT, "e2e", "perf_search.py"), "500", "30")
    assert "p95" in perf, "측정이 숫자를 안 냈다: %r" % perf

    print("e2e 통과 — %d문서 색인, CLI 로 README 형태의 상대 경로로 띄운 API 가 "
          "1페이지 10건(has_next 참)·2페이지 5건(거짓)·겹침 0, 400/404/501 이 트레이스백 "
          "없이 나온다. 색인을 치우면 503·되돌리면 200 이고 200 과 503 이 version 1 을 "
          "가지며, 빈 DB 경로로 뜬 서버는 200 이 아니라 503 이다. /passages 도 같은 "
          "계약 위에 있고(200·위치·400·501·503), 손상된 DB 는 두 경로 다 500 이다"
          % (DOCS + 1))
    print(perf.strip().splitlines()[-1])


if __name__ == "__main__":
    main()
