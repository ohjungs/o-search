"""indexer e2e — plan_indexer.md 의 시나리오 그대로.

로컬 서버(한국어·영어 본문 3페이지)를 crawl 로 수집한 뒤, 사용자가 하는 그대로
`python3 -m websearch.indexer <db>` 로 색인하고 `--query` 로 질의한다.
검증: ① 3문서 색인 ② 한국어 2글자 질의·영어 질의가 각각 정답 URL 을 돌려줌
③ 재실행 시 "0 문서 색인" (증분) ④ 무결과 질의가 침묵하지 않음
⑤ README 그대로의 **상대 경로**(`data/crawl.db`)로도 질의가 되고, 없는 상대 경로는
   rc 1 + 안내이며 **빈 DB 파일을 만들지 않는다** (계획 47 · db-open-atomic)

실행: PYTHONPATH=src python3 e2e/indexer_e2e.py
"""
import http.server
import os
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "/": '<html><title>목차</title><body><p>문서 목록</p>'
         '<a href="/kimchi">1</a><a href="/python">2</a></body></html>',
    "/kimchi": '<html><title>김치 담그기</title><body>'
               '<p>어제 <b>김치</b>를 담갔다. 배추와 고춧가루가 필요하다.</p></body></html>',
    "/python": '<html><title>Python Tutorial</title><body>'
               '<p>Learning Python for beginners.</p></body></html>',
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

    def run(*args, cwd=None):
        proc = subprocess.run([sys.executable] + list(args), env=env, cwd=cwd,
                              capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        return proc.stdout

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        # crawl CLI 는 db 경로 인자가 없어 -c 로 감싼다 (crawl_e2e.py 와 같은 이유)
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], 3, db_path=sys.argv[2])", base + "/", db)
        server.shutdown()

        first = run("-m", "websearch.indexer", db)
        assert "3 문서 색인" in first, "1회차 stdout: %r" % first

        kr = run("-m", "websearch.indexer", db, "--query", "김치")
        assert base + "/kimchi" in kr, "한국어 질의 실패: %r" % kr

        en = run("-m", "websearch.indexer", db, "--query", "python")
        assert base + "/python" in en, "영어 질의 실패: %r" % en

        miss = run("-m", "websearch.indexer", db, "--query", "우주선")
        assert miss.strip(), "무결과인데 아무것도 출력하지 않았다"
        assert base not in miss, "무결과인데 URL 이 나왔다: %r" % miss

        second = run("-m", "websearch.indexer", db)
        assert "0 문서 색인" in second, "증분 실패 — 2회차 stdout: %r" % second

        # 여기까지는 전부 절대 경로다. **README 의 세 명령은 상대 경로**(`data/crawl.db`)라
        # DB 를 여는 `file:` URI 조립이 깨져도(`file://` + 경로면 `data` 가 authority 로
        # 읽혀 열기 자체가 죽는다) 위 단언은 하나도 안 운다 — 아래가 그 자리를 잰다.
        os.mkdir(os.path.join(tmp, "data"))
        os.rename(db, os.path.join(tmp, "data", "crawl.db"))
        rel = run("-m", "websearch.indexer", "data/crawl.db", "--query", "김치", cwd=tmp)
        assert base + "/kimchi" in rel, "상대 경로 질의 실패: %r" % rel

        # 없는 상대 경로 — rc 1 · 안내 · **빈 DB 를 만들지 않는다**(계획 47 의 주제).
        # 만들면 그 뒤로 파일이 있으니 "DB 없음"(서버로는 503)이 영영 안 난다.
        gone = subprocess.run([sys.executable, "-m", "websearch.indexer", "data/none.db"],
                              env=env, cwd=tmp, capture_output=True, text=True, timeout=120)
        assert gone.returncode == 1, "없는 DB 인데 rc %d 다 (기대 1)\n%s" % (gone.returncode,
                                                                            gone.stderr)
        assert "DB 파일이 없다" in gone.stderr, "안내가 없다: %r" % gone.stderr
        assert not os.path.exists(os.path.join(tmp, "data", "none.db")), \
            "없는 DB 를 열다가 빈 파일을 만들었다"

    print("e2e 통과 — 3문서 색인, 한/영 질의 정답 매치, 재실행 0문서(증분), 무결과 안내 출력, "
          "README 형태의 상대 경로 질의 성공 · 없는 상대 경로는 rc 1 이고 파일을 안 만든다")


if __name__ == "__main__":
    main()
