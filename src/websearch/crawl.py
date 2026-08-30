"""크롤 루프: robots 확인 → fetch → 저장 → 링크를 프런티어에. CLI 엔트리 포함.

**네트워크만 동시에 돈다.** `Store`·`Frontier`·카운터는 메인 스레드가 독점하므로
락도 스레드별 SQLite 커넥션도 없다 (docs/design_crawl-throughput.md).
"""
import concurrent.futures
import signal
import sys
import threading
import time

from websearch import fetcher, flags, links, urls
from websearch.frontier import Frontier, DOMAIN_INTERVAL, MAX_DELAY
from websearch.robots import RobotsCache
from websearch.store import Store


WORKERS = 8  # 동시에 띄우는 요청 수. **보정 손잡이지 상수가 아니다** — CLI 의 --workers

# 시드가 가질 수 있는 스킴. `links.py` 가 발견된 링크에 거는 조건과 **같은 것**이고,
# 여기 있는 이유는 시드가 거기를 안 지나가기 때문이다. 한쪽을 늘리면 다른 쪽도 본다.
FETCHABLE_SCHEMES = ("http", "https")


class NoUsableSeedsError(ValueError):
    """시드가 하나도 프런티어에 못 들어갔다 — 크롤이 시작될 수조차 없다.

    "0페이지 수집" 과 다르다. 저쪽은 크롤이 돌았고 결과가 없는 것이라 rc 0 이고
    (robots 가 정당하게 막은 사이트가 그 자리다), 이쪽은 요청이 한 건도 나갈 수
    없는 것이라 사용자 입력 오류(rc 2)다. 이 구분을 없애면 예의를 지킨 크롤이
    오작동으로 보고된다.
    """


class _Interrupted(Exception):
    """중단 신호가 발신 훅을 접었다. **`_fetch_one` 만 던지고 `_fetch_one` 만 잡는다** —

    `fetcher` 는 훅을 `try` 밖에서 부르므로(`fetcher.py:36-37`) 이 예외는 그대로 나온다.
    밖으로 흘리면 `_store_result` 의 `except` 가 **모르는 실패**로 읽어 in-flight 개수만큼
    `요청이 예외로 끝났다` 를 찍는다 — 일부러 만든 상태를 오류로 보고하는 것이다
    (docs/design_graceful-interrupt.md 계약 5).
    """


