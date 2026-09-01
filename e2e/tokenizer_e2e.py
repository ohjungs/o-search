"""tokenizer e2e — plan_tokenizer.md 의 시나리오 6개 그대로.

로컬 서버 페이지를 crawl 로 수집·색인한 뒤 **사용자가 하는 그대로**
`python3 -m websearch.serve <db> --port 0` 로 띄우고 **화면(HTML)** 을 HTTP 로 때린다.
유닛은 `search()` 를 직접 부르므로, crawl→색인→서빙→화면 전체 경로에서 2-gram 이
살아 있는지는 여기서만 본다.

검증: ① 복합어 뒷부분 ② 띄어쓰기 변형 양방향 + 어순 ③ 영어 굴절
      ④ 스니펫이 사람이 읽을 수 있다(bigram 나열·구분자 누출 없음 + 원문 있음)
      ⑤ 한글·영어 섞인 두 어절의 AND 계약 ⑥ 옛 색인은 소리를 내고, 재색인하면 낫는다

실행: PYTHONPATH=src python3 e2e/tokenizer_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 정답 문서에는 질의어가 **낱말로 들어 있지 않다** — 복합어 뒷부분·띄어쓰기 변형·굴절이다
DOCS = {
    "/kimchi": ("김치찌개보관법 냉장 사흘이 한계다", "완전히 식힌 뒤 뚜껑을 덮어 넣는다"),
    "/olle": ("올레 길 7코스 안내", "표지 리본을 따라 걷는다"),
    "/tuple": ("Lists and the tuple type", "A tuple cannot be changed after it is made."),
    "/mixed": ("김치 담그기", "Learning Python for beginners"),
    "/ko-only": ("김치 볶음밥", "배추와 고춧가루를 넣는다"),
}
PAGES = {
    "/": '<html><title>목차</title><body><p>문서 목록</p>'
         + "".join('<a href="%s">%s</a>' % (p, p) for p in DOCS)
         + '</body></html>',
}
PAGES.update({
    path: '<html><title>%s</title><body><p>%s</p></body></html>' % (title, body)
    for path, (title, body) in DOCS.items()
})

OLD_SCHEMA = ("CREATE VIRTUAL TABLE docs "
              "USING fts5(title, body, url UNINDEXED, tokenize='unicode61')")


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


def screen(base, query):
    """화면(HTML)을 질의어로 연다. (상태코드, 본문). 4xx·5xx 도 값으로 돌려준다."""
    url = "%s/?q=%s" % (base, urllib.parse.quote(query))
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def hits(base, query, site):
    """화면에 나온 정답 문서 경로들. 사람이 보는 것과 같은 것만 센다."""
    status, body = screen(base, query)
    assert status == 200, "[%s] 화면이 %d 다" % (query, status)
    assert "Traceback" not in body, "[%s] 화면에 트레이스백이 있다" % query
    return {path for path in DOCS if 'href="%s%s"' % (site, path) in body}


def main():
    origin = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=origin.serve_forever, daemon=True).start()
    site = "http://127.0.0.1:%d" % origin.server_address[1]
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))

    def run(*args, **kw):
        proc = subprocess.run([sys.executable] + list(args), env=env,
                              capture_output=True, text=True, timeout=180)
        if not kw.get("allow_fail"):
            assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        return proc

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], %d, db_path=sys.argv[2])" % (len(DOCS) + 1),
            site + "/", db)
        origin.shutdown()
        indexed = run("-m", "websearch.indexer", db).stdout
        assert "%d 문서 색인" % (len(DOCS) + 1) in indexed, "색인 stdout: %r" % indexed

        server = subprocess.Popen([sys.executable, "-m", "websearch.serve", db,
                                   "--port", "0"], env=env,
                                  stdout=subprocess.PIPE, text=True)
        try:
            line = server.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            base = line.split("/search")[0]

            # ① 복합어 뒷부분 — 문서에 '보관법' 이라는 낱말은 없다
            assert "/kimchi" in hits(base, "보관법", site), "① 복합어 뒷부분이 안 잡힌다"

            # ② 띄어쓰기 변형 양방향 + 어순 (어순은 2026-08-27 리뷰가 잡은 구멍이다)
            for query in ("올레길", "올레 길"):
                assert "/olle" in hits(base, query, site), "② [%s] 가 안 잡힌다" % query
            for query in ("보관법 냉장", "냉장 보관법"):
                assert "/kimchi" in hits(base, query, site), "② [%s] 가 안 잡힌다" % query
            assert "/olle" in hits(base, "7코스 올레길", site), "② 숫자 어절이 분기를 끈다"

            # ③ 영어 굴절 — 문서는 'tuple' 만 쓴다
            assert "/tuple" in hits(base, "tuples", site), "③ 영어 굴절이 안 잡힌다"

            # ④ 스니펫이 사람이 읽을 수 있다. 부정 단언만 두면 빈 화면도 통과한다
            _, body = screen(base, "보관법")
            assert "치찌 찌개" not in body, "④ 화면에 bigram 나열이 나온다"
            assert "\x02" not in body, "④ 스니펫 구분자가 화면으로 샌다"
            assert "완전히 식힌 뒤" in body, "④ 원문 스니펫이 없다(긍정 짝)"

            # ⑤ AND 계약 — 섞인 두 어절은 둘 다 가진 문서만
            assert hits(base, "김치 python", site) == {"/mixed"}, "⑤ AND 계약이 깨졌다"
            assert hits(base, "김치 볶음", site) == {"/ko-only"}, "⑤ 한국어 AND 계약"

            # ⑥ 옛 색인 — 조용히 0건이 아니라 소리를 내고, 재색인하면 낫는다
            drift = sqlite3.connect(db)
            drift.execute("DROP TABLE docs")
            drift.execute(OLD_SCHEMA)
            drift.execute("INSERT INTO docs(title, body, url) VALUES (?, ?, ?)",
                          ("김치찌개보관법 냉장 사흘이 한계다", "완전히 식힌 뒤",
                           site + "/kimchi"))
            drift.commit()
            drift.close()
            status, body = screen(base, "보관법")
            assert status == 500, "⑥ 옛 색인인데 화면이 %d 다 — 조용히 넘어갔다" % status
            assert "Traceback" not in body, "⑥ 오류 화면에 트레이스백이 있다"
            stale = run("-m", "websearch.indexer", db, "--query", "보관법",
                        allow_fail=True)
            assert stale.returncode == 1, "⑥ CLI 가 옛 색인에서 %d 로 끝났다" % stale.returncode
            assert "Traceback" not in stale.stderr, "⑥ CLI 가 트레이스백을 뱉는다"

            rebuilt = run("-m", "websearch.indexer", db).stdout
            assert "%d 문서 색인" % (len(DOCS) + 1) in rebuilt, "⑥ 재색인 stdout: %r" % rebuilt
            assert "색인 제외" not in rebuilt, "⑥ 재구축을 noindex 제외로 오보한다"
            assert "/kimchi" in hits(base, "보관법", site), "⑥ 재색인 후에도 ① 이 안 된다"
            assert "/olle" in hits(base, "올레길", site), "⑥ 재색인 후에도 ② 가 안 된다"
            assert "/tuple" in hits(base, "tuples", site), "⑥ 재색인 후에도 ③ 이 안 된다"
        finally:
            server.terminate()
            server.wait(timeout=20)

    print("e2e 통과 — %d문서를 crawl→색인→CLI 서버로 띄우고 화면(HTML)으로 확인했다: "
          "복합어 뒷부분·띄어쓰기 양방향·어순·영어 굴절이 잡히고, 스니펫에 bigram 이 "
          "새지 않으며, 섞인 두 어절의 AND 가 유지되고, 옛 색인은 500/rc=1 로 소리를 낸 뒤 "
          "재색인으로 낫는다" % (len(DOCS) + 1))


if __name__ == "__main__":
    main()
