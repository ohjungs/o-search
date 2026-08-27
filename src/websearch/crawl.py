"""크롤 루프: robots 확인 → fetch → 저장 → 링크를 프런티어에. CLI 엔트리 포함.

**네트워크만 동시에 돈다.** `Store`·`Frontier`·카운터는 메인 스레드가 독점하므로
락도 스레드별 SQLite 커넥션도 없다 (docs/design_crawl-throughput.md).
"""
import concurrent.futures
import sys
import time
import urllib.parse

from websearch import fetcher, links, urls
from websearch.frontier import Frontier, MAX_DELAY
from websearch.robots import RobotsCache
from websearch.store import Store


WORKERS = 8  # 동시에 띄우는 요청 수. **보정 손잡이지 상수가 아니다** — CLI 의 --workers


def _fetch_one(url, robots, now):
    """워커 스레드가 하는 일 전부. **`Store`·`Frontier`·카운터를 만지지 않는다** (설계 계약 4).

    `robots` 는 예외로 워커들이 **공유하는** `RobotsCache` 다. `_parser()` 가
    check-then-set 이라 그 자체로는 스레드 안전하지 않지만, 계약 3(도메인당 in-flight 1개)
    덕에 같은 base 를 두 워커가 동시에 로드하지 않는다. **계약 3을 풀면 여기가 깨진다.**

    돌려주는 것: `(allowed, requested_delay, sent_at, FetchResult|None)`.
    순서는 순차 루프와 같다 — robots 확인 → 간격 조회 → fetch. 사이트가 보는
    요청 순서가 변하지 않는다.
    """
    if not robots.allowed(url):
        return False, None, None, None
    requested = robots.delay(url)
    sent_at = now()  # 간격 시계는 팝이 아니라 **발신**에서 시작한다 (계약 9)
    return True, requested, sent_at, fetcher.fetch(url)


def crawl(seeds, max_pages, db_path="data/crawl.db", robots_cache=None,
          now=time.monotonic, workers=WORKERS):
    """수집에 성공(2xx + HTML)한 페이지 수를 돌려준다. robots_cache·now 는 테스트 주입 지점.

    `workers=1` 이면 요청이 하나씩 떠서 순차 루프와 같은 순서로 돈다 — 되돌리기 수단이다.

    **Ctrl-C 가 즉시 안 먹는다.** `ThreadPoolExecutor` 는 나갈 때 떠 있는 요청을 기다려서,
    최악 `fetcher` 타임아웃 10초 × 재시도만큼 늦는다(동시화 전에는 즉시 끊겼다).
    저장은 upsert 마다 커밋이라 **유실은 없다**. `cancel_futures` 로는 안 줄어든다 —
    취소되는 건 대기 중인 작업뿐인데 여기선 제출한 것이 곧 실행 중인 것이다.
    """
    store = Store(db_path)
    robots = robots_cache if robots_cache is not None else RobotsCache()
    frontier = Frontier(now=now)
    ascii_seeds = []
    for seed in seeds:  # 시드는 CLI 가 준 것 — 버릴 때는 왜 버렸는지 알린다
        normalized = urls.to_ascii(seed)
        if normalized is None:
            print("%s: URL 로 읽을 수 없는 시드 — 건너뛴다" % seed, file=sys.stderr)
        else:
            ascii_seeds.append(normalized)
    frontier.add(ascii_seeds)
    saved = 0
    inflight = {}  # Future -> (url, domain). **떠 있는 도메인은 다시 팝하지 않는다**(계약 3)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        while saved < max_pages:
            busy = {domain for _, domain in inflight.values()}
            while len(inflight) < workers and saved + len(inflight) < max_pages:
                url = frontier.next(exclude=busy)
                if url is None:
                    break
                if store.has(url):
                    continue
                domain = urllib.parse.urlsplit(url).netloc
                busy.add(domain)
                inflight[pool.submit(_fetch_one, url, robots, now)] = (url, domain)
            if not inflight:
                if frontier.empty():
                    break
                time.sleep(frontier.seconds_until_ready())
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
    밖으로 나가는 요청이 둘 있다: `robots.txt` 왕복(digest [4] 로 간격 측정에서 제외)과
    `fetcher` 의 재시도(연결 실패 시 3회가 간격 없이 나간다 — 실측 0.4ms 간격).
    후자는 이 계획이 연 것이 아니고 `digest.md ## 판단 필요` 에 올려 뒀다.
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
    # 리다이렉트면 최종 URL 이 정본. 못 바꾸면 요청한 url(프런티어를 거쳤으니 ASCII)로 저장한다
    page_url = urls.to_ascii(result.url or url) or url
    if page_url != url and store.has(page_url):
        return 0
    store.upsert(page_url, result.html, result.status)
    if result.html is not None and 200 <= result.status < 300:
        frontier.add(links.extract(page_url, result.html))
        return 1
    return 0


def _number_flag(args, name, default):
    """`--name N` 을 뽑아 args 에서 지운다. 없으면 default, 숫자 하나가 아니면 None."""
    if name not in args:
        return default
    i = args.index(name)
    try:
        value = int(args[i + 1])
    except (IndexError, ValueError):
        return None
    del args[i:i + 2]
    return value


def main(argv):
    if len(argv) < 2:
        print("usage: python3 -m websearch.crawl <seed-url> [seed-url ...] "
              "[--max N] [--workers N]", file=sys.stderr)
        return 2
    args = list(argv[1:])
    max_pages = _number_flag(args, "--max", 100)
    if max_pages is None:
        print("--max 는 숫자 하나를 받는다", file=sys.stderr)
        return 2
    workers = _number_flag(args, "--workers", WORKERS)
    if workers is None or workers < 1:
        print("--workers 는 1 이상의 숫자 하나를 받는다", file=sys.stderr)
        return 2
    n = crawl(args, max_pages, workers=workers)
    print("수집 %d 페이지" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
