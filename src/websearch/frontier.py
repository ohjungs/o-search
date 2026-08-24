"""방문 예정 URL 큐. 도메인 라운드로빈 + 같은 도메인 1초 간격을 큐 수준에서 보장."""
import collections
import time
import urllib.parse

DOMAIN_INTERVAL = 1.0  # 초 — concept.md 크롤 윤리, 내리지 않는다
# robots 가 이보다 긴 간격을 요구하면 지킬 수 없다고 보고 그 도메인을 버린다.
# 깎아서 계속 때리는 것은 윤리 위반이고, 곧이곧대로 자면 무인 크롤이 밤을 통째로 쓴다.
MAX_DELAY = 30.0


class Frontier:
    def __init__(self, now=time.monotonic):
        self._now = now
        self._queues = collections.OrderedDict()  # domain -> deque[url]
        self._seen = set()
        self._last_fetch = {}  # domain -> 시각
        self._delays = {}      # domain -> 초. robots 가 요구한 간격(하한 적용 후)
        self._dropped = set()  # 간격을 지킬 수 없어 버린 도메인

    def set_delay(self, domain, seconds):
        """robots 가 요청한 간격을 반영한다. seconds 가 None 이면 기본 간격 그대로.

        간격은 늘어나는 방향으로만 움직인다 — DOMAIN_INTERVAL 아래로는 내려가지 않는다.
        MAX_DELAY 를 넘으면 그 도메인을 통째로 버린다(큐를 비우고 이후 add 도 받지 않는다).
        """
        if seconds is not None and seconds > MAX_DELAY:
            self._dropped.add(domain)
            self._queues.pop(domain, None)
            return
        self._delays[domain] = max(DOMAIN_INTERVAL, seconds or 0)

    def _interval(self, domain):
        return self._delays.get(domain, DOMAIN_INTERVAL)

    def add(self, urls):
        for url in urls:
            if url in self._seen:
                continue
            domain = urllib.parse.urlsplit(url).netloc
            if domain in self._dropped:
                continue
            self._seen.add(url)
            self._queues.setdefault(domain, collections.deque()).append(url)

    def next(self):
        """지금 요청해도 되는 URL 하나. 전 도메인이 쿨다운이면 None."""
        for domain in list(self._queues):
            last = self._last_fetch.get(domain)
            if last is not None and self._now() - last < self._interval(domain):
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
            waits.append(0.0 if last is None
                         else max(0.0, self._interval(domain) - (self._now() - last)))
        return min(waits)
