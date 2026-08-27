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
        """robots 가 요청한 간격을 반영한다. 계속 크롤할 도메인이면 True.

        간격은 **늘어나는 방향으로만** 움직인다 — 같은 netloc 이 http/https 로 섞여 들어오면
        한쪽엔 지시가 없어서(None), 낮은 쪽이 이기면 20초를 요구한 사이트를 1초로 때린다.
        DOMAIN_INTERVAL 아래로도 내려가지 않는다.
        MAX_DELAY 를 넘으면 그 도메인을 통째로 버린다(큐를 비우고 이후 add 도 받지 않는다).
        """
        if seconds is not None and seconds > MAX_DELAY:
            self._dropped.add(domain)
            self._delays.pop(domain, None)  # 안 쓰일 값을 남겨두면 읽는 사람이 헷갈린다
            self._queues.pop(domain, None)
            return False
        self._delays[domain] = max(self.interval(domain), seconds or 0)
        return True

    def interval(self, domain):
        """이 도메인에 대해 **아는** 간격. 모르면 하한.

        `set_delay` 가 단조 증가로만 쓰므로 이 값은 내려가지 않는다 —
        읽는 쪽은 "여기까지는 확실히 기다려야 한다" 로 믿어도 된다.
        **단 하나의 예외는 버려진 도메인이다**: 상한을 넘게 요구한 도메인은
        `_delays` 에서도 지워지므로 여기서는 하한으로 읽힌다. 그 도메인은 큐에서
        빠지고 `add` 도 거부되니 요청이 다시 나갈 일이 없어 지금은 관측되지 않지만,
        **이 값을 "언제나 안 내려간다" 로 읽으면 안 된다**(`test_a_dropped_domain_
        reads_as_the_floor_again`). 읽기 전에 그 도메인이 살아 있는지 먼저 본다.
        `robots.delay()` 와 다른 점: 저쪽은 **스킴별** robots.txt 의 값이고
        이쪽은 **netloc 단위**로 모은 값이다. 같은 서버에 스킴이 둘이면
        여기가 더 크다.
        """
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

    def next(self, exclude=()):
        """지금 요청해도 되는 URL 하나. 전 도메인이 쿨다운이면 None.

        **간격 시계를 걸지 않는다 — 읽어서 거르기만 한다.** 팝은 요청이 아니다.
        팝해 놓고 요청을 안 보내는 경로가 실제로 둘 있어(`store.has` 스킵·robots 차단),
        팝이 시계를 걸면 요청도 없이 그 도메인이 쉰다
        (docs/design_cooldown-burn.md 계약 1). 시계는 `mark_sent()` 만 건다.

        `exclude` 는 **지금 요청이 떠 있는 도메인**이다. 경과 시간만으로 재면
        응답이 간격보다 오래 걸릴 때 같은 도메인을 in-flight 인 채로 다시 내준다 —
        순차 루프에서는 불가능했고 동시화가 처음 여는 구멍이다
        (docs/design_crawl-throughput.md 계약 3). **팝과 발신 사이의 창도 이것이 덮는다** —
        `crawl` 이 제출 전에 `busy` 에 넣으므로 그 사이 같은 도메인이 다시 안 나온다.
        """
        for domain in list(self._queues):
            if domain in exclude:
                continue
            last = self._last_fetch.get(domain)
            if last is not None and self._now() - last < self.interval(domain):
                continue
            queue = self._queues[domain]
            url = queue.popleft()
            if not queue:
                del self._queues[domain]
            else:
                self._queues.move_to_end(domain)  # 라운드로빈
            return url
        return None

    def mark_sent(self, domain, at):
        """요청이 **실제로 나간** 시각. 간격 시계를 팝이 아니라 여기서 다시 건다.

        팝과 발신 사이에는 robots.txt 왕복이 끼어들 수 있어, 팝 시각으로 재면
        실제 간격이 `interval - robots왕복` 으로 줄어든다 (digest [4], 실측 0.819초).
        **늦은 쪽으로만 움직인다** — 이르게 당기는 것이 곧 위반이다.
        """
        if at is not None:
            self._last_fetch[domain] = max(self._last_fetch.get(domain, at), at)

    def empty(self):
        return not self._queues

    def seconds_until_ready(self, exclude=()):
        """다음 URL 이 나올 때까지 기다릴 시간. 빈 큐면 0.

        `exclude`(요청이 떠 있는 도메인)는 0초로 읽히므로 빼고 본다 — 안 빼면
        그 0에 가려 정작 쿨다운이 풀리는 도메인을 놓친다.
        """
        if self.empty():
            return 0.0
        waits = []
        for domain in self._queues:
            if domain in exclude:
                continue
            last = self._last_fetch.get(domain)
            waits.append(0.0 if last is None
                         else max(0.0, self.interval(domain) - (self._now() - last)))
        return min(waits) if waits else 0.0
