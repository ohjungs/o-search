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

**세 세계에서 잰다.** 같은 하네스로 robots.txt 만 갈아끼운다:
  [열림] 아무것도 안 막는 사이트 — 위 판정 3개
  [차단] 페이지 11개 중 6개를 막는 사이트 — 기준선 처리량 + 막힌 경로 요청 0건
  [예외] 워커가 예외로 끝나는 경우 — 간격이 유지되는가
뒤의 둘은 **workers=8 일 때만 돈다** (되돌리기 경로는 아래 main 에서 일찍 끝난다).

실행: PYTHONPATH=src python3 e2e/perf_crawl.py
"""
import collections
import contextlib
import hashlib
import http.server
import io
import os
import sys
import types
import urllib.parse
import sqlite3
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import crawl as crawl_mod  # noqa: E402
from websearch.crawl import crawl  # noqa: E402

_real_fetcher = crawl_mod.fetcher  # 예외 주입 시나리오가 되돌릴 원본

DOMAINS = 12
PAGES_PER_DOMAIN = 12          # 프런티어가 굶지 않을 만큼. 48문서를 12도메인이 나눠 낸다
LATENCY = 0.4                  # 초. 응답 대기 흉내 — 이게 0이면 측정이 무의미하다
MAX_PAGES = 48
TARGET_RATE = 5.0              # concept.md:44. 제품 목표라 여기 맞춘다 — 올리지 않는다.
# 이 값이 가르는 것은 **순차(약 2/s) 대 동시(약 10/s)** 까지다. workers 가 8→4 로
# 줄어드는 정도의 동시성 회귀는 여전히 통과한다(상한이 workers/LATENCY 라 4여도 10/s).
# 부분 회귀는 시간이 아니라 `tests/test_crawl.py` 의 `TestConcurrency`(배리어)가 잡는다.
MIN_GAP = 0.95                 # 1.0 - 왕복 지터 여유. crawl_delay_e2e.py:86 과 같은 값

# **기준선은 합격선과 다른 질문이다.** TARGET_RATE 는 "제품 목표를 넘나",
# 아래는 "어제보다 나빠졌나". 그리고 기준선에는 **어떤 세계에서 잰 숫자인지**를 적는다 —
# 이걸 안 적어서 8일 동안 못 본 것이 아래 차단 시나리오다 (docs/design_cooldown-burn.md).
BASELINE_BLOCKED = 9.0         # robots 가 페이지 11개 중 6개를 막는 세계. 실측 10.3/s.
# 이 시나리오가 없던 동안 실제 값은 **4.5/s** 로 TARGET_RATE 밑이었고 아무도 몰랐다.
# 팝 시점에 간격 시계를 걸어 요청도 안 보낸 URL 이 쿨다운을 태우고 있었다.

BLOCKED = tuple("/p%d" % i for i in range(1, 7))  # 차단 시나리오가 막는 경로
OPEN_ROBOTS = b"User-agent: *\n"
BLOCKING_ROBOTS = (OPEN_ROBOTS
                   + b"".join(b"Disallow: %s\n" % p.encode() for p in BLOCKED))

REQUEST_LOG = []               # (시각, netloc, path)
_LOG_LOCK = threading.Lock()   # 서버가 스레드로 응답한다 — 로그만 잠근다
ROBOTS_BODY = OPEN_ROBOTS      # 시나리오가 갈아끼운다


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 요청마다 stderr 로 찍으면 측정 출력이 안 보인다

    def do_GET(self):
        netloc = "127.0.0.1:%d" % self.server.server_address[1]
        with _LOG_LOCK:
            REQUEST_LOG.append((time.monotonic(), netloc, self.path))
        time.sleep(LATENCY)  # 응답 대기
        if self.path == "/robots.txt":
            body, ctype = ROBOTS_BODY, "text/plain"
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


def run_crawl(workers, max_pages=MAX_PAGES):
    """서버 12대를 띄우고 한 번 크롤한다. `(rate, saved, elapsed, paths)`.

    `ROBOTS_BODY` 를 갈아끼우면 **같은 하네스로 다른 세계**를 잰다.
    """
    global NETLOCS
    REQUEST_LOG.clear()
    NETLOCS = []
    servers = []
    for _ in range(DOMAINS):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        NETLOCS.append("127.0.0.1:%d" % server.server_address[1])
    seeds = ["http://%s/" % netloc for netloc in NETLOCS]

    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "crawl.db")
        saved = crawl(seeds, max_pages, db_path=db_path, workers=workers)
        # 저장된 URL 집합. 포트가 실행마다 달라 경로만 본다 — 그래야 두 실행을 비교할 수 있다
        paths = sorted(urllib.parse.urlsplit(u).path for (u,) in
                       sqlite3.connect(db_path).execute("SELECT url FROM pages"))
    elapsed = time.monotonic() - started
    for server in servers:
        server.shutdown()
    return saved / elapsed, saved, elapsed, paths


def assert_gaps_kept(label):
    """간격을 깎아서 빨라진 것이면 통과시키면 안 된다 (concept.md:59).

    `(재는 도메인 수, 실측 최소 간격)` 을 돌려준다. **하한이 아니라 실측치를 돌려주는
    이유**: "전부 0.95s 이상" 만 찍으면 1.004s 와 3.0s 가 같은 줄로 보인다. 여유가
    얼마나 남았는지는 회귀가 나기 **전에** 알아야 값이 있다 (기준선에는 값만이 아니라
    어떤 세계에서 잰 숫자인지를 적는다 — docs/project.md).
    """
    gaps = page_gaps()
    measured = [d for d, g in gaps.items() if g]
    assert measured, "%s: 간격을 재려면 한 도메인을 두 번 이상 요청해야 한다" % label
    too_fast = ["%s %.3fs" % (d, g) for d, gs in gaps.items() for g in gs if g < MIN_GAP]
    assert not too_fast, "%s: 도메인 간격 1초를 깼다: %s" % (label, too_fast[:5])
    return len(measured), min(g for gs in gaps.values() for g in gs)


def scenario_blocked():
    """**robots 가 막는 세계.** 이 시나리오가 없어서 8일 동안 4.5/s 를 못 봤다.

    현실의 사이트는 대개 무언가를 막는다. 아무것도 안 막는 사이트만 재는 하네스는
    "빠르다" 고 말하면서 정작 도는 경로가 목표 밑인 것을 못 본다.
    """
    global ROBOTS_BODY
    ROBOTS_BODY = BLOCKING_ROBOTS
    try:
        # 막힌 페이지가 /p1~/p6 이라 도메인당 받을 수 있는 것은 홈 + /p7~/p11 = 6개다
        rate, saved, elapsed, _ = run_crawl(8, max_pages=MAX_PAGES)
    finally:
        ROBOTS_BODY = OPEN_ROBOTS

    print("[차단] robots 가 페이지 %d개를 막는 사이트 · 수집 %d문서 / %.2fs "
          "= **초당 %.2f문서**" % (len(BLOCKED), saved, elapsed, rate))
    assert saved == MAX_PAGES, "[차단] 수집 %d, 기대 %d" % (saved, MAX_PAGES)

    # ③ robots 준수 — 막힌 경로를 한 번이라도 때리면 처리량이 아무리 좋아도 실패다
    # netloc 으로 **이 세계의 서버만** 본다 — 앞 시나리오의 늦은 핸들러 스레드가
    # REQUEST_LOG.clear() 뒤에 한 줄 흘리면 남의 세계 요청으로 여기가 빨개진다
    hits = [(n, p) for _, n, p in REQUEST_LOG if p in BLOCKED and n in NETLOCS]
    assert not hits, "[차단] robots 가 막은 경로를 요청했다: %s" % hits[:5]
    # 긍정 짝 — 허용 경로는 실제로 받았다. 없으면 "아무것도 안 받음" 으로도 통과한다
    allowed_hits = [p for _, n, p in REQUEST_LOG
                    if p.startswith("/p") and p not in BLOCKED and n in NETLOCS]
    assert allowed_hits, "[차단] 허용 경로를 하나도 안 받았다 — 차단이 과했다"

    n, lo = assert_gaps_kept("[차단]")
    assert rate >= BASELINE_BLOCKED, (
        "[차단] 초당 %.2f문서 — 기준선 %.1f 미달. 요청도 안 보낸 URL 이 도메인 쿨다운을 "
        "태우고 있는지 본다 (docs/design_cooldown-burn.md)" % (rate, BASELINE_BLOCKED))
    print("[차단] 통과: %.2f/s (기준선 %.1f) · 도메인 %d개 최소 간격 %.3fs (하한 %.2fs) · "
          "차단 경로 요청 0건" % (rate, BASELINE_BLOCKED, n, lo, MIN_GAP))


def scenario_worker_exception():
    """**요청은 나갔고 결과만 터진 경우에도 간격이 유지되는가.**

    처리량은 안 본다 — 여기서 재는 것은 윤리 하나다. 이 시나리오가 없으면
    "팝 쓰기만 지운" 순진한 수정이 차단 시나리오를 통과해 버린다(설계 탐침 실측:
    차단 시나리오 10.31/s·1.001s 로 통과, 그러나 예외를 섞으면 **0.310s**).

    fetcher 를 감싸 **실제로 요청을 보낸 뒤** 터뜨린다. 네트워크는 진짜로 나간다 —
    그래야 "나간 요청" 의 쿨다운을 다뤄야 하는 상황이 재현된다.
    """
    # **도메인마다 실제로 팝되는 경로여야 한다.** 링크 순서가 곧 팝 순서라
    # 앞쪽 두 개를 고른다 — 뒤쪽을 고르면 상한에 걸려 한 번도 안 터지고,
    # 그러면 이 시나리오가 초록불인 채로 아무것도 안 재게 된다 (실제로 한 번 그랬다)
    boom = {"/p1", "/p2"}
    real_fetch = crawl_mod.fetcher.fetch

    def exploding_fetch(url):
        result = real_fetch(url)  # 요청은 정말로 나갔다
        if urllib.parse.urlsplit(url).path in boom:
            raise RuntimeError("주입한 워커 예외 — %s" % url)
        return result

    crawl_mod.fetcher = types.SimpleNamespace(fetch=exploding_fetch)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            _, saved, _, _ = run_crawl(8, max_pages=MAX_PAGES)
    finally:
        crawl_mod.fetcher = _real_fetcher

    assert saved > 0, "[예외] 크롤이 통째로 죽었다"
    assert "주입한 워커 예외" in err.getvalue(), "[예외] 예외가 조용히 삼켜졌다"
    n, lo = assert_gaps_kept("[예외]")
    print("[예외] 통과: 워커 예외 %d종을 섞어도 도메인 %d개 최소 간격 %.3fs "
          "(하한 %.2fs · 수집 %d문서)" % (len(boom), n, lo, MIN_GAP, saved))


def main():
    # 인자로 워커 수를 받는다. 시나리오 4(되돌리기 경로가 같은 결과를 낸다) 를
    # e2e 수준에서 돌리기 위한 것 — `perf_crawl.py 1` 로 실행한다. 기본은 8.
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    rate, saved, elapsed, paths = run_crawl(workers)
    print("[열림] 도메인 %d · 응답지연 %.1fs · 수집 %d문서 / %.2fs = **초당 %.2f문서**"
          "   ← 아무것도 막지 않는 세계의 숫자다"
          % (DOMAINS, LATENCY, saved, elapsed, rate))

    assert saved == MAX_PAGES, "수집 %d, 기대 %d — 처리량 이전에 크롤이 덜 돌았다" % (
        saved, MAX_PAGES)

    # ② 윤리 먼저 본다. 간격을 깎아서 빨라진 것이면 통과시키면 안 된다 (concept.md:59)
    measured_n, lo = assert_gaps_kept("[열림]")

    # ③ 같은 URL 을 두 번 받으면 처리량 숫자가 부풀고 남의 서버도 두 번 맞는다
    seen = collections.Counter((netloc, path) for _, netloc, path in REQUEST_LOG
                               if path != "/robots.txt")
    dupes = [k for k, n in seen.items() if n > 1]
    assert not dupes, "같은 URL 을 두 번 요청했다: %s" % dupes[:5]

    # 시나리오 4: 워커 수가 달라도 **결과 문서 집합이 같다**. 포트가 매번 달라 경로로 비교한다
    print("문서집합(경로 %d개) sha1: %s"
          % (len(paths), hashlib.sha1("\n".join(paths).encode()).hexdigest()))

    # ① 처리량 — 되돌리기 경로(workers=1)는 느린 게 정상이라 이 판정에서 뺀다
    if workers < 8:
        print("workers=%d — 되돌리기 경로라 처리량 판정은 건너뛴다 "
              "(간격·중복·문서집합은 위에서 그대로 봤다). "
              "**[차단]·[예외] 시나리오도 안 돈다** — 둘 다 동시성 계약을 재는 것이라 "
              "워커 1개에서는 잴 것이 없다" % workers)
        return 0

    assert rate >= TARGET_RATE, (
        "초당 %.2f문서 — concept.md:44 기준 %.1f 미달. "
        "도메인 %d개를 순차로 받으면 1/%.1fs = 초당 %.1f문서가 상한이다"
        % (rate, TARGET_RATE, DOMAINS, LATENCY, 1 / LATENCY))

    print("[열림] 통과: 처리량 %.2f/s (기준 %.1f) · 도메인 %d개 최소 간격 %.3fs "
          "(하한 %.2fs) · 중복 0" % (rate, TARGET_RATE, measured_n, lo, MIN_GAP))

    # **여기서 끝내면 안 된다.** 위 숫자는 아무것도 막지 않는 세계의 것이고,
    # 현실의 사이트는 대개 무언가를 막는다 (docs/design_cooldown-burn.md 범위 밖 절)
    scenario_blocked()
    scenario_worker_exception()
    print("e2e 통과: 3시나리오(열림·차단·워커예외) 전부 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
