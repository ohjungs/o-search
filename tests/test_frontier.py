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
