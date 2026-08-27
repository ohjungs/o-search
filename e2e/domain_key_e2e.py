"""domain-key e2e — plan_domain-key.md 5절의 시나리오 그대로.

계획이 연 문제는 **한 서버인데 표기가 다르면 다른 서버 취급**이라는 것이었다.
열쇠가 날 `netloc` 이라 `http://a.test` · `http://A.test` · `http://a.test:80` 이
큐도 `_last_fetch` 도 `_delays` 도 따로 갖는다 — 선언한 `Crawl-delay` 가 통째로
빠져나가고 `robots.txt` 도 표기 수만큼 받는다(실측 간격 0.002초 · robots 2회).

여기서는 그것을 실물로 잰다 — 진짜 소켓·진짜 HTTP·진짜 robots·진짜 프런티어.
그리고 **크롤러 내부 상태가 아니라 서버가 받은 시각**을 잰다
(`crawl_politeness_e2e.py`·`retry_interval_e2e.py` 와 같은 자세).

  1 `Crawl-delay: 2` 서버에 **대소문자가 다른 호스트**로 링크가 걸린다
    → 서버 수신 간격 ≥ 2초 · 그 서버의 `robots.txt` 는 **1회**
  2 **기본 포트를 붙인 링크**(`http://a.test:80/`)도 같은 칸 — 같은 자로 잰다
  3 대조군: **기본이 아닌 포트**(`http://a.test:443/`, 스킴은 http)는 여전히 다른
    도메인 — 남의 2초에 안 묶이고 자기 하한 1초로 돈다
  4 잴 대상이 사라지면(요청 표본 부족) **종료 코드 2**

바깥 네트워크는 안 탄다 — 이름 해석 대신 `PORTS` 가 로컬 임시 포트로 보낸다.
표기 세 개는 **같은 서버**로, 대조군만 **다른 서버**로 간다. 시간이 걸리는 것이
정상이다(간격을 실제로 잰다). 약 7초.

실행: PYTHONPATH=src python3 e2e/domain_key_e2e.py
     PYTHONPATH=src python3 e2e/domain_key_e2e.py --control  # 측정 불능 = 종료 2
"""
import http.client
import http.server
import os
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import crawl  # noqa: E402

DECLARED = 2.0   # 같은 서버가 선언한 Crawl-delay
FLOOR = 1.0      # frontier.DOMAIN_INTERVAL — 대조군이 쓰는 하한
JITTER = 0.05    # 왕복 지터가 서버 수신 시각에 실린다 — crawl_e2e.py 와 같은 값

HOST = "a.test"
# 같은 서버를 가리키는 세 표기. 대소문자 + 기본 포트.
SAME = [HOST, "A.test", HOST + ":80"]
# 대조군 — **기본이 아닌 포트**다. http 스킴에서 443 은 기본이 아니다.
OTHER = HOST + ":443"

PORTS = {}   # netloc -> 로컬 포트
LOG = {}     # 서버 역할 -> [(시각, Host 헤더, 경로)]


class Handler(http.server.BaseHTTPRequestHandler):
    """`/` 가 링크를 내고 `/p*` 는 잎이다. 도착 시각을 역할별로 적는다."""

    control = False  # True 면 시드가 링크를 안 낸다 — 잴 간격이 사라진다

    def do_GET(self):
        role = self.server.role
        LOG.setdefault(role, []).append(
            (time.monotonic(), self.headers.get("Host", ""), self.path))
        if self.path == "/robots.txt":
            # 대조군에는 선언이 없다 — 하한 1초로 돈다. 두 값이 달라야 "남의 간격에
            # 묶였는지" 를 잴 수 있다
            body = (("User-agent: *\nCrawl-delay: %g\n" % DECLARED).encode()
                    if role == "same" else b"User-agent: *\nDisallow: /nope\n")
            self._send(body, "text/plain")
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

    간격을 재는 e2e 의 가장 위험한 실패는 "잴 대상이 사라졌는데 단언이 공집합 위에서
    참이 되는" 것이다 — 링크를 한 번도 안 따라가면 `all(g >= 2)` 는 참이다.
    실패(1)와 구분되는 코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 표본이 %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def gaps(times):
    return [b - a for a, b in zip(times, times[1:])]