def _fetch_one(url, robots, now, floor, sleep=time.sleep, stop=None):
    """워커 스레드가 하는 일 전부. **`Store`·`Frontier`·카운터를 만지지 않는다** (설계 계약 4).

    `robots` 는 예외로 워커들이 **공유하는** `RobotsCache` 다. `_parser()` 가
    check-then-set 이라 그 자체로는 스레드 안전하지 않지만, 계약 3(도메인당 in-flight 1개)
    덕에 같은 base 를 두 워커가 동시에 로드하지 않는다. **계약 3을 풀면 여기가 깨진다.**

    돌려주는 것: `(allowed, requested_delay, sent_at, FetchResult|None)`.
    순서는 순차 루프와 같다 — robots 확인 → 간격 조회 → fetch. 사이트가 보는
    요청 순서가 변하지 않는다.

    **재시도도 요청이다.** `fetcher` 는 간격을 모르므로 여기서 넘기는 훅이 재운다
    (docs/design_crawl-politeness.md 2절). 그래서 `sent_at` 은 **마지막** 발신 시각이다 —
    첫 발신으로 시계를 걸면 마지막 재시도 직후 0초 만에 다음 요청이 나간다.

    `floor` 는 **프런티어가 그 서버에 대해 아는 간격**이다. `robots.delay()` 만
    보면 스킴별 robots.txt 만 보는 셈이라, `http` 가 5초를 선언한 서버의 `https`
    재시도가 1초로 나간다(실측). 프런티어는 서버 단위(`urls.domain_key`)로 모으므로
    그쪽이 더 크다.
    **메인 스레드가 제출 시점에 읽어 넘긴다** — 워커는 `Frontier` 를 안 만진다(계약 4).
    올리기만 한다: `floor` 는 이미 `DOMAIN_INTERVAL` 이상이다.
    """
    # 진입 검사 — **바로 뒤가 `robots.txt` 왕복이다**(`robots.allowed`). 재시도만 접으면
    # 이 왕복은 안 막힌다. 신호 뒤에 새로 여는 소켓은 0개다 (설계 계약 4)
    if stop is not None and stop.is_set():
        return True, None, None, None
    if not robots.allowed(url):
        return False, None, None, None
    requested = robots.delay(url)
    # `DOMAIN_INTERVAL` 을 여기 남겨 둔다. `floor` 는 오늘 언제나 그 이상이지만,
    # **하한은 컨셉의 절대 조건**이라 그 보장이 호출부 한 곳에만 있으면 안 된다 —
    # 더 작은 값을 넘기는 호출이 하나 생기는 순간 조용히 사라지는 종류의 것이다
    interval = max(DOMAIN_INTERVAL, floor, requested or 0)
    # `stop` 이 None 이면 주입된 `sleep` 만 불린다 (graceful-interrupt 계약 2)
    wait = sleep if stop is None else stop.wait
    sends = []  # 이 URL 로 실제로 나간 시도들의 시각

    def before_send():
        """발신 직전. 재시도면 마지막 발신에서 간격이 찰 때까지 잔다.

        워커 스레드를 최대 `retries × interval` 만큼 붙든다 — 컨셉 우선순위상
        크롤 윤리가 성능 위라 받아들인 값이다(설계 2-3절). 타임아웃 실패는 이미
        10초가 벌어져 있어 남은 시간이 음수가 되고 잠들지 않는다.

        **중단이면 안 보내고 접는다.** 잠만 깨우고 그대로 보내면 `Crawl-delay: 30` 을
        선언한 서버에 10초 간격으로 3발이 나간다 — 지금 이 잠이 붙들고 있는 것이 바로
        그 예절이라 깨우기와 취소는 나눌 수 없다 (graceful-interrupt 계획 2절 3번).
        """
        if stop is not None and stop.is_set():
            raise _Interrupted
        if sends:
            remaining = interval - (now() - sends[-1])
            # `time.sleep` 은 None(거짓)을, `Event.wait` 는 신호가 서면 True 를 돌려준다 —
            # 한 표현이 "간격이 찼다" 와 "중단으로 깼다" 를 다 덮는다 (graceful-interrupt 계약 3)
            if remaining > 0 and wait(remaining):
                raise _Interrupted
        sends.append(now())  # 간격 시계는 팝이 아니라 **발신**에서 시작한다 (계약 9)

    # 간격을 지킬 수 없는 도메인(상한 초과)에는 다시 보내지 않는다 — 깎아서 때리는 것보다
    # 안 보내는 것이 맞고, 요구대로 자면 워커가 하루를 붙든다 (설계 2-4절)
    try:
        result = fetcher.fetch(url, before_send=before_send,
                               retries=fetcher.RETRIES if interval <= MAX_DELAY else 0)
    except _Interrupted:
        # 중단된 시도는 **결과가 아니다.** `FetchResult(0, None, None)` 로 돌려주면
        # 안 받은 페이지가 status 0 으로 DB 에 박혀 다음 실행이 그 URL 을 영영
        # 건너뛴다 — 중단이 프런티어를 오염시키면 안 된다 (설계 계약 5)
        result = None
    # 훅이 한 번도 안 불렸으면 **요청이 나가지 않았다**(`Request()` 생성 실패).
    # 그때 시각을 지어내면 나가지도 않은 요청으로 도메인 쿨다운을 태운다
    # (cooldown-burn 계약 1). `mark_sent` 는 None 을 받으면 시계를 안 건다
    return True, requested, sends[-1] if sends else None, result


