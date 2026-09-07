"""noindex-respect e2e — plan_noindex-respect.md 의 시나리오 + 계획 69 의 엔티티 갈래.

로컬 서버에 일반 페이지 / `<meta name="robots" content="noindex">` / `content="none"` /
**`name` 을 엔티티로 인코딩한 `<meta name="&#114;obots" content="noindex">`** /
`content="index, follow"` 를 띄우고(본문은 다 같은 낱말 pyeongsan), crawl 로 수집한 뒤
사용자가 하는 그대로 `python3 -m websearch.indexer` 로 색인하고,
`python3 -m websearch.serve` 로 띄운 **화면(HTTP)** 과 CLI 질의 양쪽에서 확인한다.
검증: ① noindex·none·엔티티 인코딩 페이지는 색인되지 않음 ② 화면과 질의에 허용 문서만
③ 이미 색인된 문서가 뒤늦게 **엔티티 인코딩** noindex 를 달면 색인에서 빠짐(제거 경로가
엔티티 갈래까지 보는지) ④ 평범한 noindex 도 그대로 빠지고 출력으로 알림
⑤ 오탐 0 — `robots` 없이 `&#8212;` 만 든 문서와 `index, follow` 문서는 계속 색인된다

실행: PYTHONPATH=src python3 e2e/noindex_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from websearch.store import Store  # noqa: E402 — 위 경로 삽입 뒤라야 임포트된다

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOINDEX_HTML = ('<html><head><title>거부</title>'
                '<meta name="robots" content="noindex"></head>'
                '<body><p>pyeongsan 색인 거부 문서</p></body></html>')

# 계획 69 가 닫은 자리 — HTML 파서는 name 을 'robots' 로 풀지만, 원문에는 'robots' 라는
# 글자가 없다. 사전 필터의 `&#` 갈래가 없으면 이 선언은 통째로 무시된다.
ENTITY_NOINDEX_HTML = ('<html><head><title>거부3</title>'
                       '<meta name="&#114;obots" content="noindex"></head>'
                       '<body><p>pyeongsan 은 엔티티로 인코딩한 거부다.</p></body></html>')

PAGES = {
    "/": '<html><title>목차</title><body><p>문서 목록</p>'
         '<a href="/open">1</a><a href="/noindex">2</a><a href="/none">3</a>'
         '<a href="/entity">4</a><a href="/follow">5</a></body></html>',
    # robots 는 없고 `&#` 만 있다 — 넓힌 필터가 오탐을 내는지 보는 대조군이다
    "/open": '<html><title>공개 문서</title><body>'
             '<p>pyeongsan 은 색인해도 되는 문서다 &#8212; 대시도 있다.</p></body></html>',
    "/noindex": NOINDEX_HTML,
    "/none": '<html><head><title>거부2</title>'
             '<meta name="robots" content="none"></head>'
             '<body><p>pyeongsan 도 색인 거부다.</p></body></html>',
    "/entity": ENTITY_NOINDEX_HTML,
    "/follow": '<html><head><title>허용</title>'
               '<meta name="robots" content="index, follow"></head>'
               '<body><p>pyeongsan 을 명시적으로 허용한 문서다.</p></body></html>',
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
                  "crawl([sys.argv[1]], 6, db_path=sys.argv[2])", base + "/", db)
        server.shutdown()

        pages = sqlite3.connect(db).execute("SELECT count(*) FROM pages").fetchone()[0]
        assert pages == 6, "6페이지를 수집해야 한다 — 수집 %d" % pages

        first = run("-m", "websearch.indexer", db)
        # 목차·/open·/follow 만 색인된다. /noindex·/none·/entity 는 수집돼 있어도 대상이 아니다
        assert "3 문서 색인" in first, "1회차 stdout: %r" % first

        # ② 사용자가 실제로 보는 화면(HTTP)에서 확인한다
        serve = subprocess.Popen([sys.executable, "-m", "websearch.serve", db,
                                  "--port", "0"], env=env,
                                 stdout=subprocess.PIPE, text=True)
        try:
            line = serve.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            api = line.split("/search")[0]
            with urllib.request.urlopen("%s/?q=pyeongsan" % api, timeout=20) as resp:
                assert resp.status == 200, "화면이 %d 다" % resp.status
                screen = resp.read().decode()
        finally:
            serve.terminate()
            serve.wait(timeout=20)

        assert "Traceback" not in screen, "화면에 트레이스백이 있다"
        assert 'href="%s/open"' % base in screen, "일반 문서가 화면에 없다"
        assert 'href="%s/follow"' % base in screen, "index,follow 문서가 화면에 없다"
        for path in ("/noindex", "/none", "/entity"):
            assert 'href="%s%s"' % (base, path) not in screen, "%s 가 화면에 나왔다" % path

        hits = run("-m", "websearch.indexer", db, "--query", "pyeongsan")
        assert base + "/open" in hits, "일반 문서가 안 나왔다: %r" % hits
        assert base + "/follow" in hits, "index,follow 문서가 안 나왔다: %r" % hits
        assert "/noindex" not in hits, "noindex 문서가 검색됐다: %r" % hits
        assert "/none" not in hits, "none 문서가 검색됐다: %r" % hits
        assert "/entity" not in hits, "엔티티 인코딩 noindex 문서가 검색됐다: %r" % hits

        # 이미 색인된 문서가 뒤늦게 noindex 를 달았다. CLI 재크롤은 기수집 URL 을
        # 건너뛰므로(digest [5], 별도 사안) pages 를 직접 갱신해 상황만 만든다.
        #
        # **`Store.upsert` 로 갱신하는 이유**는 raw SQL 이 «옛 저장 표현»을 쓰기 때문이다.
        # 계획 77 이 `pages.html` 을 압축한 뒤로, 직접 UPDATE 하면 이 시나리오만 압축 안 된
        # TEXT 를 검사하게 되어 **제품이 실제로 쓰는 경로를 안 지난다.** 계획 77 이 잡은 결함
        # (표현에 기대는 SQL 이 조용히 죽는 것)을 잡아낸 것이 바로 «픽스처가 제품 경로를
        # 지났다» 는 성질이라, 여기서 그 성질을 버리면 같은 부류를 다음에는 못 잡는다.
        def retract(path, html):
            Store(db).upsert(base + path, html, 200)

        # ③ 엔티티 갈래 — 제거 질의의 `OR p.html LIKE '%&#%'` 가 사는 자리다.
        #    진입(is_noindex)만 고쳤으면 이미 색인된 이 문서는 그대로 남는다.
        retract("/follow", ENTITY_NOINDEX_HTML)
        pulled = run("-m", "websearch.indexer", db)
        assert "0 문서 색인" in pulled, "3회차 stdout: %r" % pulled
        assert "1 문서 색인 제외" in pulled, "엔티티 거부를 제거하지 않았다: %r" % pulled

        left = run("-m", "websearch.indexer", db, "--query", "pyeongsan")
        assert "/follow" not in left, "엔티티 거부가 색인에 남았다: %r" % left
        assert base + "/open" in left, "무관한 문서까지 빠졌다: %r" % left

        # ④ 평범한 noindex 도 그대로 빠진다 (계획 69 가 회귀시키지 않았다)
        retract("/open", NOINDEX_HTML)
        second = run("-m", "websearch.indexer", db)
        assert "0 문서 색인" in second, "4회차 stdout: %r" % second
        assert "1 문서 색인 제외" in second, "제거를 알리지 않았다: %r" % second

        gone = run("-m", "websearch.indexer", db, "--query", "pyeongsan")
        assert base not in gone, "색인에서 빠졌어야 하는데 검색됐다: %r" % gone
        assert gone.strip(), "무결과인데 아무것도 출력하지 않았다"

    print("e2e 통과 — 수집 6페이지 중 3문서 색인(noindex·none·엔티티 인코딩 제외), "
          "화면(HTTP)과 질의 둘 다 허용 문서만, 뒤늦은 엔티티 거부·평범한 거부 모두 "
          "색인에서 제거되고 출력으로 알림")


if __name__ == "__main__":
    main()
