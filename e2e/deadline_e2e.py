"""deadline e2e — plan_deadline.md 스텝 4/4.

**단위 테스트가 구조적으로 못 보는 두 자리**를 본다. 겹치는 것은 안 다시 잰다.

  시나리오 0  대조군 — 예산을 **안 주면** 오늘과 한 글자도 안 다르다 (계획 4절 [2]).
              이 세계가 몇 페이지를 낼 수 있는지 여기서 재고, 그 수가 아래 둘의 잣대다.
  시나리오 1  CLI 배선 — `--deadline` 값이 정말 `crawl()` 까지 가는가 (변이 M6).
              단위는 `main()` 의 rc 2 경로만 돌아서 **정상값이 흘러가는지 아무도 안 본다.**
  시나리오 2  실시계 — 가짜 시계는 `time.sleep` 에서만 흐르고 `sleep` 은 `inflight` 가
              빌 때만 한다. 그래서 **"떠 있는 요청을 둔 채 예산 만료"** 에 단위는
              도달할 수 없다. 실시계에서는 fetch 도는 동안 시간이 가므로 바로 난다.

**포트가 곧 도메인이다**(`urls.domain_key` — perf_crawl.py 와 같은 수법). 응답 지연을
도메인마다 어긋나게 줘서 예산 만료 순간에 요청이 떠 있도록 만든다.

**간격은 안 깎는다.** 예산이 하는 일은 "덜 보낸다" 뿐이라, 세 시나리오 모두에서
도메인당 1초 하한이 지켜지는지 같이 잰다 — 끝을 당기려고 간격을 깎으면 여기서 죽는다.

**측정 불능(2)은 조용한 통과가 아니다** (계획 4절 [4]). 여기 단언은 전부 "덜 모았다"
꼴이라 **서버가 안 떠서 0페이지여도 전부 참**이다. 대조군이 세계를 먼저 세우고,
못 세우면 초록도 빨강도 아닌 **종료 2** 로 죽는다.

약 10초. 실행:
     PYTHONPATH=src python3 e2e/deadline_e2e.py
     PYTHONPATH=src python3 e2e/deadline_e2e.py --control  # 측정 불능 = 종료 2
"""
import http.server
import os
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from websearch.crawl import crawl  # noqa: E402
from websearch.store import Store  # noqa: E402

# 도메인(포트)별 페이지 응답 지연. **서로 어긋나 있는 것이 요점이다** —
# 같으면 한 라운드가 통째로 같이 끝나 예산 만료 때 떠 있는 요청이 안 남는다
PAGE_DELAY = [0.3, 0.8, 0.9, 1.0]
PAGES_PER_HOST = 4  # 루트 + /p1..3
BUDGET = 2.0
MAX_PAGES = 20  # 예산이 안 걸리면 다 채우도록 넉넉히 — 4도메인 × 1초 간격이라 5초 이상
TOTAL_PAGES = PAGES_PER_HOST * len(PAGE_DELAY)  # 예산이 없으면 이만큼 다 모은다 (대조군이 잰다)

REQUEST_LOG = []  # (시각, 포트, 경로)
LOG_LOCK = threading.Lock()
BROKEN = False  # `--control`: 페이지가 사라진 세계. 측정 불능 가드가 살아 있는지 본다


def make_handler(delay):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            port = self.server.server_address[1]
            if self.path == "/robots.txt":
                # robots 는 안 재운다 — 도메인당 1회 메타 요청이라 지연을 실으면
                # 재는 것이 흐려진다(crawl_delay_e2e.py 와 같은 이유로 간격 계산에서도 뺀다)
                body, ctype = b"User-agent: *\nAllow: /\n", "text/plain"
            elif BROKEN and (self.path == "/" or self.path.startswith("/p")):
                self.send_error(503)  # 잴 대상을 없앤다 — 단언은 여전히 전부 참이 된다
                return
            elif self.path == "/" or self.path.startswith("/p"):
                time.sleep(delay)  # 여기서 요청이 '떠 있는' 상태가 된다
                with LOG_LOCK:
                    REQUEST_LOG.append((time.monotonic(), port, self.path))
                if self.path == "/":
                    links = "".join('<a href="/p%d">%d</a>' % (i, i)
                                    for i in range(1, PAGES_PER_HOST))
                    body = ("<html><title>%d</title>%s</html>" % (port, links)).encode()
                else:
                    body = b"<html><title>leaf</title>leaf</html>"
                ctype = "text/html"
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

    return Handler


