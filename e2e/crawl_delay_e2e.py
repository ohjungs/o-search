"""crawl-delay e2e — plan_crawl-delay.md 의 시나리오 그대로.

같은 로컬 서버를 **두 도메인**으로 쓴다(`127.0.0.1` 과 `localhost` 는 netloc 이 다르다).
Host 헤더로 robots.txt 를 갈라 낸다:

  127.0.0.1 → `Crawl-delay: 2`   느리게 달라고 요청한 사이트
  localhost → `Crawl-delay: 0`   빨리 와도 된다고 말하는 사이트 (전제 조건은 못 푼다)

검증: ① 두 사이트 6페이지 수집 ② 127.0.0.1 요청 간격 ≥ 2초
③ localhost 요청 간격 ≥ 1초이면서 2초 미만 — **하한은 지키고, 남의 간격이 새지 않는다**

시간이 걸리는 것이 정상이다(간격을 실제로 잰다). 약 4.5초.
실행: PYTHONPATH=src python3 e2e/crawl_delay_e2e.py
"""
import http.server
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch.crawl import crawl  # noqa: E402

REQUEST_LOG = []  # (시각, host, 경로)

DELAY_BY_HOST = {"127.0.0.1": "2", "localhost": "0"}
PAGES_PER_HOST = 3


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get("Host", "").split(":")[0]
        REQUEST_LOG.append((time.monotonic(), host, self.path))
        if self.path == "/robots.txt":
            body = ("User-agent: *\nCrawl-delay: %s\n"
                    % DELAY_BY_HOST.get(host, "0")).encode()
            ctype = "text/plain"
        elif self.path == "/":
            anchors = "".join('<a href="/p%d">%d</a>' % (i, i)
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


def page_gaps(host):
    """그 호스트의 **페이지** 요청 간격. robots.txt 는 도메인당 1회 메타 요청이라 뺀다."""
    times = [t for t, h, path in REQUEST_LOG if h == host and path != "/robots.txt"]
    return [b - a for a, b in zip(times, times[1:])]


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    seeds = ["http://%s:%d/" % (host, port) for host in DELAY_BY_HOST]

    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        saved = crawl(seeds, len(DELAY_BY_HOST) * PAGES_PER_HOST,
                      db_path=os.path.join(tmp, "crawl.db"))
    server.shutdown()
    elapsed = time.monotonic() - started

    want = len(DELAY_BY_HOST) * PAGES_PER_HOST
    assert saved == want, "수집 %d != %d — 간격을 지키느라 빠뜨리면 안 된다" % (saved, want)

    # 왕복 지터가 서버 수신 시각에 실린다. 0.05s 여유는 crawl_e2e.py 와 같은 값이다.
    slow = page_gaps("127.0.0.1")
    assert slow, "간격을 재려면 같은 호스트를 두 번 이상 요청해야 한다"
    bad = ["%.3f" % g for g in slow if g < 1.95]
    assert not bad, "Crawl-delay: 2 인데 2초 미만 간격 %s" % bad

    floor = page_gaps("localhost")
    assert floor, "localhost 페이지 요청이 2건 미만이다"
    too_fast = ["%.3f" % g for g in floor if g < 0.95]
    assert not too_fast, "Crawl-delay: 0 이 1초 하한을 풀었다: %s" % too_fast
    # 느린 쪽 간격이 이쪽까지 오면 도메인별이 아니라 전역으로 느려진 것이다
    leaked = ["%.3f" % g for g in floor if g >= 1.95]
    assert not leaked, "남의 Crawl-delay 가 localhost 에 샜다: %s" % leaked

    print("e2e 통과 — %d페이지 %.1fs / Crawl-delay:2 최소 %.2fs · 하한 도메인 최소 %.2fs"
          % (saved, elapsed, min(slow), min(floor)))


if __name__ == "__main__":
    main()
