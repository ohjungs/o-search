"""retry-interval e2e — plan_retry-interval.md 5절의 시나리오 그대로.

계획이 연 문제는 **한 서버인데 두 경로가 다른 값을 쓴다**는 것이었다.
`robots.txt` 는 스킴별 문서라 `https` 쪽에는 선언이 없고, `_fetch_one` 이 그것만 보면
`http` 가 선언한 5초를 모른 채 **1초로 재시도**한다. 프런티어는 netloc 단위로 모아
5초를 알고 있는데도 그랬다.

여기서는 그것을 실물로 잰다 — 진짜 소켓·진짜 HTTP·진짜 robots·진짜 프런티어·진짜
`fetcher` 재시도. 그리고 **우리가 의도한 시각이 아니라 서버에 닿은 시각**을 잰다
(`crawl_politeness_e2e.py` 와 같은 자세).

  1 `http` 만 `Crawl-delay: 5` 인 서버의 `https` **재시도 간격이 5초 이상**
  2 대조군(선언 없는 도메인)의 재시도는 1초대 — **남의 값이 새지 않는다**
  3 잴 대상이 사라지면(재시도 표본 부족) **종료 코드 2**

**한 가지만 주입한다: 스킴이 어느 포트로 가느냐.** TLS 를 세우지 않고
`https://127.0.0.1/` 를 로컬 평문 서버로 보낸다 — hosts 파일이 하는 일과 같은 층이다.
URL·robots 캐시 열쇠·프런티어 열쇠는 전부 진짜 그대로다. **포트를 안 쓰는 것이 핵심**
이다: `http://127.0.0.1/` 와 `https://127.0.0.1/` 는 netloc 이 같아야(둘 다 `127.0.0.1`)
프런티어가 한 도메인으로 보고, robots 는 `스킴://netloc` 으로 캐시해 서로 다른
`robots.txt` 를 본다. 포트를 붙이면 netloc 이 갈려 이 상황 자체가 안 만들어진다.

시간이 걸리는 것이 정상이다(간격을 실제로 잰다). 약 17초.
실행: PYTHONPATH=src python3 e2e/retry_interval_e2e.py
     PYTHONPATH=src python3 e2e/retry_interval_e2e.py --control  # 측정 불능 = 종료 2
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

from websearch import crawl, fetcher  # noqa: E402

DECLARED = 5.0   # http 쪽 robots 가 선언하는 값
FLOOR = 1.0      # 선언이 없을 때의 하한 (frontier.DOMAIN_INTERVAL)
JITTER = 0.05    # 왕복 지터가 서버 수신 시각에 실린다 — crawl_e2e.py 와 같은 값

SLOW, CTRL = "127.0.0.1", "localhost"
PORTS = {}       # (스킴, 호스트) -> 로컬 포트
LOG = {}         # 역할 -> [서버가 요청을 받은 시각]


class Handler(http.server.BaseHTTPRequestHandler):
    """역할은 **서버 인스턴스**가 들고 있다 — Host 헤더에 안 기댄다.

    `/boom` 은 요청줄만 읽고 응답 없이 끊어 `RemoteDisconnected` 를 만든다.
    `fetcher` 가 재시도하는 바로 그 경로다. `--control` 이면 정상 응답한다 —
    재시도가 사라져 **잴 것이 없어진다**.
    """

    control = False

    def do_GET(self):
        role = self.server.role
        if self.path == "/robots.txt":
            # 선언은 http 쪽에만 있다. https 쪽 robots 에는 Crawl-delay 가 없다 —
            # 이 비대칭이 계획이 연 문제 전부다
            body = b"User-agent: *\nCrawl-delay: 5\n" if role == "slow-http" \
                else b"User-agent: *\nDisallow: /nope\n"
            self._send(body, "text/plain")
            return
        if self.path == "/":
            body = ('<html><title>%s</title><body><a href="%s">boom</a></body></html>'
                    % (role, self.server.link)).encode()
            self._send(body, "text/html")
            return
        LOG.setdefault(role, []).append(time.monotonic())
        if Handler.control:
            self._send(b"<html>ok</html>", "text/html")
            return
        self.close_connection = True  # 응답을 안 쓴다

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve(role, link=""):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.role, server.link = role, link
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _routed(scheme):
    """`scheme` 의 요청을 `PORTS` 가 가리키는 로컬 포트로 보내는 커넥션 공장."""
    def factory(host, **kw):
        return http.client.HTTPConnection("127.0.0.1", PORTS[(scheme, host)], **kw)
    return factory


class _LocalHTTP(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_routed("http"), req)


class _LocalHTTPS(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_routed("https"), req)  # TLS 없이 평문으로 — 층만 바꾼다


def measured(samples, what, least):
    """표본이 모자라면 **조용히 통과하지 않고** 종료 코드 2로 죽는다.

    간격을 재는 e2e 의 가장 위험한 실패는 "잴 대상이 사라졌는데 단언이 공집합 위에서
    참이 되는" 것이다 — 재시도가 아예 안 나가면 `all(g >= 5)` 는 참이다.
    실패(1)와 구분되는 코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 표본이 %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def gaps(times):
    return [b - a for a, b in zip(times, times[1:])]