def pages(role):
    """robots.txt 를 뺀 도착 기록. robots 는 같은 워커가 페이지 직전에 받아
    간격이 0초라, 섞으면 재려는 값이 가려진다."""
    return [row for row in LOG.get(role, []) if row[2] != "/robots.txt"]


def run():
    # 세 표기가 전부 같은 서버로 간다. 링크는 **표기를 바꿔가며** 건다 —
    # 상대 경로 `/p3` 는 시드 표기(a.test)로 풀린다
    same = serve("same", ["http://A.test/p1", "http://%s:80/p2" % HOST, "/p3"])
    other = serve("other", ["/q1", "/q2"])
    PORTS.update(dict.fromkeys(SAME, same.server_address[1]))
    PORTS[OTHER] = other.server_address[1]
    urllib.request.install_opener(urllib.request.build_opener(_LocalHTTP))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # 프런티어가 빌 때까지 돈다 (같은 서버 4쪽 + 대조군 3쪽)
            crawl.crawl(["http://%s/" % HOST, "http://%s/" % OTHER], 99,
                        db_path=os.path.join(tmp, "crawl.db"))
    finally:
        urllib.request.install_opener(urllib.request.build_opener())
        for server in (same, other):
            server.shutdown()


def check():
    # 1·2 — 세 표기가 한 칸을 나눠 쓴다. 서버가 본 도착 간격으로 잰다
    arrivals = measured(pages("same"), "같은 서버 페이지 도착", least=4)
    hosts = {host for _, host, _ in arrivals}
    assert hosts == set(SAME), (
        "세 표기가 다 도착하지 않았다: %s — 안 따라간 표기가 있으면 간격 단언이 "
        "공짜로 참이 된다" % sorted(hosts))
    bad = ["%.3f" % g for g in gaps([t for t, _, _ in arrivals])
           if g < DECLARED - JITTER]
    assert not bad, ("표기가 다르다고 %g초 선언이 새어 나갔다 — 서버 수신 간격 %s"
                     % (DECLARED, bad))
    robots = [row for row in LOG.get("same", []) if row[2] == "/robots.txt"]
    assert len(robots) == 1, ("같은 서버의 robots.txt 를 %d회 받았다(표기 %s) — 1회여야 한다"
                              % (len(robots), [h for _, h, _ in robots]))

    # 3 — 대조군. 기본이 아닌 포트는 여전히 다른 도메인이라 남의 2초에 안 묶인다
    ctrl = gaps([t for t, _, _ in
                 measured(pages("other"), "대조군 페이지 도착", least=3)])
    assert all(g >= FLOOR - JITTER for g in ctrl), (
        "대조군이 하한 %g초를 어겼다 — %s" % (FLOOR, ["%.3f" % g for g in ctrl]))
    assert all(g < DECLARED - JITTER for g in ctrl), (
        "기본이 아닌 포트가 %s 의 %g초에 묶였다 — 별개 도메인이어야 한다: %s"
        % (HOST, DECLARED, ["%.3f" % g for g in ctrl]))
    return arrivals, ctrl


def main(argv):
    if "--control" in argv:
        # 시드가 링크를 안 낸다 → 도착이 1건뿐 → 잴 간격이 없다 → 종료 2
        Handler.control = True
        print("[대조] 시드가 링크를 안 낸다 — 측정 불능(2)이 나와야 한다")
    started = time.monotonic()
    run()
    arrivals, ctrl = check()
    print("OK %.1fs — 같은 서버 %d회 도착(표기 %s) 간격 %s · robots 1회 · "
          "대조군(%s) 간격 %s"
          % (time.monotonic() - started, len(arrivals), sorted(set(SAME)),
             ["%.2f" % g for g in gaps([t for t, _, _ in arrivals])],
             OTHER, ["%.2f" % g for g in ctrl]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
