"""중단 e2e — plan_graceful-interrupt.md 스텝 4/4, 5절 시나리오 그대로.

**단위 테스트가 구조적으로 못 보는 것을 본다: 진짜 SIGINT 를 진짜 프로세스에.**
단위는 설치된 핸들러를 손으로 부른다 — `os.kill` 을 쓰면 핸들러가 자기를 `SIG_DFL` 로
내린 뒤라 테스트 프로세스가 죽기 때문이다(스텝 3 에서 배운 것). 그래서 **신호가
프로세스에 도착해서 크롤이 접히기까지의 전 구간**을 본 사람이 아직 아무도 없다.
`crawl()` 직접 호출이 아니라 **CLI 서브프로세스**로 재는 이유이기도 하다 — 계획 020 의
변이 M6(CLI 가 인자를 안 넘긴다)은 단위에 안 잡힌 전례가 있다.

  시나리오 0  대조군 — 신호를 **안 보내면** 오늘 그대로다. 아래 넷의 잣대다.
  시나리오 1  응답 없는 서버 + `Crawl-delay: 30` → SIGINT 뒤 12초 안에 rc 130,
              서버가 받은 페이지 요청 **1건**, DB **0행**(안 받은 페이지를 안 박는다).
  시나리오 2  느린 서버 → 이미 나간 요청의 응답은 **줍는다**(DB 1행). 회귀 방지용.
  시나리오 3  예절 — 시나리오 1 의 요청 수신 간격이 `Crawl-delay` 미만이 아니다.
              **중단이 예절의 예외가 되는 순간 이 계획은 실패다**(계획 7절).
  시나리오 4  두 번째 Ctrl-C → 기본 동작으로 즉사한다(사용자가 탈출구를 잃지 않는다).

**포트가 도메인이다**(`urls.domain_key` — deadline_e2e.py 와 같은 수법). 세 서버가
각각 다른 세계를 산다: 안 답하는 서버 · 느린 서버 · 빠른 서버(대조군).

**고정 sleep 으로 신호 시점을 잡지 않는다.** 탐침이 쓰던 "0.5초 뒤 SIGINT" 는 어떤
날은 파이썬 부팅에도 못 미친다 — 요청이 안 나간 채로 신호를 보내면 잴 것이 없는데
초록이 켜진다. **서버가 그 요청을 받은 것을 보고** 신호를 보낸다.

종료 코드: 0 통과 / 1 위반 / 2 측정 불능(잴 대상이 사라졌다 — 계획 4절 [4]).

  PYTHONPATH=src python3 e2e/interrupt_e2e.py
  PYTHONPATH=src python3 e2e/interrupt_e2e.py --control   # 세계를 깨고 불능 가드만 확인 → 2
"""
import http.server
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from websearch.store import Store  # noqa: E402

CRAWL_DELAY = 30  # 안 답하는/느린 서버가 선언하는 간격. 재시도가 접히는지를 재는 잣대
SLOW_SECONDS = 5.0  # 느린 서버의 응답 지연. `fetcher.TIMEOUT` 10초 안이어야 '느린' 이지
#                     '죽은' 이 아니다 — 계획서는 8초를 적었지만 여유 2초는 부하가 걸린
#                     기계에서 타임아웃으로 새고, 재는 것(응답을 줍는가)은 값과 무관하다
CONTROL_PAGES = 3  # 대조군이 모아야 하는 페이지 수(루트 + /p1 + /p2)

REQUEST_LOG = []  # (수신 시각, 포트, 경로) — **응답이 아니라 도착**을 적는다. 간격도 이쪽이다
LOG_LOCK = threading.Lock()
BROKEN = False  # `--control`: 페이지가 사라진 세계. 잴 대상이 없으면 초록이 아니라 2 다


