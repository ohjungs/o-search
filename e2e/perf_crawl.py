"""크롤 처리량 측정. concept.md:44 성능 축 2번 — 초당 5문서 이상 지속.

`e2e/perf_search.py` 가 검색 p95 에 하는 일을 크롤 처리량에 한다.
**실제 네트워크를 치지 않는다** — 로컬 서버만 쓴다.

도메인 다양성을 로컬에서 만드는 법: **포트가 곧 netloc 이다.**
`frontier.py:44` 가 `urlsplit(url).netloc` 으로 도메인을 가르므로
`127.0.0.1:PORT` 12개는 프런티어에게 서로 다른 12개 도메인이다.
(`e2e/crawl_delay_e2e.py` 가 호스트 2개로 하던 것의 확장)

**인위 지연 0.4초가 이 측정의 핵심이다.** 지연이 없으면 순차 크롤과 동시 크롤이
같은 숫자를 내서 아무것도 판정하지 못한다. 실제 웹의 응답 대기를 이걸로 흉내낸다.

판정 3개 — 처리량만 재면 간격을 깎아서 통과할 수 있다. 그래서 윤리를 함께 잰다:
  ① 처리량      수집 문서 / 총 소요초 >= 5.0
  ② 도메인 간격  도메인별 페이지 요청 간격이 전부 >= 0.95초
  ③ 중복 없음    같은 URL 을 두 번 요청하지 않았다

실행: PYTHONPATH=src python3 e2e/perf_crawl.py
"""
import collections
import http.server
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch.crawl import crawl  # noqa: E402

DOMAINS = 12
PAGES_PER_DOMAIN = 12          # 프런티어가 굶지 않을 만큼. 48문서를 12도메인이 나눠 낸다
LATENCY = 0.4                  # 초. 응답 대기 흉내 — 이게 0이면 측정이 무의미하다
MAX_PAGES = 48
TARGET_RATE = 5.0              # concept.md:44. 제품 목표라 여기 맞춘다 — 올리지 않는다.
# 이 값이 가르는 것은 **순차(약 2/s) 대 동시(약 10/s)** 까지다. workers 가 8→4 로
# 줄어드는 정도의 동시성 회귀는 여전히 통과한다(상한이 workers/LATENCY 라 4여도 10/s).
# 부분 회귀는 시간이 아니라 `tests/test_crawl.py` 의 `TestConcurrency`(배리어)가 잡는다.
MIN_GAP = 0.95                 # 1.0 - 왕복 지터 여유. crawl_delay_e2e.py:86 과 같은 값

REQUEST_LOG = []               # (시각, netloc, path)
_LOG_LOCK = threading.Lock()   # 서버가 스레드로 응답한다 — 로그만 잠근다


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 요청마다 stderr 로 찍으면 측정 출력이 안 보인다

    def do_GET(self):
        netloc = "127.0.0.1:%d" % self.server.server_address[1]
        with _LOG_LOCK:
            REQUEST_LOG.append((time.monotonic(), netloc, self.path))
        time.sleep(LATENCY)  # 응답 대기
        if self.path == "/robots.txt":
            body, ctype = b"User-agent: *\n", "text/plain"
        elif self.path == "/":
            own = "".join('<a href="/p%d">p%d</a>' % (i, i)
                          for i in range(1, PAGES_PER_DOMAIN))
            others = "".join('<a href="http://%s/">o</a>' % peer
                             for peer in NETLOCS if peer != netloc)
            body = ("<html><title>%s</title>%s%s</html>"
                    % (netloc, own, others)).encode()
            ctype = "text/html"
        elif self.path.startswith("/p"):
            body = ("<html><title>%s%s</title>leaf</html>"
                    % (netloc, self.path)).encode()
            ctype = "text/html"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


NETLOCS = []  # Handler 가 링크를 만들 때 읽는다 — 서버를 다 띄운 뒤 채워진다


def page_gaps():
    """도메인별 **페이지** 요청 간격. robots.txt 는 뺀다 (간격 계약 밖 — digest [4])."""
    by_domain = collections.defaultdict(list)
    for at, netloc, path in sorted(REQUEST_LOG):
        if path != "/robots.txt":
            by_domain[netloc].append(at)
    return {d: [b - a for a, b in zip(ts, ts[1:])] for d, ts in by_domain.items()}


def main():
    servers = []
    for _ in range(DOMAINS):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        NETLOCS.append("127.0.0.1:%d" % server.server_address[1])
    seeds = ["http://%s/" % netloc for netloc in NETLOCS]

    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        saved = crawl(seeds, MAX_PAGES, db_path=os.path.join(tmp, "crawl.db"))
    elapsed = time.monotonic() - started
    for server in servers:
        server.shutdown()

    rate = saved / elapsed
    print("도메인 %d · 응답지연 %.1fs · 수집 %d문서 / %.2fs = **초당 %.2f문서**"
          % (DOMAINS, LATENCY, saved, elapsed, rate))

    assert saved == MAX_PAGES, "수집 %d, 기대 %d — 처리량 이전에 크롤이 덜 돌았다" % (
        saved, MAX_PAGES)

    # ② 윤리 먼저 본다. 간격을 깎아서 빨라진 것이면 통과시키면 안 된다 (concept.md:59)
    gaps = page_gaps()
    measured = [d for d, g in gaps.items() if g]
    assert measured, "간격을 재려면 한 도메인을 두 번 이상 요청해야 한다"
    too_fast = ["%s %.3fs" % (d, g) for d, gs in gaps.items() for g in gs if g < MIN_GAP]
    assert not too_fast, "도메인 간격 1초를 깼다: %s" % too_fast[:5]

    # ③ 같은 URL 을 두 번 받으면 처리량 숫자가 부풀고 남의 서버도 두 번 맞는다
    seen = collections.Counter((netloc, path) for _, netloc, path in REQUEST_LOG
                               if path != "/robots.txt")
    dupes = [k for k, n in seen.items() if n > 1]
    assert not dupes, "같은 URL 을 두 번 요청했다: %s" % dupes[:5]

    # ① 처리량
    assert rate >= TARGET_RATE, (
        "초당 %.2f문서 — concept.md:44 기준 %.1f 미달. "
        "도메인 %d개를 순차로 받으면 1/%.1fs = 초당 %.1f문서가 상한이다"
        % (rate, TARGET_RATE, DOMAINS, LATENCY, 1 / LATENCY))

    print("e2e 통과: 처리량 %.2f/s (기준 %.1f) · 도메인 %d개 간격 전부 %.2fs 이상 · 중복 0"
          % (rate, TARGET_RATE, len(measured), MIN_GAP))
    return 0


if __name__ == "__main__":
    sys.exit(main())
