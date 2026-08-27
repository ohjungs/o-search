"""pagination-ui e2e — plan_pagination-ui.md 의 시나리오 그대로.

**링크가 있느냐가 아니라 따라간 결과를 잰다.** 계획이 연 문제는 "주소창을 편집할 줄
아는 사람만 11번째 결과를 본다" 였다. 그러니 검증도 주소창을 안 건드리고 **화면에
그려진 링크만 따라가서** 11번째 문서에 닿는지 봐야 한다.

로컬 서버 페이지를 crawl 로 수집·색인하고, 사용자가 하는 그대로
`python3 -m websearch.serve <db> --port 0` 로 띄워 HTTP 로 때린다(바깥 네트워크 없음).

  1 1페이지의 `다음` 을 따라가면 **1페이지에 없던 문서**가 보인다
  2 부정 짝 — 마지막 페이지에 `다음` 없음 · 1페이지에 `이전` 없음
  3 회귀 — `design_check.py` 종료 0 (JS 0B · 대비 4.5:1 · 360px)
  4 잴 대상이 사라지면(문서가 11개 미만) **종료 코드 2**

실행: PYTHONPATH=src python3 e2e/pagination_ui_e2e.py
     PYTHONPATH=src python3 e2e/pagination_ui_e2e.py --control  # 측정 불능 = 종료 2
"""
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = 11        # 2페이지에 딱 1건 남는다 — `len(hits) > PAGE_SIZE` 가 틀리면 빈 화면
CONTROL = 10     # 대조군: 1페이지로 끝나 **잴 이동 링크가 없다**

# 시드에는 `김치` 를 넣지 않는다 — 넣으면 히트가 12건이 돼 "2페이지에 1건" 이라는
# 재려는 경계가 사라진다
SEED = ('<html><title>목차</title><body><p>문서 목록</p>'
        + "".join('<a href="/doc%02d">%d</a>' % (i, i) for i in range(DOCS))
        + '</body></html>')
DOC = ('<html><title>김치 %02d</title><body>'
       '<p>%s 배추를 절여 담근다.</p></body></html>')


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            body, ctype = b"User-agent: *\n", "text/plain"
        elif self.path == "/":
            body, ctype = SEED.encode(), "text/html"
        elif re.fullmatch(r"/doc\d\d", self.path):
            i = int(self.path[4:])
            body, ctype = (DOC % (i, "김치 " * (i + 1))).encode(), "text/html"
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


def measured(samples, what, least=1):
    """잴 대상이 없으면 **조용히 통과하지 않고** 종료 코드 2로 죽는다.

    이동을 재는 e2e 의 가장 위험한 실패는 "링크가 사라졌는데 부정 단언들이 전부
    참이 되는" 것이다 — `다음이 없다`·`겹치지 않는다` 는 공집합 위에서 참이다.
    실패(1)와 구분되는 코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 이(가) %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def get(url):
    with urllib.request.urlopen(url, timeout=20) as resp:
        assert resp.status == 200, "%s → %d" % (url, resp.status)
        return resp.read().decode()


def pager(body):
    """화면에 **그려진** 이동 링크만 `{rel: href}` 로. 속성 순서에 안 기댄다."""
    block = re.search(r"<nav[^>]*class=\"pager\"[^>]*>(.*?)</nav>", body, re.S)
    if not block:
        return {}
    found = {}
    for tag in re.findall(r"<a\b[^>]*>", block.group(1)):
        rel = re.search(r'rel="([^"]*)"', tag)
        href = re.search(r'href="([^"]*)"', tag)
        assert rel and href, "이동 링크에 rel 또는 href 가 없다: %s" % tag
        found[rel.group(1)] = href.group(1).replace("&amp;", "&")
    return found


def hits(body):
    """결과 목록의 URL 들. 사용자가 실제로 누를 수 있는 것만 센다."""
    items = re.findall(r'<li class="hit">(.*?)</li>', body, re.S)
    return [re.search(r'href="([^"]*)"', it).group(1) for it in items]


def scenario(base, docs):
    """1페이지에서 **링크를 따라가** 11번째 문서에 닿는가."""
    q = urllib.parse.quote("김치")
    # 먼저 **갈 곳이 있는지**를 화면이 아닌 API 로 확인한다. 이 둘을 안 가르면
    # 기능을 통째로 지운 것과 문서가 모자란 것이 같은 종료 코드로 나온다 —
    # 여기서 걸리면 2(못 쟀다), 갈 곳이 있는데 링크가 없으면 아래에서 1(빨강)이다
    measured(json.loads(get("%s/search?q=%s&page=2" % (base, q)))["results"],
             "2페이지에 남은 문서")

    first = get(base + "/?q=" + q)
    page1 = hits(first)
    assert len(page1) == 10, "1페이지가 %d건이다 — 탐침 행이 샜거나 색인이 모자라다" % len(page1)

    nav = pager(first)
    assert "prev" not in nav, "1페이지에 이전 링크가 있다: %s" % nav
    assert "next" in nav, "갈 곳이 있는데 화면에 다음 링크가 없다 — 주소창을 아는 사람만 본다"
    nxt = nav["next"]

    # **주소창을 안 건드린다** — 화면이 준 href 를 그대로 따라간다
    second = get(base + nxt)
    page2 = hits(second)
    fresh = set(page2) - set(page1)
    assert len(fresh) == 1, ("다음을 따라갔는데 새 문서가 %d개다 (기대 1). "
                             "page2=%s" % (len(fresh), page2))
    assert len(set(page1) | set(page2)) == docs, \
        "%d문서인데 두 페이지 합집합이 %d개다" % (docs, len(set(page1) | set(page2)))

    back = pager(second)
    assert "next" not in back, "마지막 페이지가 다음을 내줬다 — 따라가면 빈 화면이다"
    assert "prev" in back, "2페이지에 이전이 없다 — 막다른 길이다"
    assert get(base + back["prev"]) == first, "이전을 따라갔는데 1페이지가 아니다"
    return sorted(fresh)[0]


def main(argv):
    docs = CONTROL if "--control" in argv else DOCS
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
        # crawl CLI 는 db 경로 인자가 없어 -c 로 감싼다 (search_api_e2e.py 와 같은 이유)
        run("-c", "import sys; from websearch.crawl import crawl; "
                  "crawl([sys.argv[1]], %d, db_path=sys.argv[2])" % (docs + 1), site + "/", db)
        origin.shutdown()
        indexed = run("-m", "websearch.indexer", db)
        assert "%d 문서 색인" % (docs + 1) in indexed, "색인 stdout: %r" % indexed

        # 사용자가 하는 그대로 — CLI 로 띄우고 stdout 에서 실제 포트를 읽는다
        server = subprocess.Popen([sys.executable, "-m", "websearch.serve", db, "--port", "0"],
                                  env=env, stdout=subprocess.PIPE, text=True)
        try:
            line = server.stdout.readline().strip()
            assert line.startswith("http://127.0.0.1:"), "포트를 못 읽었다: %r" % line
            base = line.split("/search")[0]
            fresh = scenario(base, docs)
        finally:
            server.terminate()
            server.wait(timeout=20)

    if "--control" in argv:
        print("대조군이 그냥 통과했다 — 측정 불능 가드가 죽어 있다", file=sys.stderr)
        return 1

    design = run(os.path.join(ROOT, "e2e", "design_check.py"))
    print("e2e 통과 — %d문서 · 다음을 따라가 1페이지에 없던 %s 에 닿는다 · "
          "마지막에 다음 없음 · 1페이지에 이전 없음" % (docs, fresh.rsplit("/", 1)[-1]))
    print(design.strip().splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