def page_gaps(port):
    """그 도메인의 **페이지** 요청 간격. 서버가 응답을 시작한 시각으로 잰다."""
    times = sorted(t for t, p, _ in REQUEST_LOG if p == port)
    return [b - a for a, b in zip(times, times[1:])]


def check_intervals(ports, where):
    """예산이 걸린 크롤도 도메인당 1초 하한을 지키는가. **깎으면 여기서 죽는다.**"""
    measured = []
    for port in ports:
        for gap in page_gaps(port):
            measured.append(gap)
            assert gap >= 0.95, (  # 0.05s 는 왕복 지터 여유 — crawl_delay_e2e.py 와 같은 값
                "%s: 포트 %d 간격 %.3f초 — 예산이 1초 하한을 깎았다" % (where, port, gap))
    return measured


def measured(samples, what, least):
    """표본이 모자라면 **조용히 통과하지 않고** 종료 코드 2로 죽는다.

    `retry_interval_e2e.py`·`url_normalize_e2e.py` 와 같은 관용구다. 이 파일의 위험은
    거기와 똑같다 — "예산이 덜 모으게 했다" 는 단언은 **아무것도 안 모은 세계에서도 참**이다.
    실패(1)와 구분되는 코드를 쓴다: 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.
    """
    if len(samples) < least:
        print("측정 불능 — %s 표본이 %d개다(필요 %d). 잴 대상이 사라졌다"
              % (what, len(samples), least), file=sys.stderr)
        raise SystemExit(2)
    return samples


def scenario_0_control(seeds, ports):
    """대조군 — 예산을 안 주면 오늘 그대로다 (계획 4절 [2]).

    **이 시나리오가 아래 둘의 잣대를 만든다.** 없으면 `saved < TOTAL_PAGES` 가
    서버가 죽었을 때도 참이라 초록이 근거 없이 켜진다.
    """
    with tempfile.TemporaryDirectory() as tmp:
        started = time.monotonic()
        saved = crawl(seeds, MAX_PAGES, db_path=os.path.join(tmp, "crawl.db"), workers=8)
        elapsed = time.monotonic() - started

    # 예산 없이도 다 못 모으는 세계면 "예산이 깎았다" 를 잴 수 없다 — 실패가 아니라 불능이다
    measured([1] * saved, "대조군이 모은 페이지", least=TOTAL_PAGES)
    check_intervals(ports, "대조군")
    return saved, elapsed


def scenario_1_cli_wiring(seeds):
    """`--deadline` 이 CLI 에서 `crawl()` 까지 가는가 (M6).

    배선이 끊기면 셋 다 깨진다: 예산 소진 메시지가 안 나오고, MAX_PAGES 를 다 채우고,
    4도메인 × 1초 간격이라 5초 넘게 돈다.

    **인자 형태를 섞어 준다** — `--deadline=N`(붙임) 과 `--max N`(띄움) 을 한 번에.
    `=` 형태가 조용히 무시되면 예산 없이 돌아 ① 이 죽는다. 단위는 `main()` 을
    직접 부르므로 **진짜 argv 로 오는 형태를 보는 자리는 여기뿐이다.**
    """
    with tempfile.TemporaryDirectory() as tmp:
        os.mkdir(os.path.join(tmp, "data"))  # CLI 는 db 경로를 안 받는다 — cwd 로 가둔다
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"),
                   PYTHONDONTWRITEBYTECODE="1")
        started = time.monotonic()
        proc = subprocess.run(
            [sys.executable, "-m", "websearch.crawl"] + seeds
            + ["--max", str(MAX_PAGES), "--deadline=%d" % int(BUDGET), "--workers=8"],
            cwd=tmp, env=env, capture_output=True, text=True, timeout=60)
        elapsed = time.monotonic() - started
        saved = Store(os.path.join(tmp, "data", "crawl.db")).count()

    assert proc.returncode == 0, "rc %d\n%s" % (proc.returncode, proc.stderr)
    # ① 예산을 본 흔적. 이 줄은 `deadline is not None` 일 때만 찍힌다 — M6 이 여기서 죽는다
    assert "예산" in proc.stderr and "소진" in proc.stderr, (
        "CLI 가 --deadline 을 crawl() 로 안 넘겼다 (M6) — stderr:\n%s" % proc.stderr)
    # ② 예산이 실제로 덜 보내게 했나
    assert saved < MAX_PAGES, (
        "예산 %.0f초인데 max %d 를 다 채웠다 — 배선은 됐지만 예산이 안 먹었다"
        % (BUDGET, MAX_PAGES))
    # ③ 예산 근처에서 끝났나. 상한은 예산 + 응답 하나(최대 1.0s) + 프로세스 기동 여유
    assert elapsed < BUDGET + 4.0, "예산 %.0f초인데 %.1f초 걸렸다" % (BUDGET, elapsed)
    return saved, elapsed, proc.stderr.strip()


