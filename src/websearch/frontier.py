"""방문 예정 URL 큐. 도메인 라운드로빈 + 같은 도메인 1초 간격을 큐 수준에서 보장."""
import collections
import time
import urllib.parse

DOMAIN_INTERVAL = 1.0  # 초 — concept.md 크롤 윤리, 내리지 않는다


class Frontier:
    def __init__(self, now=time.monotonic):
        self._now = now
        self._queues = collections.OrderedDict()  # domain -> deque[url]
        self._seen = set()
        self._last_fetch = {}  # domain -> 시각

    def add(self, urls):
        for url in urls:
            if url in self._seen:
                continue
            self._seen.add(url)
            domain = urllib.parse.urlsplit(url).netloc
            self._queues.setdefault(domain, collections.deque()).append(url)

    def next(self):
        """지금 요청해도 되는 URL 하나. 전 도메인이 쿨다운이면 None."""
        for domain in list(self._queues):
            last = self._last_fetch.get(domain)
            if last is not None and self._now() - last < DOMAIN_INTERVAL:
                continue
            queue = self._queues[domain]
            url = queue.popleft()
            if not queue:
                del self._queues[domain]
            else:
                self._queues.move_to_end(domain)  # 라운드로빈
            self._last_fetch[domain] = self._now()
            return url
        return None

    def empty(self):
        return not self._queues

    def seconds_until_ready(self):
        """다음 URL 이 나올 때까지 기다릴 시간. 빈 큐면 0."""
        if self.empty():
            return 0.0
        waits = []
        for domain in self._queues:
            last = self._last_fetch.get(domain)
            waits.append(0.0 if last is None else max(0.0, DOMAIN_INTERVAL - (self._now() - last)))
        return min(waits)
