import unittest

from websearch.frontier import Frontier


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


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
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertIsNone(self.f.next())  # 1초 안 지남 — 낼 것 없음
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_other_domain_served_while_first_cooling(self):
        self.f.add(["http://a.com/1", "http://a.com/2", "http://b.com/1"])
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertEqual(self.f.next(), "http://b.com/1")  # a 쿨다운 중엔 b

    def test_wait_time_reported(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.f.next()
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
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.f.set_delay("a.com", 5.0)  # 크롤 루프가 robots 를 읽은 직후 알려준다
        self.assertEqual(self.f.next(), "http://b.com/1")
        self.clock.t += 1.5  # b 는 1초면 되고 a 는 아직 멀었다
        self.assertEqual(self.f.next(), "http://b.com/2")
        self.assertIsNone(self.f.next())
        self.clock.t += 3.5
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_wait_time_uses_declared_delay(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.f.next()
        self.f.set_delay("a.com", 4.0)
        self.assertAlmostEqual(self.f.seconds_until_ready(), 4.0)

    def test_delay_never_goes_below_the_floor(self):
        # 1초는 전제 조건이다 (concept.md) — 사이트가 풀어줄 수 있는 것이 아니다
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.f.next()
        self.f.set_delay("a.com", 0.1)
        self.clock.t += 0.5  # 요청받은 0.1초는 지났다 — 하한이 없으면 여기서 나온다
        self.assertIsNone(self.f.next())
        self.assertAlmostEqual(self.f.seconds_until_ready(), 0.5)
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_no_directive_keeps_default_interval(self):
        self.f.add(["http://a.com/1", "http://a.com/2"])
        self.f.next()
        self.f.set_delay("a.com", None)
        self.clock.t += 1.0
        self.assertEqual(self.f.next(), "http://a.com/2")

    def test_unkeepable_delay_drops_the_domain(self):
        # 못 지킬 간격이면 깎아서 계속 때리는 대신 그 도메인을 버린다
        self.f.add(["http://a.com/1", "http://slow.com/1"])
        self.f.set_delay("slow.com", 86400)
        self.f.add(["http://slow.com/2"])  # 나중에 링크로 다시 들어와도 안 받는다
        self.assertEqual(self.f.next(), "http://a.com/1")
        self.assertTrue(self.f.empty())