def scenario_2_realtime_inflight(seeds, ports):
    """실시계에서 예산이 만료될 때 떠 있던 요청은 어떻게 되는가.

    **줍는다** — 설계 4절이 비워 뒀던 자리를 2026-08-29 에 정했고(`crawl()` 문서열),
    수치만 남기던 이 자리도 그때 단언이 됐다.

    **눈먼 단언이 아니다**: 줍기를 빼고 3회 돌리면 매번 `버려진 응답 1건` 이 나온다
    (2026-08-29 실측). 0 은 "그 라운드에 떠 있던 요청이 없었다" 로도 나올 수 있으므로,
    시나리오가 그 상태를 실제로 만드는지 확인한 뒤에만 이 단언이 뜻을 가진다.
    """
    with tempfile.TemporaryDirectory() as tmp:
        started = time.monotonic()
        saved = crawl(seeds, MAX_PAGES, db_path=os.path.join(tmp, "crawl.db"),
                      deadline=BUDGET, workers=8)
        elapsed = time.monotonic() - started

    assert saved < MAX_PAGES, "예산이 안 먹었다 — %d/%d" % (saved, MAX_PAGES)
    # 서버가 실제로 200 HTML 을 돌려준 페이지 수. 저장된 수보다 많으면 그 차이가
    # **이미 보낸 요청인데 결과를 버린 것**이다 (다음 실행에서 같은 URL 을 또 때린다)
    served = len(REQUEST_LOG)
    discarded = served - saved
    assert discarded == 0, (
        "이미 받은 응답 %d건을 버렸다 — 다음 실행이 같은 URL 을 또 때린다 "
        "(저장 %d / 서버 응답 %d)" % (discarded, saved, served))
    check_intervals(ports, "시나리오 2")
    return saved, elapsed, served, discarded


def main():
    global BROKEN
    BROKEN = "--control" in sys.argv[1:]

    servers = []
    for delay in PAGE_DELAY:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), make_handler(delay))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    ports = [s.server_address[1] for s in servers]
    seeds = ["http://127.0.0.1:%d/" % p for p in ports]

    try:
        # 잣대가 먼저다 — 이 세계가 예산 없이 몇 페이지를 낼 수 있는지 모르면
        # 아래 둘의 "덜 모았다" 가 아무것도 안 모은 세계에서도 참이 된다
        s0_saved, s0_elapsed = scenario_0_control(seeds, ports)
        del REQUEST_LOG[:]  # 시나리오끼리 요청이 섞이면 간격도 유실 수치도 못 잰다
        s1_saved, s1_elapsed, s1_err = scenario_1_cli_wiring(seeds)
        gaps_1 = check_intervals(ports, "시나리오 1")
        del REQUEST_LOG[:]
        s2 = scenario_2_realtime_inflight(seeds, ports)
    finally:
        for server in servers:
            server.shutdown()

    s2_saved, s2_elapsed, served, discarded = s2
    print("e2e 통과 — 도메인 %d개 · 예산 %.0f초" % (len(ports), BUDGET))
    print("  [0] 대조군(예산 없음): %d페이지 전부, %.1fs — 아래 둘의 잣대"
          % (s0_saved, s0_elapsed))
    print("  [1] CLI 배선: %d페이지 / max %d, %.1fs, 예산 소진 보고 있음 "
          "(M6 죽음 · 인자는 --deadline=N 붙임 형태)" % (s1_saved, MAX_PAGES, s1_elapsed))
    print("      stderr: %s" % s1_err.splitlines()[-1] if s1_err else "")
    print("      간격 최소 %.2fs (하한 1초)" % min(gaps_1) if gaps_1 else "")
    print("  [2] 실시계: 저장 %d / 서버가 응답한 페이지 %d, %.1fs"
          % (s2_saved, served, s2_elapsed))
    print("      **버려진 응답 %d건** — 0이어야 한다(단언). 줍기를 빼면 1건이 나온다"
          % discarded)


if __name__ == "__main__":
    main()
