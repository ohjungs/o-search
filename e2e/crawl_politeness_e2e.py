"""crawl-politeness e2e — plan_crawl-politeness.md 의 시나리오 그대로.

`crawl_delay_e2e.py` 가 **정상 경로**의 간격을 재는 데 반해, 여기서는 계획 013 이 연
**두 구멍**을 실물로 재현한다. 진짜 소켓·진짜 HTTP·진짜 robots·진짜 프런티어를 쓴다
(바깥 네트워크는 안 탄다 — 서버는 전부 로컬 임시 포트다).

  A 워커가 예외로 끝나도 `Crawl-delay` 를 지키는가   (실측 구멍: 1.0초, 요구 2초)
  B `fetcher` 의 재시도가 도메인 간격을 지키는가      (실측 구멍: 0.0002초, 하한 1초)

A 는 두 도메인을 쓴다 — `127.0.0.1` 은 `Crawl-delay: 2`, `localhost` 는 `0`(하한 대조군).
B 는 **자기 포트**를 쓴다(포트가 다르면 netloc 이 다르다). 요청줄만 읽고 응답 없이
연결을 끊어 `RemoteDisconnected` 를 만든다 — `fetcher` 가 재시도하는 바로 그 경로다.

시간이 걸리는 것이 정상이다(간격을 실제로 잰다). 약 8초.
실행: PYTHONPATH=src python3 e2e/crawl_politeness_e2e.py
     PYTHONPATH=src python3 e2e/crawl_politeness_e2e.py --control  # 측정 불능 = 종료 2
"""
import http.server
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import crawl, fetcher  # noqa: E402

DELAY_BY_HOST = {"127.0.0.1": "2", "localhost": "0"}
PAGES_PER_HOST = 3
SLOW, FLOOR = "127.0.0.1", "localhost"
JITTER = 0.05  # 왕복 지터가 서버 수신 시각에 실린다 — crawl_e2e.py 와 같은 값