def crawl(seeds, max_pages, db_path="data/crawl.db", robots_cache=None,
          now=time.monotonic, workers=WORKERS, deadline=None, sleep=time.sleep,
          stop=None):
    """수집에 성공(2xx + HTML)한 페이지 수를 돌려준다. robots_cache·now·sleep 은 테스트 주입 지점.

    `workers=1` 이면 요청이 하나씩 떠서 순차 루프와 같은 순서로 돈다 — 되돌리기 수단이다.

    `deadline` 은 **총 크롤 시간 예산(상대 초)** 이다. `None` 이면 오늘과 같은 경로만
    돈다 — 기본값이 곧 꺼진 플래그다(docs/design_deadline.md 6절).
    예산이 하는 일은 **"덜 보낸다"** 뿐이고 "빨리 보낸다" 는 아니다: 간격은 안 깎는다.
    **메인 스레드만 예산을 본다** — 이미 떠 있는 요청은 그대로 끝까지 간다.
    그래서 실제 종료는 예산 + 떠 있는 요청 하나의 최악만큼 늦는다 — **실측 69.57초**다
    (설계 5절 2번이 적어 둔 "90초" 는 오답이다. 분해는 아래 Ctrl-C 문단).
    `stop` 은 **중단 신호**다 — `is_set()`·`wait(t)` 를 가진 것(`threading.Event`).
    `None` 이면 오늘과 같은 경로만 돈다 — `deadline` 과 같은 형태로 기본값이 곧 꺼진
    플래그다(docs/design_graceful-interrupt.md). 신호가 서면 **새 요청을 제출하지 않고**
    예산 소진과 같은 가지로 빠진다 — 떠 있는 결과는 줍는다.
    잠드는 자리도 `stop.wait` 로 간다: 신호가 잠을 깨워야 하기 때문이다.

    그 요청들의 **결과는 줍는다** — 설계 4절이 줍는지 버리는지를 비워 뒀고
    2026-08-29 에 줍는 쪽으로 정했다. executor 가 `with` 를 나갈 때 어차피 그것들을
    기다리므로 **추가 대기는 0**이고, 버리면 이미 받은 응답을 버린 채 다음 실행이
    같은 URL 을 또 때린다 — 크롤 윤리로도 손해다. 줍는 것은 결과뿐이라
    **새 요청은 나가지 않는다**(`_store_result` 는 네트워크를 하지 않는다).

    **Ctrl-C 는 `stop` 을 줬을 때만 빠르다.** `ThreadPoolExecutor` 는 나갈 때 떠 있는
    요청을 기다린다 — `stop` 없이는 재시도 잠까지 다 치르느라 **실측 69.57초**가 걸렸다
    (탐침이 적어 뒀던 "최악 90초" 는 오답이다: 간격 대기가 이미 흘러간 타임아웃을 빼므로
    발신 간격은 `interval + 10` 이 아니라 `interval` 이다. 분해는 계획서 2절).
    `stop` 을 주면 재시도가 접혀 **남는 것은 소켓 읽기 1회(`fetcher` 타임아웃 10초)뿐**이다.
    재시도 대기는 예의를 위해 치르기로 한 값이다(docs/design_crawl-politeness.md 2-3절).
    저장은 upsert 마다 커밋이라 **유실은 없다**. `cancel_futures` 로는 안 줄어든다 —
    취소되는 건 대기 중인 작업뿐인데 여기선 제출한 것이 곧 실행 중인 것이다.
    """
    store = Store(db_path)
    robots = robots_cache if robots_cache is not None else RobotsCache()
    frontier = Frontier(now=now)
    ascii_seeds = []
    for seed in seeds:  # 시드는 CLI 가 준 것 — 버릴 때는 왜 버렸는지 알린다
        normalized = urls.normalize(seed)
        if normalized is None:
            print("%s: URL 로 읽을 수 없는 시드 — 건너뛴다" % seed, file=sys.stderr)
        elif urls.scheme_of(normalized) not in FETCHABLE_SCHEMES:
            # **새 계약이 아니라 이미 있는 계약의 구멍이다.** `links.py` 는 발견된
            # 링크를 `http(s)` 로 이미 거른다 — 시드만 그 가드를 안 지나갔다.
            # 그래서 `example.com` 이 fetcher 까지 내려가 robots 를 받으려다
            # `unknown url type: ':///robots.txt'` 로 죽었다(실측).
            print("%s: http(s) 가 아니라 가져올 수 없는 시드 — 건너뛴다" % seed,
                  file=sys.stderr)
        else:
            ascii_seeds.append(normalized)
    if not ascii_seeds:
        # 한 건도 못 넣었으면 크롤은 **시작될 수조차 없다.** `수집 0 페이지` rc 0 은
        # 크롤이 돌고도 아무것도 못 찾은 것과 구별되지 않는다 — 26(`--max 0`)·21 과
        # 같은 값이다. 반대쪽 경계는 건드리지 않는다: 시드가 하나라도 살아남았으면
        # 0페이지는 그대로 rc 0 이다(robots 가 정당하게 막은 사이트가 그 자리다).
        #
        # **시드가 애초에 0건인 경우도 여기다.** `crawl --max 1` 은 플래그만 있고
        # 시드가 없는데 `len(argv) < 2` 를 통과해(플래그가 인자를 채운다) 조용히
        # `수집 0 페이지` rc 0 으로 끝났다(실측). "다 거절당해서 0건" 과 "처음부터
        # 0건" 은 크롤이 못 도는 이유로는 같은 것이라 한 자리에서 막는다.
        raise NoUsableSeedsError(
            "가져올 수 있는 시드가 하나도 없다 — http:// 나 https:// 로 시작하는 "
            "주소를 준다")
    frontier.add(ascii_seeds)
    saved = 0
    started = now()
    inflight = {}  # Future -> (url, domain). **떠 있는 도메인은 다시 팝하지 않는다**(계약 3)
    # 중단 신호가 있으면 **잠도 그쪽으로 잔다** — 이 자리(아래 `wait_fn(...)`)는 깨워 줄
    # 워커가 없어 `futures.wait` 처럼 저절로 깨지 않는 유일한 대기다(설계서 축3).
    # `stop` 이 None 이면 주입된 `sleep` 만 불린다 (설계 계약 2)
    wait_fn = sleep if stop is None else stop.wait
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        while saved < max_pages:
            # 남은 예산. None 이면 예산이 없다는 뜻이라 아래 두 자리가 오늘 그대로 흐른다
            left = None if deadline is None else deadline - (now() - started)
            # 중단은 **예산 소진과 같은 종료다** — 새 요청을 안 내고, 떠 있는 결과는 줍고,
            # 사유를 남기고 끝난다. 새 종료 경로를 만들지 않는다 (설계 계약 6)
            interrupted = stop is not None and stop.is_set()
            if interrupted or (left is not None and left <= 0):
                # 떠 있는 요청은 **결과만 줍고** 끝낸다. `with` 를 나갈 때 executor 가
                # 어차피 이것들을 기다리므로 추가 대기는 0이다 — 안 주우면 이미 보낸
                # 요청의 응답을 버리고 다음 실행에서 같은 URL 을 또 때리게 된다
                for future in list(inflight):
                    url, domain = inflight.pop(future)
                    saved += _store_result(future, url, domain, store, frontier,
                                           now, robots)
                # 조용히 적게 수집한 것과 "예산대로/중단으로 끝났다" 는 구별돼야 한다
                print("중단 — %d페이지에서 멈춘다" % saved if interrupted else
                      "예산 %g초 소진 — %d페이지에서 멈춘다" % (deadline, saved),
                      file=sys.stderr)
                break
            busy = {domain for _, domain in inflight.values()}
            while len(inflight) < workers and saved + len(inflight) < max_pages:
                url = frontier.next(exclude=busy)
                if url is None:
                    break
                if store.has(url):
                    continue
                domain = urls.domain_key(url)
                busy.add(domain)
                inflight[pool.submit(_fetch_one, url, robots, now,
                                     frontier.interval(domain), sleep,
                                     stop)] = (url, domain)
            if not inflight:
                if frontier.empty():
                    break
                # 예산이 지난 뒤 최대 `MAX_DELAY` 만큼 더 자는 것을 막는다. **깎는 게
                # 아니라 자르는 것이다** — 깨어나서 위의 소진 검사로 끝낼 뿐,
                # 짧아진 간격으로 요청이 나가지는 않는다
                wait = frontier.seconds_until_ready()
                # 중단이면 여기서 깬다 — 반환값은 안 본다. 깨어나서 위 검사로 끝낼 뿐이다
                wait_fn(wait if left is None else min(wait, left))
                continue
            # 던질 것이 없으면 결과를 기다린다 — 0초는 "떠 있는 도메인뿐" 이라는 뜻이라
            # 타임아웃 대신 완료를 기다린다 (계약 8)
            wait_for = frontier.seconds_until_ready(exclude=busy)
            done, _ = concurrent.futures.wait(
                inflight, timeout=wait_for or None,
                return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                url, domain = inflight.pop(future)
                saved += _store_result(future, url, domain, store, frontier, now,
                                       robots)
    return saved


def _apply_delay(frontier, domain, requested):
    """robots 가 요청한 간격을 프런티어에 건다. **성공 가지와 예외 가지가 함께 지나는 자리다.**

    `requested` 가 None 이면 프런티어의 하한(`DOMAIN_INTERVAL`)이 답이다 —
    `robots.known_delay` 의 주석 참조. 상한을 넘으면 그 도메인을 통째로 버린다.
    """
    if not frontier.set_delay(domain, requested):
        # 조용히 1페이지만 받고 끝나면 사용자는 이유를 알 방법이 없다
        print("%s: %g초 간격을 요구해 상한 %g초를 넘는다 — 이 도메인은 더 가지 않는다"
              % (domain, requested, MAX_DELAY), file=sys.stderr)


def _store_result(future, url, domain, store, frontier, now, robots):
    """워커 결과 하나를 반영한다. 수집에 성공했으면 1, 아니면 0.

    **간격 시계를 거는 유일한 자리다** (docs/design_cooldown-burn.md 계약 2·3).
    **간격 값을 거는 자리도 여기 하나다** — 성공이든 예외든 `_apply_delay()` 를 지난다
    (docs/design_crawl-politeness.md 1-5절).
    robots 가 막았으면 페이지 요청이 안 나갔으니 걸지 않는다 — 그 도메인을 재우면
    요청도 없이 쿨다운을 태우는 것이다.

    **"시계를 거는 유일한 자리" 지 "요청이 나가는 유일한 자리" 가 아니다.** 이 계약
    밖으로 나가는 요청이 아직 하나 있다: `robots.txt` 왕복(digest [4] 로 간격 측정에서 제외).
    `fetcher` 의 재시도도 밖으로 나가지만 이제는 `_fetch_one` 의 발신 훅이 재우고,
    `sent_at` 이 **마지막** 발신이라 프런티어가 보는 시각이 실제와 어긋나지 않는다.
    """
    try:
        allowed, requested, sent_at, result = future.result()
    except Exception as err:  # 워커 하나가 죽어도 크롤은 안 죽는다 (계약 6)
        # **요청이 나갔는지 알 수 없다** — 예외는 fetch 전에도 후에도 날 수 있다.
        # 보수적으로 지금 시각으로 건다. 늦게 잡는 것은 안전하고 이르게 당기는 것만
        # 위반이며, `mark_sent` 가 `max` 로 늦은 쪽으로만 움직인다.
        # 여기를 빼면 다음 요청이 즉시 나간다 (설계 탐침 실측 0.310s).
        frontier.mark_sent(domain, now())
        # **간격 값도 여기서 건다.** 반환값이 안 왔다고 `Crawl-delay` 를 잊으면 다음 요청이
        # 기본 1초로 나간다 — robots 위반이다(실측: 5초 선언 도메인이 1.0초로 떨어졌다).
        # 캐시에 이미 있는 값만 본다 — 메인 스레드는 네트워크를 안 한다(동시화 계약 4).
        _apply_delay(frontier, domain, robots.known_delay(url))
        print("%s: 요청이 예외로 끝났다 — %r" % (url, err), file=sys.stderr)
        return 0
    if not allowed:
        return 0
    frontier.mark_sent(domain, sent_at)
    _apply_delay(frontier, domain, requested)
    # 중단으로 접힌 시도 — **시계와 간격은 걸고 지나간 뒤** 아무것도 안 박는다.
    # 이미 나간 발신이 있으면 그 쿨다운은 유효하고, 안 받은 페이지를 status 0 으로
    # 박으면 다음 실행이 그 URL 을 영영 건너뛴다 (graceful-interrupt 계약 5)
    if result is None:
        return 0
    # 리다이렉트면 최종 URL 이 정본. 못 바꾸면 요청한 url(프런티어를 거쳤으니 ASCII)로 저장한다
    page_url = urls.normalize(result.url or url) or url
    if page_url != url and store.has(page_url):
        return 0
    store.upsert(page_url, result.html, result.status)
    if result.html is not None and 200 <= result.status < 300:
        frontier.add(links.extract(page_url, result.html))
        return 1
    return 0


def main(argv):
    if len(argv) < 2:
        print("usage: python3 -m websearch.crawl <seed-url> [seed-url ...] "
              "[--max N] [--workers N] [--deadline N]", file=sys.stderr)
        return 2
    args = list(argv[1:])
    max_pages = flags.number_flag(args, "--max", 100)
    # 0 은 요청을 한 건도 안 보내고 `수집 0 페이지` rc 0 을 냈다 — 크롤이 아무것도
    # 못 찾은 것과 구별되지 않는 성공이다. `--workers`·`--deadline` 과 같은 하한을 쓴다
    if max_pages is None or max_pages < 1:
        print("--max 는 1 이상의 숫자 하나를 받는다", file=sys.stderr)
        return 2
    workers = flags.number_flag(args, "--workers", WORKERS)
    if workers is None or workers < 1:
        print("--workers 는 1 이상의 숫자 하나를 받는다", file=sys.stderr)
        return 2
    # `--deadline` 은 없는 것이 정상값(`None`)이라 `flags.number_flag` 의 오류값과 겹친다.
    # **형태를 여기서 다시 세지 않는다** — `a.startswith("--deadline=")` 를 여기 두면
    # 파서와 두 벌이 되고, 형태가 하나 늘 때 이쪽만 조용히 뒤처진다. 센티널로 가른다.
    missing = object()
    deadline = flags.number_flag(args, "--deadline", missing)
    if deadline is missing:
        deadline = None
    elif deadline is None or deadline < 1:
        print("--deadline 은 1 이상의 숫자 하나를 받는다", file=sys.stderr)
        return 2
    # **남은 `-` 는 시드가 아니다.** 파서가 아는 플래그를 뽑고 남은 것은 시드인데,
    # 오타(`--maxx`)·하이픈 하나(`-max`)·중복(`--max 3 --max 5`)은 시드로 새어
    # 크롤이 **기본값으로 조용히 돌았다**(rc 0). `indexer`·`serve` 는 `len(args) != 1`
    # 이 이미 거른다 — 시드 개수가 가변인 여기만 셀 수가 없어 구멍이었다
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        print("모르는 인자: %s — 시드 URL 로 읽지 않는다" % " ".join(unknown),
              file=sys.stderr)
        return 2
    # Ctrl-C 를 크롤이 보는 신호로 바꾼다 (docs/design_graceful-interrupt.md 계약 7)
    stop = threading.Event()

    def interrupt(signum, frame):
        # **자기를 먼저 내리고 그다음 세운다** — 두 번째 Ctrl-C 는 기본 동작으로
        # 즉사해야 한다. 순서가 반대면 사용자가 탈출구를 잃는 창이 생긴다
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        stop.set()

    # `signal.signal` 의 반환값이 곧 옛 핸들러다 — 안 되돌리면 한 프로세스에서
    # 여러 번 도는 호출자(테스트·래퍼)가 오염된다. 중단 갈래는 위에서 SIG_DFL 로
    # 내려간 채라 특히 그렇다
    previous = signal.signal(signal.SIGINT, interrupt)
    try:
        n = crawl(args, max_pages, workers=workers, deadline=deadline, stop=stop)
    except NoUsableSeedsError as exc:
        # 판정은 `crawl()` 이 한다 — 여기서 스킴을 다시 보면 `-` 를 거절하는 위 가드와
        # 한 덩어리가 되어 27 의 변이 M4 가 경고한 다른 계약으로 넓어진다
        print(exc, file=sys.stderr)
        return 2
    finally:
        signal.signal(signal.SIGINT, previous)
    print("수집 %d 페이지" % n)
    # 중단은 **오늘 관측값과 같은 130** 이다 — 0 으로 내면 `crawl && indexer` 가
    # 중단 뒤에도 다음 단계를 돈다. 주운 페이지 수는 중단이어도 찍는다
    return 130 if stop.is_set() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
