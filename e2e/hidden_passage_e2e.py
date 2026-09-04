"""hidden-passage e2e — plan_hidden-passage.md 5절 완료 기준 1·2 를 **사용자 자리**에서.

계획 3절의 탐침은 `indexer.passages()` 를 **프로세스 안에서** 불렀다. 사용자는 그렇게
쓰지 않는다 — crawl 로 남의 HTML 을 받아 색인하고, README 그대로 CLI 서버를 띄워
`GET /passages` 를 HTTP 로 때린다. 그 형태에서 숨은 텍스트가 근거로 나가는지를 잰다.

검증:
① 다섯 모양(`template`·`hidden`·`aria-hidden`·`display:none`·`font-size:0`) 각각에서
   숨은 문장이 근거 문단으로 **0건** 나온다 (착수 시점 5/5 → 0/5)
② 그 다섯 문서의 근거 문단은 **본문 문단 그대로**다 — 조용히 비지 않는다
③ 숨은 블록만 질의어를 담은 문서는 **문단 0건**이다 (완료 기준 2 — 첫 블록으로 안 대신한다)
④ 오탐 대조군(`aria-hidden="false"`·`font-size:0.9em`·`class="hidden-md"`)은 안 물린다
⑤ 색인은 안 바뀐다 — ③ 의 문서가 `/search` 결과에는 **그대로 나온다**(계획 7절)

실행: PYTHONPATH=src python3 e2e/hidden_passage_e2e.py
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

Q = "김치찌개"
HIDDEN = "숨은근거 %s %s %s" % (Q, Q, Q)          # 질의어 3회 — 본문(1회)을 밀도로 이긴다
VISIBLE = "%s는 돼지고기와 두부를 넣고 푹 끓인 찌개다." % Q

# 다섯 모양 = `extract._is_hidden` 의 다섯 가지. 앞이 숨은 블록, 뒤가 본문 문단이다.
SHAPES = {
    "template": '<template><p>%s</p></template>' % HIDDEN,
    "hidden": '<div hidden><p>%s</p></div>' % HIDDEN,
    "aria": '<div aria-hidden="true"><p>%s</p></div>' % HIDDEN,
    "display": '<div style="display:none"><p>%s</p></div>' % HIDDEN,
    "font": '<div style="font-size:0"><p>%s</p></div>' % HIDDEN,
}

# 오탐 대조군 — 이름만 닮았을 뿐 화면에 보인다. **문서를 하나씩 따로 둔다**: 한 문서에
# 몰아 두면 하나가 잘려도 남은 문단이 대신 뽑혀 판정이 안 선다 (실제로 M3 가 살아남았다).
NEGATIVES = {
    "neg-aria": '<p aria-hidden="false">%s 에 라면 사리를 넣어 먹는다.</p>' % Q,
    "neg-font9": '<p style="font-size:0.9em">%s 국물이 아주 진하다.</p>' % Q,
    "neg-class": '<p class="hidden-md">%s 와 곁들일 반찬은 김이다.</p>' % Q,
    "neg-display": '<p style="display:block">%s 에 대파를 마지막에 넣는다.</p>' % Q,
}

PAGES = {
    name: '<html><title>%s</title><body>%s<p>%s</p></body></html>' % (name, markup, VISIBLE)
    for name, markup in SHAPES.items()
}
# ③ 숨은 블록만 질의어를 담았다 — 색인 본문에는 남으므로 `/search` 는 이 문서를 찾는다
PAGES["only"] = ('<html><title>only</title><body><div hidden><p>%s</p></div>'
                 '<p>오늘 저녁은 무엇을 먹을지 아직 고민이다.</p></body></html>' % HIDDEN)
PAGES.update({
    name: '<html><title>%s</title><body>%s</body></html>' % (name, markup)
    for name, markup in NEGATIVES.items()
})

# `serve.PASSAGE_LIMIT` 이 10 이라 질의어를 담은 문서가 11개가 되면 하나가 창 밖으로
# 밀려 «잘렸다» 와 구별이 안 된다 (한 번 밟았다). 여기서 세어 두고 넘으면 즉시 죽는다.
assert len(SHAPES) + 1 + len(NEGATIVES) <= 10, "질의어를 담은 문서가 PASSAGE_LIMIT 을 넘는다"

INDEX = ('<html><title>목차</title><body>'
         + "".join('<a href="/%s">%s</a>' % (n, n) for n in PAGES)
         + '</body></html>')


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            body, ctype = b"User-agent: *\n", "text/plain"
        elif self.path == "/":
            body, ctype = INDEX.encode(), "text/html"
        elif self.path.lstrip("/") in PAGES:
            body, ctype = PAGES[self.path.lstrip("/")].encode(), "text/html"
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


def get(url):
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode())


def main():
    origin = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=origin.serve_forever, daemon=True).start()
    site = "http://127.0.0.1:%d" % origin.server_address[1]
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    total = len(PAGES) + 1  # 목차까지

    def run(*args, **kw):
        proc = subprocess.run([sys.executable] + list(args), env=env,
                              capture_output=True, text=True, timeout=180, **kw)
        assert proc.returncode == 0, "exit %d\n%s" % (proc.returncode, proc.stderr)
        return proc.stdout

    with tempfile.TemporaryDirectory() as tmp:
        os.mkdir(os.path.join(tmp, "data"))
        db = os.path.join(tmp, "data", "crawl.db")
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], %d, db_path=sys.argv[2])" % total, site + "/", db)
        origin.shutdown()
        indexed = run("-m", "websearch.indexer", db)
        assert "%d 문서 색인" % total in indexed, "색인 stdout: %r" % indexed

        server = subprocess.Popen([sys.executable, "-m", "websearch.serve",
                                   "data/crawl.db", "--port", "0"],
                                  env=env, cwd=tmp, stdout=subprocess.PIPE, text=True)
        try:
            line = server.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            api = line.split("/search")[0]
            q = urllib.parse.quote(Q)

            found = get("%s/passages?q=%s" % (api, q))
            assert found["version"] == 1, found
            by_url = {p["url"]: p for p in found["passages"]}

            # ① 숨은 텍스트가 근거로 나간 건수 — 0 이어야 한다
            leaked = [p for p in found["passages"] if "숨은근거" in p["text"]]
            assert not leaked, "숨은 텍스트가 근거로 나간 문서 %d개: %r" % (len(leaked), leaked)

            # ② 다섯 모양 전부 본문 문단이 그대로 나온다
            for name in SHAPES:
                got = by_url.get("%s/%s" % (site, name))
                assert got is not None, "%s 의 문단이 통째로 사라졌다" % name
                assert got["text"] == VISIBLE, "%s → %r (기대 %r)" % (name, got["text"], VISIBLE)

            # ③ 숨은 블록만 질의어를 담은 문서 — 문단 0건, 첫 블록으로 안 대신한다
            assert "%s/only" % site not in by_url, \
                "숨김만 매치한 문서가 문단을 냈다: %r" % by_url["%s/only" % site]

            # ④ 오탐 대조군은 안 물린다 — 문서마다 문단이 하나뿐이라 잘리면 0건이 된다
            for name in NEGATIVES:
                neg = by_url.get("%s/%s" % (site, name))
                assert neg is not None and Q in neg["text"], \
                    "오탐 — %s 의 보이는 문단이 잘렸다: %r" % (name, neg)
            expect = len(SHAPES) + len(NEGATIVES)
            assert len(found["passages"]) == expect, \
                "문단 %d건 (기대 %d)" % (len(found["passages"]), expect)

            # ⑤ 색인은 안 바뀐다 — ③ 의 문서가 검색에는 그대로 나온다 (계획 7절)
            hits = get("%s/search?q=%s" % (api, q))
            urls = {r["url"] for r in hits["results"]}
            assert "%s/only" % site in urls, \
                "숨김만 매치한 문서가 검색에서도 사라졌다 — 색인 경로가 움직였다"
            assert len(urls) == len(PAGES), "검색 %d건 (기대 %d)" % (len(urls), len(PAGES))
        finally:
            server.terminate()
            server.wait(timeout=20)

    print("e2e 통과 — %d문서 crawl→색인→CLI 서버(README 형태 상대 경로)로 띄워 HTTP 로 잰다: "
          "다섯 모양의 숨은 텍스트가 근거 문단으로 **0/%d** 나가고(착수 5/5), 같은 문서의 "
          "본문 문단은 %d/%d 그대로다. 숨김만 매치한 문서는 문단 0건이고 첫 블록으로 "
          "대신하지 않는다. 오탐 대조군 %d종은 안 물린다. 그 문서는 /search 에는 %d건 중 "
          "하나로 그대로 나온다 — 색인은 안 움직였다"
          % (total, len(SHAPES), len(SHAPES), len(SHAPES), len(NEGATIVES), len(PAGES)))


if __name__ == "__main__":
    main()