def run():
    """두 도메인을 한 번의 크롤로 돌린다. 서로 다른 netloc 이라 간섭하지 않는다."""
    slow_https = serve("slow-https")
    slow_http = serve("slow-http", link="https://%s/boom" % SLOW)
    ctrl = serve("ctrl", link="/boom")
    PORTS.update({
        ("http", SLOW): slow_http.server_address[1],
        ("https", SLOW): slow_https.server_address[1],
        ("http", CTRL): ctrl.server_address[1],
    })
    urllib.request.install_opener(
        urllib.request.build_opener(_LocalHTTP, _LocalHTTPS))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # 프런티어가 빌 때까지 돈다 — boom 은 한 번도 수집으로 안 세진다
            crawl.crawl(["http://%s/" % SLOW, "http://%s/" % CTRL], 99,
                        db_path=os.path.join(tmp, "crawl.db"))
    finally:
        urllib.request.install_opener(urllib.request.build_opener())
        for server in (slow_http, slow_https, ctrl):
            server.shutdown()


def check():
    tries = 1 + fetcher.RETRIES
    slow = gaps(measured(LOG.get("slow-https", []), "https 재시도", least=tries))
    assert len(slow) == tries - 1, \
        "https 시도가 %d회다 — RETRIES=%d 와 안 맞는다" % (len(slow) + 1, fetcher.RETRIES)
    bad = ["%.3f" % g for g in slow if g < DECLARED - JITTER]
    assert not bad, ("http 이 선언한 %g초를 같은 서버의 https 재시도가 안 지켰다 — "
                     "간격 %s (프런티어는 알고 있었다)" % (DECLARED, bad))

    floor = gaps(measured(LOG.get("ctrl", []), "대조군 재시도", least=tries))
    too_fast = ["%.3f" % g for g in floor if g < FLOOR - JITTER]
    assert not too_fast, "대조군의 하한 %g초가 풀렸다: %s" % (FLOOR, too_fast)
    leaked = ["%.3f" % g for g in floor if g >= 2.0]
    assert not leaked, ("남의 도메인 선언이 대조군에 샜다 — 간격 %s. "
                        "전부 5초로 재우면 이 단언이 잡는다" % leaked)
    return min(slow), min(floor)


def main(argv):
    if "--control" in argv:
        # 대조군: 끊지 않으면 재시도가 사라진다. 단언들은 공집합 위에서 참이 되는데
        # `measured` 가 그 앞에서 종료 코드 2로 죽어야 옳다
        Handler.control = True
        run()
        check()
        print("대조군이 그냥 통과했다 — 측정 불능 가드가 죽어 있다", file=sys.stderr)
        return 1

    started = time.monotonic()
    run()
    slow, ctrl = check()
    print("e2e 통과 — %.1fs / https 재시도 최소 %.2fs(http 선언 %g초, 고치기 전 1.0) · "
          "대조군 최소 %.2fs(하한 %g초, 안 샜다)"
          % (time.monotonic() - started, slow, DECLARED, ctrl, FLOOR))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
