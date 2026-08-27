"""url-normalize e2e — plan_url-normalize.md 5절의 시나리오 그대로.

계획이 연 문제는 **같은 문서인데 표기가 다르면 다른 문서 취급**이라는 것이었다.
017(`domain-key`)이 "어느 서버인가" 를 한 칸으로 모은 뒤에도 `Frontier._seen` 과
`store.pages.url` 은 문자열 그대로를 열쇠로 써서, `http://a.test/p` ·
`http://A.test/p` · `http://a.test:80/p` 를 **세 번 받고 세 번 저장하고 세 번**
색인했다. 간격은 지켜지므로 윤리 위반은 아니지만 크롤 예산이 표기 수만큼 샌다.

여기서는 그것을 실물로 잰다 — 진짜 소켓·진짜 HTTP·진짜 robots·진짜 SQLite.
그리고 **크롤러 내부 상태가 아니라 서버가 받은 것**으로 잰다
(`domain_key_e2e.py`·`crawl_politeness_e2e.py` 와 같은 자세). 같은 문서를
가리키는 표기는 **한 실서버**에 걸고, 대조군만 **다른 실서버**로 보낸다 —
정규화가 안 되면 갈린 표기가 진짜로 나가야 "2회 받았다" 가 관찰된다.

  1 `/p` 를 세 표기로 건다(대소문자 · 기본 포트) → 그 서버의 `/p` 수신 **1회**
  2 빈 경로: `http://a.test` 와 `http://a.test/` → `/` 수신 **1회**(시드뿐)
  3 퍼센트 표기: `/%ea%b0%80` 와 `/%EA%B0%80` → 수신 **1회**, 받은 경로는 대문자
  4 대조군 — **기본이 아닌 포트**(`http://a.test:8080/p`)는 다른 서버다.
    자기 `/p` 를 따로 **1회** 받는다. 여기가 죽으면 정규화가 과한 것이다
  5 `pages` 는 **4행**(`/` · `/p` · `/%EA%B0%80` · 대조군 `/p`)
  6 잴 대상이 사라지면(수신 표본 부족) **종료 코드 2**

바깥 네트워크는 안 탄다 — 이름 해석 대신 `PORTS` 가 로컬 임시 포트로 보낸다.
**갈린 표기도 전부 PORTS 에 등록한다**: 등록을 빼면 정규화를 지운 변이가
"연결 실패" 로 죽어서, 재려던 "두 번 받았다" 를 관찰할 수 없다.
간격 1초가 실제로 걸려 시간이 걸리는 것이 정상이다. 약 4초.

실행: PYTHONPATH=src python3 e2e/url_normalize_e2e.py
     PYTHONPATH=src python3 e2e/url_normalize_e2e.py --control  # 측정 불능 = 종료 2
"""
import http.client
import http.server
import os
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import crawl  # noqa: E402

HOST = "a.test"
# 같은 서버를 가리키는 표기 전부. 정규화가 살아 있으면 첫 것만 실제로 나간다
SAME = [HOST, "A.test", HOST + ":80"]
# 대조군 — 기본이 아닌 포트라 **다른 서버**다. 진짜 다른 소켓에 물린다
OTHER = HOST + ":8080"

KOREAN = "/%EA%B0%80"  # 정규화된 표기. 링크에는 소문자 hex 로도 건다

PORTS = {}   # netloc -> 로컬 포트
LOG = {}     # 서버 역할 -> [(시각, Host 헤더, 경로)]


class Handler(http.server.BaseHTTPRequestHandler):
    """`/` 가 링크를 내고 나머지는 잎이다. 도착을 역할별로 적는다."""

    control = False  # True 면 시드가 링크를 안 낸다 — 잴 수신이 사라진다

    def do_GET(self):
        role = self.server.role
        LOG.setdefault(role, []).append(
            (time.monotonic(), self.headers.get("Host", ""), self.path))
        if self.path == "/robots.txt":
            self._send(b"User-agent: *\nDisallow: /nope\n", "text/plain")
        elif self.path == "/":
            anchors = "" if Handler.control else "".join(
                '<a href="%s">%d</a>' % (href, i)
                for i, href in enumerate(self.server.links))
            self._send(("<html><title>%s</title><body>%s</body></html>"
                        % (role, anchors)).encode(), "text/html")
        else:
            self._send(b"<html><body>leaf</body></html>", "text/html")

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve(role, links):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.role, server.links = role, links
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _routed(host, **kw):
    """이름을 풀지 않고 `PORTS` 가 가리키는 로컬 포트로 보낸다 — 바깥으로 안 나간다."""
    return http.client.HTTPConnection("127.0.0.1", PORTS[host], **kw)