def measured(samples, what, least=2):
    """표본이 모자라면 **조용히 통과하지 않고** 종료 코드 2로 죽는다.

    간격을 재는 e2e 의 가장 위험한 실패는 "잴 대상이 사라졌는데 단언이 공집합 위에서
    참이 되는" 것이다 — 크롤러가 재시도를 아예 안 하게 되면 `all(g >= 1.0)` 은 참이다.
    실패(1)와 구분되는 코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 표본이 %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def gaps(times):
    return [b - a for a, b in zip(times, times[1:])]


class PagesHandler(http.server.BaseHTTPRequestHandler):
    """A 용. Host 헤더로 robots.txt 를 갈라 두 도메인을 한 서버로 흉내낸다."""

    log = []  # (시각, host, 경로)
    port = 0

    def do_GET(self):
        host = self.headers.get("Host", "").split(":")[0]
        PagesHandler.log.append((time.monotonic(), host, self.path))
        if self.path == "/robots.txt":
            body = ("User-agent: *\nCrawl-delay: %s\n"
                    % DELAY_BY_HOST.get(host, "0")).encode()
            ctype = "text/plain"
        elif self.path == "/":
            # 대조군 도메인의 시드 하나가 **두 도메인의 URL 을 전부** 낸다.
            # 느린 도메인은 자기 페이지를 한 번도 성공시키지 못해야 한다 — 성공하면
            # 성공 가지가 간격을 걸어 **예외 가지가 재고 싶은 것을 가린다**
            anchors = "".join(
                '<a href="/p%d">%d</a><a href="http://%s:%d/p%d">s%d</a>'
                % (i, i, SLOW, PagesHandler.port, i, i)
                for i in range(1, PAGES_PER_HOST))
            body = ("<html><title>%s</title>%s</html>" % (host, anchors)).encode()
            ctype = "text/html"
        elif self.path.startswith("/p"):
            body, ctype = b"<html>leaf</html>", "text/html"
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


class DropHandler(http.server.BaseHTTPRequestHandler):
    """B 용. robots.txt 만 정상으로 주고, 페이지는 **응답 없이 연결을 끊는다**.

    클라이언트는 `RemoteDisconnected` 를 받는다 — `fetcher` 가 재시도하는 그 경로다.
    `--control` 이면 정상 응답한다: 재시도가 사라져 **B 를 잴 수 없게** 된다.
    """

    log = []      # 페이지 요청이 서버에 닿은 시각 = 시도 하나당 하나
    control = False

    def do_GET(self):
        if self.path == "/robots.txt":
            body = b"User-agent: *\nDisallow: /nope\n"  # Crawl-delay 없음 = 하한 1초
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        DropHandler.log.append(time.monotonic())
        if DropHandler.control:
            body = b"<html>ok</html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.close_connection = True  # 요청줄만 읽고 끊는다 — 응답을 안 쓴다

    def log_message(self, *args):
        pass


def serve(handler):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def dying_fetch(boom):
    """`boom` 인 URL 은 **요청을 진짜로 보낸 뒤** 워커가 죽는다.

    가짜가 아니라 진짜 `fetcher.fetch` 를 그대로 부르고 결과를 버린다 — 발신 훅도
    재시도도 전부 진짜가 돈다(`**kw` 로 삼키지 않는다). 워커 예외는 원래 버그로
    생기는 것이라 실물로 만들 방법이 없어, 이 한 점만 주입한다.
    """
    real = fetcher.fetch

    def fetch(url, **kw):
        result = real(url, **kw)
        if url in boom:
            raise RuntimeError("워커가 죽었다 — 요청은 이미 나갔다")
        return result

    return fetch


def scenario_a():
    """예외로 끝난 워커가 `Crawl-delay: 2` 를 잊지 않는가. 대조군은 하한 1초 도메인."""
    server, port = serve(PagesHandler)
    PagesHandler.port = port
    # 느린 도메인은 **시드가 아니다** — 대조군의 시드 페이지가 링크로 물어온다
    seeds = ["http://%s:%d/" % (FLOOR, port)]
    boom = {"http://%s:%d/p%d" % (SLOW, port, i) for i in range(1, PAGES_PER_HOST)}
    real = fetcher.fetch
    fetcher.fetch = dying_fetch(boom)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # 프런티어가 빌 때까지 돈다 — 느린 도메인 요청은 하나도 수집으로 안 세진다
            crawl.crawl(seeds, 99, db_path=os.path.join(tmp, "crawl.db"))
    finally:
        fetcher.fetch = real
        server.shutdown()

    def pages(host):
        return [t for t, h, path in PagesHandler.log
                if h == host and path != "/robots.txt"]

    slow = gaps(measured(pages(SLOW), "%s 페이지 요청" % SLOW))
    assert all(p in [u.split(str(port))[-1] for u in boom]
               for _, h, p in PagesHandler.log
               if h == SLOW and p != "/robots.txt"), \
        "느린 도메인에 성공한 요청이 섞였다 — 성공 가지가 예외 가지를 가린다"
    bad = ["%.3f" % g for g in slow if g < 2 - JITTER]
    assert not bad, "워커가 죽자 Crawl-delay: 2 를 잊었다 — 간격 %s" % bad

    floor = gaps(measured(pages(FLOOR), "%s 페이지 요청" % FLOOR))
    too_fast = ["%.3f" % g for g in floor if g < 1 - JITTER]
    assert not too_fast, "하한 1초가 풀렸다: %s" % too_fast
    leaked = ["%.3f" % g for g in floor if g >= 2 - JITTER]
    assert not leaked, "남의 Crawl-delay 가 대조군 도메인에 샜다: %s" % leaked
    return min(slow), min(floor)


def scenario_b():
    """연결이 끊기는 도메인의 **재시도 3회**가 각각 1초 넘게 벌어지는가."""
    server, port = serve(DropHandler)
    seed = "http://127.0.0.1:%d/" % port
    try:
        with tempfile.TemporaryDirectory() as tmp:
            crawl.crawl([seed], 1, db_path=os.path.join(tmp, "crawl.db"))
    finally:
        server.shutdown()

    attempts = measured(DropHandler.log, "연결 시도", least=1 + fetcher.RETRIES)
    assert len(attempts) == 1 + fetcher.RETRIES, \
        "시도가 %d회다 — RETRIES=%d 와 안 맞는다" % (len(attempts), fetcher.RETRIES)
    retries = gaps(attempts)
    bad = ["%.4f" % g for g in retries if g < 1 - JITTER]
    assert not bad, "재시도가 도메인 간격을 안 지켰다 — 간격 %s" % bad
    return min(retries)


def main(argv):
    if "--control" in argv:
        # 대조군: 끊지 않으면 재시도가 사라진다. 그때 B 의 단언은 **공집합 위에서 참**이
        # 되어야 하는데, `measured` 가 먼저 종료 코드 2로 죽어야 옳다
        DropHandler.control = True
        scenario_b()
        print("대조군이 그냥 통과했다 — 측정 불능 가드가 죽어 있다", file=sys.stderr)
        return 1

    started = time.monotonic()
    slow, floor = scenario_a()
    retry = scenario_b()
    print("e2e 통과 — %.1fs / A 예외 뒤 최소 %.2fs(요구 2s) · 대조군 최소 %.2fs(하한 1s) "
          "/ B 재시도 최소 %.2fs(하한 1s)"
          % (time.monotonic() - started, slow, floor, retry))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