def make_handler(mode):
    """mode: "hang" 안 답한다 · "slow" 늦게 답한다 · "fast" 바로 답한다."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            port = self.server.server_address[1]
            if self.path == "/robots.txt":
                # robots 는 안 재우고 안 적는다 — 도메인당 1회 메타 요청이라 간격
                # 계산에 넣으면 재는 것이 흐려진다(crawl_delay_e2e.py 와 같은 이유)
                delay = 0 if mode == "fast" else CRAWL_DELAY
                self._send(b"User-agent: *\nCrawl-delay: %d\n" % delay, "text/plain")
                return
            with LOG_LOCK:
                REQUEST_LOG.append((time.monotonic(), port, self.path))
            if BROKEN:
                self.send_error(503)  # 잴 대상을 없앤다 — 단언은 여전히 전부 참이 된다
                return
            if mode == "hang":
                # `fetcher` 의 소켓 타임아웃 10초를 실제로 태운다. 스레드는 데몬이라
                # (ThreadingHTTPServer) e2e 가 끝날 때 같이 죽는다
                time.sleep(120)
                return
            if mode == "slow":
                time.sleep(SLOW_SECONDS)
            if self.path == "/":
                body = (b'<html><title>root</title>'
                        b'<a href="/p1">1</a><a href="/p2">2</a></html>')
            else:
                body = b"<html><title>leaf</title>leaf</html>"
            self._send(body, "text/html")

        def _send(self, body, ctype):
            self.send_response(200)
            self.send_header("Content-Type", "%s; charset=utf-8" % ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


def unmeasurable(why):
    """실패(1)와 다른 코드로 나간다 — 초록도 빨강도 아니고 **못 쟀다**는 뜻이다.

    `deadline_e2e.py`·`retry_interval_e2e.py` 와 같은 규약. 잴 대상이 사라지면
    아래 단언들은 **아무 일도 안 일어난 세계에서도 참**이 된다.
    """
    print("측정 불능 — %s" % why, file=sys.stderr)
    raise SystemExit(2)


def page_hits(port):
    with LOG_LOCK:
        return [(t, path) for t, p, path in REQUEST_LOG if p == port]


def wait_for_request(port, timeout=20.0):
    """서버가 그 포트로 페이지 요청을 **받을 때까지** 기다린다.

    신호를 보낼 시점을 여기서 잡는다. 고정 sleep 을 쓰면 요청이 나가기도 전에
    신호가 가는 날이 생기고, 그때 이 e2e 는 아무것도 안 재고 초록을 켠다.
    """
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        if page_hits(port):
            return True
        time.sleep(0.02)
    return False


def start_crawl(tmp, seed, max_pages=5):
    os.mkdir(os.path.join(tmp, "data"))  # 기본 db_path 는 cwd 기준 data/crawl.db
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"),
               PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen(
        [sys.executable, "-m", "websearch.crawl", seed,
         "--max", str(max_pages), "--workers", "1"],
        env=env, cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def finish(proc, timeout, what):
    """끝나기를 기다린다. **안 끝나면 죽이고 위반으로 친다** — 무한 대기는 이 계획이
    다루는 바로 그 실패라, 여기서 e2e 가 같이 매달리면 안 된다."""
    try:
        return proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise AssertionError("%s: %g초 안에 안 끝났다 — 중단이 안 먹었다"
                             % (what, timeout))


def saved_rows(tmp):
    return Store(os.path.join(tmp, "data", "crawl.db")).count()


def scenario_0_control(seed):
    """대조군 — 신호를 안 보내면 오늘 그대로다. **없으면 아래 넷이 근거를 잃는다**:
    서버가 죽어 요청이 한 건도 안 나가는 세계에서도 "빨리 끝났다" 는 참이다."""
    with tempfile.TemporaryDirectory() as tmp:
        proc = start_crawl(tmp, seed, max_pages=CONTROL_PAGES)
        started = time.monotonic()
        out, err = finish(proc, 60, "대조군")
        elapsed = time.monotonic() - started
        saved = saved_rows(tmp)
    if proc.returncode != 0 or saved < CONTROL_PAGES:
        unmeasurable("대조군이 rc %d · %d행이다(기대 rc 0 · %d행). 크롤이 도는 세계가 "
                     "아니면 중단을 잴 수 없다\n%s"
                     % (proc.returncode, saved, CONTROL_PAGES, err.strip()[-400:]))
    assert "중단" not in err, "신호를 안 보냈는데 중단으로 끝났다: %s" % err.strip()[-200:]
    return saved, elapsed


def scenario_1_and_3_hang(seed, port):
    """안 답하는 서버 + `Crawl-delay: 30`. 오늘(신호 전) 실측 69.57초 걸리던 자리다.

    셋을 한 번에 잰다 — 같은 실행이 낳는 사실이라 나누면 두 번 더 기다릴 뿐이다:
    ① 12초 안에 rc 130 ② 페이지 요청 1건 ③ 그 요청들의 간격이 `Crawl-delay` 미만이 아니다.
    ③ 은 요청이 1건이면 자동 통과다 — **2건 이상 나가는 순간 여기서 죽으라고** 있다
    (재시도 취소를 빼면 10초 간격으로 3발이 나간다 — 계획 2절 3번).
    """
    with tempfile.TemporaryDirectory() as tmp:
        proc = start_crawl(tmp, seed)
        if not wait_for_request(port):
            proc.kill()
            proc.communicate()
            unmeasurable("중단할 요청이 서버에 도착하지 않았다")
        sent_at = time.monotonic()
        proc.send_signal(signal.SIGINT)
        out, err = finish(proc, 40, "시나리오 1")
        elapsed = time.monotonic() - sent_at
        saved = saved_rows(tmp)

    assert proc.returncode == 130, (
        "중단 종료 코드가 130 이 아니라 %d 다 — 핸들러가 안 걸렸다\n%s"
        % (proc.returncode, err.strip()[-400:]))
    assert elapsed <= 12.0, "SIGINT 뒤 %.1f초 걸렸다(목표 12초)" % elapsed
    hits = page_hits(port)
    assert len(hits) == 1, (
        "안 답하는 서버에 페이지 요청이 %d건 나갔다 — 재시도가 안 접혔다: %s"
        % (len(hits), [p for _, p in hits]))
    # 안 받은 페이지를 status 0 으로 박으면 다음 실행이 그 URL 을 영영 건너뛴다 (계약 5)
    assert saved == 0, "응답을 못 받았는데 DB 에 %d행이 들어갔다" % saved
    times = [t for t, _ in hits]
    gaps = [b - a for a, b in zip(times, times[1:])]
    bad = ["%.2f" % g for g in gaps if g < CRAWL_DELAY - 0.05]
    assert not bad, ("중단 중에 `Crawl-delay: %d` 를 어겼다 — 간격 %s초"
                     % (CRAWL_DELAY, bad))
    return elapsed, len(hits)


def scenario_2_inflight_is_kept(seed, port):
    """느린 서버 — **이미 나간 요청의 응답은 줍는다**(`crawl()` 독스트링, 설계 4절).

    버리면 받아 놓은 페이지를 버린 채 다음 실행이 같은 URL 을 또 때린다 — 크롤
    윤리로도 손해다. `Crawl-delay: 30` 이라 **메인 루프의 중단 검사가 빠지면**
    이 시나리오는 끝나지 못하고 `finish()` 가 잡는다(줍고 나서 다음 URL 을 기다린다).
    """
    with tempfile.TemporaryDirectory() as tmp:
        proc = start_crawl(tmp, seed)
        if not wait_for_request(port):
            proc.kill()
            proc.communicate()
            unmeasurable("중단할 요청이 서버에 도착하지 않았다")
        sent_at = time.monotonic()
        proc.send_signal(signal.SIGINT)
        out, err = finish(proc, 40, "시나리오 2")
        elapsed = time.monotonic() - sent_at
        saved = saved_rows(tmp)

    assert proc.returncode == 130, (
        "중단 종료 코드가 130 이 아니라 %d 다\n%s"
        % (proc.returncode, err.strip()[-400:]))
    assert elapsed <= 8.0, ("SIGINT 뒤 %.1f초 걸렸다 — 응답 %g초 뒤 바로 접혀야 한다"
                            % (elapsed, SLOW_SECONDS))
    assert saved == 1, "떠 있던 응답을 %d행으로 남겼다 — 받아 둔 페이지를 버렸다" % saved
    assert "수집 1 페이지" in out, "중단이어도 주운 페이지 수를 찍는다: %r" % out.strip()
    return elapsed, saved


def scenario_4_second_ctrl_c(seed, port):
    """두 번째 Ctrl-C 는 기본 동작으로 즉사한다.

    첫 신호만으로도 안 끝나는 상황(안 답하는 서버 — 소켓 타임아웃 10초가 남아 있다)에서
    사용자가 프로세스를 못 죽이게 되면 **지금보다 나쁘다**. 5초 상한이 그 10초와
    구별하는 잣대다.
    """
    with tempfile.TemporaryDirectory() as tmp:
        proc = start_crawl(tmp, seed)
        if not wait_for_request(port):
            proc.kill()
            proc.communicate()
            unmeasurable("중단할 요청이 서버에 도착하지 않았다")
        proc.send_signal(signal.SIGINT)
        time.sleep(0.2)  # 핸들러가 자기를 SIG_DFL 로 내릴 틈. 첫 신호는 이미 도착했다
        second_at = time.monotonic()
        proc.send_signal(signal.SIGINT)
        out, err = finish(proc, 30, "시나리오 4")
        elapsed = time.monotonic() - second_at

    assert proc.returncode == -signal.SIGINT, (
        "두 번째 Ctrl-C 인데 rc %d 다 — 기본 동작으로 안 돌아갔다" % proc.returncode)
    assert elapsed <= 5.0, ("두 번째 Ctrl-C 뒤 %.1f초 걸렸다 — 첫 신호가 기다리던 "
                            "소켓 타임아웃을 그대로 기다렸다" % elapsed)
    return elapsed


def main():
    global BROKEN
    BROKEN = "--control" in sys.argv[1:]

    servers = []
    for mode in ("fast", "hang", "slow"):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), make_handler(mode))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    fast_port, hang_port, slow_port = [s.server_address[1] for s in servers]
    seed = lambda port: "http://127.0.0.1:%d/" % port

    try:
        s0 = scenario_0_control(seed(fast_port))
        del REQUEST_LOG[:]  # 시나리오끼리 요청이 섞이면 간격도 건수도 못 잰다
        s1_elapsed, s1_hits = scenario_1_and_3_hang(seed(hang_port), hang_port)
        del REQUEST_LOG[:]
        s2_elapsed, s2_saved = scenario_2_inflight_is_kept(seed(slow_port), slow_port)
        del REQUEST_LOG[:]
        s4_elapsed = scenario_4_second_ctrl_c(seed(hang_port), hang_port)
    finally:
        for server in servers:
            server.shutdown()

    print("e2e 통과 — 서버 3개 · Crawl-delay %d초" % CRAWL_DELAY)
    print("  [0] 대조군(신호 없음): %d페이지 rc 0, %.1fs — 아래 넷의 잣대" % s0)
    print("  [1] 안 답하는 서버: SIGINT 뒤 %.1fs 에 rc 130 · 페이지 요청 %d건 · DB 0행"
          " (오늘 신호 없이 69.57s)" % (s1_elapsed, s1_hits))
    print("  [3] 예절: 그 요청들의 간격이 Crawl-delay %d초 미만이 아니다" % CRAWL_DELAY)
    print("  [2] 느린 서버: SIGINT 뒤 %.1fs · 떠 있던 응답 %d행을 줍는다"
          % (s2_elapsed, s2_saved))
    print("  [4] 두 번째 Ctrl-C: %.2fs 만에 rc -%d (기본 동작 즉사)"
          % (s4_elapsed, signal.SIGINT))


if __name__ == "__main__":
    main()
