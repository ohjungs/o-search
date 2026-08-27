import unittest
import urllib.parse

from websearch.frontier import Frontier, DOMAIN_INTERVAL, MAX_DELAY


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def pop(f, now, exclude=()):
    """`next()` 하고 **요청이 나갔다고 알린다.** 크롤 루프가 하는 일이 이것이다.

    간격 시계를 거는 자리는 `mark_sent()` 하나뿐이다 — 팝은 요청이 아니다
    (design_cooldown-burn.md 계약 1·2). 팝만 하고 요청을 안 보내는 경우
    (`store.has` 스킵·robots 차단)를 재는 곳은 `tests/test_crawl.py` 다.
    """
    url = f.next(exclude)
    if url is not None:
        f.mark_sent(urllib.parse.urlsplit(url).netloc, now())
    return url


class TestFrontier(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.f = Frontier(now=self.clock)

    def test_add_and_next(self):
        self.f.add(["http://a.com/1"])
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertIsNone(self.f.next())

    def test_duplicate_urls_enqueued_once(self):
        self.f.add(["http://a.com/1", "http://a.com/1"])
        self.f.add(["http://a.com/1"])
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertIsNone(self.f.next())

    def test_already_seen_not_requeued_after_dequeue(self):
        self.f.add(["http://a.com/1"])
        self.f.next()
        self.f.add(["http://a.com/1"])
        self.assertIsNone(self.f.next())

    def test_same_domain_respects_interval(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.assertEqual(pop(self.f, self.clock), "http://a.com/1")
        self.assertIsNone(self.f.next())  # 1초 안 지남 — 낼 것 없음
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_other_domain_served_while_first_cooling(self):
        self.f.add(["http://a.com/1", "http://a.com/2", "http://b.com/1"])
        self.assertEqual(pop(self.f, self.clock), "http://a.com/1")
        self.assertEqual(pop(self.f, self.clock), "http://b.com/1")  # a 쿨다운 중엔 b
        self.assertIsNone(self.f.next())  # 둘 다 쿨다운 — 라운드로빈이 아니라 간격이 막는다

    def test_wait_time_reported(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        pop(self.f, self.clock)
        self.assertIsNone(self.f.next())
        self.assertAlmostEqual(self.f.seconds_until_ready(), 1.0)
        self.assertFalse(self.f.empty())


class TestPerDomainDelay(unittest.TestCase):
    """robots 의 Crawl-delay 를 반영한 도메인별 간격 (design_crawl-delay.md 계약)."""

    def setUp(self):
        self.clock = FakeClock()
        self.f = Frontier(now=self.clock)

    def test_declared_delay_slows_only_that_domain(self):
        self.f.add(["http://a.com/1", "http://a.com/2", "http://b.com/1", "http://b.com/2"])
        self.assertEqual(pop(self.f, self.clock), "http://a.com/1")
        self.f.set_delay("a.com", 5.0)  # 크롤 루프가 robots 를 읽은 직후 알려준다
        self.assertEqual(pop(self.f, self.clock), "http://b.com/1")
        self.clock.t += 1.5  # b 는 1초면 되고 a 는 아직 멀었다
        self.assertEqual(pop(self.f, self.clock), "http://b.com/2")
        self.assertIsNone(self.f.next())
        self.clock.t += 3.5
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_wait_time_uses_declared_delay(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        pop(self.f, self.clock)
        self.f.set_delay("a.com", 4.0)
        self.assertAlmostEqual(self.f.seconds_until_ready(), 4.0)

    def test_delay_never_goes_below_the_floor(self):
        # 1초는 전제 조건이다 (concept.md) — 사이트가 풀어줄 수 있는 것이 아니다
        self.f.add(["http://a.com/1", "http://a.com/2"])
        pop(self.f, self.clock)
        self.f.set_delay("a.com", 0.1)
        self.clock.t += 0.5  # 요청받은 0.1초는 지났다 — 하한이 없으면 여기서 나온다
        self.assertIsNone(self.f.next())
        self.assertAlmostEqual(self.f.seconds_until_ready(), 0.5)
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_no_directive_keeps_default_interval(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        pop(self.f, self.clock)
        self.f.set_delay("a.com", None)
        self.assertIsNone(self.f.next())  # 아직 1초가 안 지났다
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_unkeepable_delay_drops_the_domain(self):
        # 못 지킬 간격이면 깎아서 계속 때리는 대신 그 도메인을 버린다
        self.f.add(["http://a.com/1", "http://slow.com/1"])
        self.f.set_delay("slow.com", 86400)
        self.f.add(["http://slow.com/2"])  # 나중에 링크로 다시 들어와도 안 받는다
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertTrue(self.f.empty())

    def test_exactly_max_delay_is_kept_not_dropped(self):
        # 경계다. 30 을 버리면 지킬 수 있는 사이트를 못 크롤하고,
        # 30.1 을 받으면 정책이 말뿐이 된다
        self.f.add(["http://ok.com/1", "http://ok.com/2", "http://over.com/1"])
        self.f.set_delay("ok.com", 30.0)
        self.f.set_delay("over.com", 30.1)
        self.assertEqual(pop(self.f, self.clock), "http://ok.com/1")
        self.assertIsNone(self.f.next())          # over.com 은 버려졌다
        self.clock.t += 30.0
        self.assertEqual(self.f.next(), "http://ok.com/2")

    def test_interval_never_shrinks(self):
        # 같은 netloc 이 http/https 로 섞여 들어오면 한쪽은 지시가 없다.
        # 낮은 쪽이 이기면 20초를 요구한 사이트를 1초로 때린다
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.f.set_delay("a.com", 20.0)
        self.f.set_delay("a.com", None)
        pop(self.f, self.clock)
        self.assertAlmostEqual(self.f.seconds_until_ready(), 20.0)

    def test_drop_reported_to_caller(self):
        self.assertTrue(self.f.set_delay("ok.com", 10.0))
        self.assertFalse(self.f.set_delay("slow.com", 90.0))


class TestConcurrentPops(unittest.TestCase):
    """동시 fetch 계약 — docs/design_crawl-throughput.md 계약 2·3·9."""

    def test_next_skips_excluded_domain(self):
        f = Frontier(now=lambda: 1000.0)
        f.add(["http://a.test/1", "http://b.test/1"])
        self.assertEqual(f.next(exclude={"a.test"}), "http://b.test/1")
        self.assertIsNone(f.next(exclude={"a.test", "b.test"}))

    def test_next_does_not_start_the_clock(self):
        # 팝은 요청이 아니다. 팝해 놓고 요청을 안 보내는 경로가 실제로 둘 있고
        # (`store.has` 스킵·robots 차단), 팝이 시계를 걸면 **요청도 없이** 그 도메인이
        # 쉰다 (design_cooldown-burn.md). 시계를 거는 자리는 `mark_sent()` 하나다
        t = {"v": 1000.0}
        f = Frontier(now=lambda: t["v"])
        f.add(["http://a.test/1", "http://a.test/2"])
        self.assertEqual(f.next(), "http://a.test/1")
        self.assertEqual(f.next(), "http://a.test/2",
                         "팝이 간격 시계를 걸고 있다 — 요청은 아직 하나도 안 나갔다")

    def test_mark_sent_moves_the_interval_clock(self):
        # 팝과 발신 사이에 robots.txt 왕복 0.4초가 끼면, 팝 시각으로 재는 간격은
        # 실제로는 0.6초다 — 1초 하한을 어긴다 (digest [4])
        t = {"v": 1000.0}
        f = Frontier(now=lambda: t["v"])
        f.add(["http://a.test/1", "http://a.test/2"])
        f.next()
        f.mark_sent("a.test", 1000.4)
        t["v"] = 1001.0
        self.assertIsNone(f.next(), "팝 시각으로 재고 있다 — 실제 간격은 0.6초다")
        t["v"] = 1001.5
        self.assertEqual(f.next(), "http://a.test/2")

    def test_mark_sent_only_moves_later(self):
        # 이르게 당기는 것이 곧 위반이다
        t = {"v": 1000.0}
        f = Frontier(now=lambda: t["v"])
        f.add(["http://a.test/1", "http://a.test/2"])
        pop(f, lambda: t["v"])
        f.mark_sent("a.test", 999.0)
        t["v"] = 1000.5
        self.assertIsNone(f.next())

    def test_seconds_until_ready_skips_excluded_domain(self):
        # 요청이 떠 있는 도메인은 0초로 읽힌다 — 그것만 보고 기다리면
        # 정작 쿨다운이 풀리는 도메인을 놓친다
        t = {"v": 1000.0}
        f = Frontier(now=lambda: t["v"])
        f.add(["http://a.test/1", "http://a.test/2", "http://b.test/1"])
        pop(f, lambda: t["v"])  # a.test 발신 → 1001.0 까지 쿨다운
        t["v"] = 1000.5
        self.assertEqual(f.seconds_until_ready(), 0.0)
        self.assertAlmostEqual(f.seconds_until_ready(exclude={"b.test"}), 0.5)


class TestIntervalIsPublicNow(unittest.TestCase):
    """`interval(domain)` 은 `crawl` 이 **워커에 넘길 바닥값**으로 읽는 공개 계약이다.

    간접적으로는 `next`·`seconds_until_ready` 가 이미 쓰고 있었지만, 그 둘은
    "언제 팝할까" 를 재는 쪽이라 **값 자체가 내려가지 않는다**는 성질은 아무도
    단언하지 않았다. `crawl` 이 그 성질에 기대기 시작했으므로 여기서 못박는다.
    """

    def test_unknown_domain_reads_as_the_floor(self):
        self.assertEqual(Frontier().interval("a.test"), DOMAIN_INTERVAL)

    def test_declared_delay_is_what_it_reads_back(self):
        f = Frontier()
        f.set_delay("a.test", 5.0)
        self.assertEqual(f.interval("a.test"), 5.0)

    def test_it_never_goes_down(self):
        # 이 성질이 `crawl` 의 바닥값이 바닥인 이유다 — 내려가면 재시도가 빨라진다
        f = Frontier()
        f.set_delay("a.test", 5.0)
        f.set_delay("a.test", 2.0)
        f.set_delay("a.test", None)
        self.assertEqual(f.interval("a.test"), 5.0)

    def test_a_zero_declaration_still_reads_as_the_floor(self):
        # `Crawl-delay: 0` 은 "얼마든지 빨리" 지만 도메인당 1초는 컨셉의 하한이다
        f = Frontier()
        f.set_delay("a.test", 0.0)
        self.assertEqual(f.interval("a.test"), DOMAIN_INTERVAL)

    def test_a_dropped_domain_reads_as_the_floor_again(self):
        # 상한 초과는 도메인을 통째로 버린다(`_delays` 에서도 지운다). 그 뒤 읽으면
        # 하한이다 — 30초를 넘는 값이 바닥값으로 새어 나가면 워커가 하루를 붙든다
        f = Frontier()
        f.set_delay("a.test", MAX_DELAY + 1)
        self.assertEqual(f.interval("a.test"), DOMAIN_INTERVAL)

    def test_domains_do_not_share_their_intervals(self):
        f = Frontier()
        f.set_delay("a.test", 5.0)
        self.assertEqual(f.interval("b.test"), DOMAIN_INTERVAL)
