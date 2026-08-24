"""크롤 루프: robots 확인 → fetch → 저장 → 링크를 프런티어에. CLI 엔트리 포함."""
import sys
import time

from websearch import fetcher, links
from websearch.frontier import Frontier
from websearch.robots import RobotsCache
from websearch.store import Store


def crawl(seeds, max_pages, db_path="data/crawl.db", robots_cache=None, now=time.monotonic):
    """수집에 성공(2xx + HTML)한 페이지 수를 돌려준다. robots_cache·now 는 테스트 주입 지점."""
    store = Store(db_path)
    robots = robots_cache if robots_cache is not None else RobotsCache()
    frontier = Frontier(now=now)
    frontier.add(seeds)
    saved = 0
    while saved < max_pages and not frontier.empty():
        url = frontier.next()
        if url is None:
            time.sleep(frontier.seconds_until_ready())
            continue
        if store.has(url) or not robots.allowed(url):
            continue
        result = fetcher.fetch(url)
        page_url = result.url or url  # 리다이렉트면 최종 URL 이 정본
        if page_url != url and store.has(page_url):
            continue
        store.upsert(page_url, result.html, result.status)
        if result.html is not None and 200 <= result.status < 300:
            saved += 1
            frontier.add(links.extract(page_url, result.html))
    return saved


def main(argv):
    if len(argv) < 2:
        print("usage: python3 -m websearch.crawl <seed-url> [seed-url ...] [--max N]", file=sys.stderr)
        return 2
    args = list(argv[1:])
    max_pages = 100
    if "--max" in args:
        i = args.index("--max")
        try:
            max_pages = int(args[i + 1])
        except (IndexError, ValueError):
            print("--max 는 숫자 하나를 받는다", file=sys.stderr)
            return 2
        del args[i:i + 2]
    n = crawl(args, max_pages)
    print("수집 %d 페이지" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