class _LocalHTTP(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_routed, req)


def measured(samples, what, least):
    """표본이 모자라면 **조용히 통과하지 않고** 종료 코드 2로 죽는다.

    수신 횟수를 재는 e2e 의 가장 위험한 실패는 "링크를 한 번도 안 따라갔는데
    `== 1` 이 참이 되는" 것이다(시드 하나만 받아도 1이다). 실패(1)와 구분되는
    코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 표본이 %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def hits(role, path):
    return [row for row in LOG.get(role, []) if row[2] == path]


def pages(role):
    """robots.txt 를 뺀 도착 기록."""
    return [row for row in LOG.get(role, []) if row[2] != "/robots.txt"]


def run(db_path):
    # 시나리오 1~3 의 표기를 전부 링크로 건다. 셋 다 **같은 서버**를 가리킨다
    same = serve("same", [
        "http://%s/p" % HOST, "http://A.test/p", "http://%s:80/p" % HOST,   # 1
        "http://%s" % HOST, "http://%s/" % HOST,                            # 2
        "/%ea%b0%80", KOREAN,                                               # 3
        "http://%s/p" % OTHER,                                              # 4 대조군
    ])
    other = serve("other", [])
    PORTS.update(dict.fromkeys(SAME, same.server_address[1]))
    PORTS[OTHER] = other.server_address[1]
    urllib.request.install_opener(urllib.request.build_opener(_LocalHTTP))
    try:
        crawl.crawl(["http://%s/" % HOST], 99, db_path=db_path)
    finally:
        urllib.request.install_opener(urllib.request.build_opener())
        for server in (same, other):
            server.shutdown()


def check(db_path):
    # 링크를 하나도 안 따라갔으면 아래 `== 1` 이 전부 공짜로 참이다
    measured(pages("same"), "같은 서버 페이지 도착", least=3)

    # 1 — 표기 셋이 한 문서다
    got = hits("same", "/p")
    assert len(got) == 1, ("`/p` 를 %d회 받았다(표기 %s) — 1회여야 한다"
                           % (len(got), [h for _, h, _ in got]))

    # 2 — 빈 경로와 `/` 는 한 문서다. 시드가 받은 1회뿐이어야 한다
    root = hits("same", "/")
    assert len(root) == 1, ("`/` 를 %d회 받았다 — 시드 1회여야 한다(빈 경로 링크가 "
                            "따로 나갔다)" % len(root))

    # 3 — 퍼센트 표기. 대문자 쪽으로 모인다
    kor = hits("same", KOREAN)
    lower = hits("same", "/%ea%b0%80")
    assert len(kor) == 1 and not lower, (
        "퍼센트 표기가 안 모였다 — 대문자 %d회 · 소문자 %d회" % (len(kor), len(lower)))

    # 4 — 대조군. **다른 실서버**가 자기 `/p` 를 따로 받는다. 정규화가 과하면 0이다
    ctrl = hits("other", "/p")
    assert len(ctrl) == 1, ("대조군(%s)이 `/p` 를 %d회 받았다 — 1회여야 한다. "
                            "0이면 기본이 아닌 포트까지 접은 것이다" % (OTHER, len(ctrl)))

    # 5 — 저장도 문서 수만큼이다. 수신이 1회여도 열쇠가 갈리면 여기서 갈린다
    with sqlite3.connect(db_path) as db:
        urls = sorted(row[0] for row in db.execute("SELECT url FROM pages"))
    want = sorted(["http://%s/" % HOST, "http://%s/p" % HOST,
                   "http://%s%s" % (HOST, KOREAN), "http://%s/p" % OTHER])
    assert urls == want, "pages 행이 다르다\n  받은 것: %s\n  기대: %s" % (urls, want)
    return urls


def main(argv):
    if "--control" in argv:
        # 시드가 링크를 안 낸다 → 도착이 1건뿐 → 잴 수신이 없다 → 종료 2
        Handler.control = True
        print("[대조] 시드가 링크를 안 낸다 — 측정 불능(2)이 나와야 한다")
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "crawl.db")
        run(db_path)
        urls = check(db_path)
    print("OK %.1fs — 표기 %d개가 문서 %d개로 접혔다: %s"
          % (time.monotonic() - started,
             len(SAME) + 4, len(urls), urls))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
