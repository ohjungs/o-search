import unittest

from websearch import urls
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
        f.mark_sent(urls.domain_key(url), now())  # 진짜 crawl 이 쓰는 그 열쇠다
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
        # 같은 서버가 http/https 로 섞여 들어오면 한쪽은 지시가 없다.
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


class TestSameServerIsOneSlot(unittest.TestCase):
    """대소문자·기본 포트로 갈라진 URL 이 **간격을 나눠 갖는가.**

    실측(고치기 전): 셋을 넣으면 t=1000.000 에 **전부** 나가고 간격이 0.000초다.
    `http://b.test` 에만 건 `Crawl-delay: 5` 는 나머지 둘에 아예 안 걸린다.
    진짜 크롤 루프에서도 같은 값이 나온다 — `Crawl-delay: 3` 선언 서버가
    `LOCALHOST`/`localhost` 링크 탓에 2밀리초 안에 요청 4개를 받는다.

    **절대 조건("선언된 값보다 빨리 치지 않는다") 쪽이라 이것이 이 계획의 RED 다.**
    """

    def setUp(self):
        self.clock = FakeClock()
        self.f = Frontier(now=self.clock)

    def _drain(self, urls_in, limit=5):
        """지금 낼 수 있는 것을 전부 내고 `(시각, url)` 로 돌려준다. 크롤 루프의 자세다."""
        self.f.add(urls_in)
        sent = []
        for _ in range(limit):
            url = pop(self.f, self.clock)
            if url is None:
                break
            sent.append((self.clock.t, url))
        return sent

    def test_upper_case_host_waits_its_turn(self):
        sent = self._drain(["http://b.test/1", "http://B.test/2"])
        self.assertEqual(len(sent), 1,
                         "같은 서버 두 URL 이 같은 시각에 나갔다: %s" % (sent,))

    def test_default_port_waits_its_turn(self):
        sent = self._drain(["http://b.test/1", "http://b.test:80/2"])
        self.assertEqual(len(sent), 1,
                         "기본 포트를 붙였다고 새 서버가 됐다: %s" % (sent,))

    def test_https_default_port_waits_its_turn(self):
        sent = self._drain(["https://b.test/1", "https://b.test:443/2"])
        self.assertEqual(len(sent), 1, "%s" % (sent,))

    def test_a_real_port_is_still_its_own_server(self):
        # **대조군.** 없으면 "전부 한 칸으로 합치기" 로도 위 셋이 통과한다 —
        # 그러면 `perf_crawl` 의 도메인 12개가 한 줄로 서서 처리량이 죽는다
        sent = self._drain(["http://b.test:8001/1", "http://b.test:8002/2"])
        self.assertEqual(len(sent), 2,
                         "포트가 다른 두 서버가 서로를 기다렸다: %s" % (sent,))

    def test_a_declaration_reaches_the_other_spelling(self):
        # 선언은 한 표기에만 걸리지만 요청은 다른 표기로도 나간다
        self.f.set_delay(urls.domain_key("http://b.test/1"), 5.0)
        self.f.add(["http://b.test/1", "http://B.test/2"])
        self.assertEqual(pop(self.f, self.clock), "http://b.test/1")
        self.clock.t += 1.5  # 하한은 넘었지만 선언한 5초는 한참 남았다
        self.assertIsNone(self.f.next(),
                          "대문자 표기가 선언한 5초를 피해 나갔다")
        self.clock.t += 3.5
        self.assertEqual(self.f.next(), "http://B.test/2")

    def test_in_flight_covers_the_other_spelling(self):
        # 동시화 계약 3 — 떠 있는 도메인은 다시 안 내준다. 열쇠가 갈리면
        # 같은 서버로 요청 둘이 **동시에** 뜬다
        self.f.add(["http://b.test/1", "http://B.test/2"])
        first = self.f.next()
        busy = {urls.domain_key(first)}
        self.assertIsNone(self.f.next(exclude=busy),
                          "요청이 떠 있는데 같은 서버를 다시 내줬다")

    def test_an_unreadable_port_does_not_kill_the_queue(self):
        # 크롤 루프를 죽인 원인이 이런 자리에서 새어 나온 예외다
        sent = self._drain(["http://b.test:abc/1", "http://b.test:99999/2"])
        self.assertEqual(len(sent), 2, "%s" % (sent,))


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


class EthicsFloorTest(unittest.TestCase):
    """도메인 간격이 **사양의 윤리 하한(1초) 아래로 못 내려간다.**

    2026-09-09 무인 사이클이 강제 종료되며 작업 트리에 `DOMAIN_INTERVAL = 0.05` 를
    남겼고 — 주석이 *"내리지 않는다"* 고 적힌 그 줄이다 — **전수 706건이 전부
    초록이었다.** 잡은 것은 검사가 아니라 사람이 diff 를 눈으로 본 것이다.

    **위 단언들이 못 잡는 이유는 전부 상수를 «참조» 하기 때문이다**
    (`assertEqual(f.interval("a.test"), DOMAIN_INTERVAL)`). 값을 내리면 단언도 같이
    내려가 언제나 참이다 — 「간격을 지키나」는 재도 「그 간격이 윤리 하한 위인가」는
    아무도 안 잰다. 자가 자기 축을 안 재면 조용히 초록이다.

    **그래서 하한을 리터럴로 박는다.** 상수로 빼면 그 상수를 같이 내려서 다시 뚫린다 —
    재는 쪽과 재이는 쪽이 같은 값을 공유하면 그것은 자가 아니다.
    """

    # `docs/specs/concept.md` 기능 3 — *"도메인당 요청 간격 1초 이상은 기능이 아니라
    # **전제 조건** — 어기는 코드는 리뷰에서 RED 다"*. 사양이 준 숫자라 여기 리터럴이다.
    # **이 줄을 고쳐서 테스트를 통과시키지 않는다.** 고칠 일이 있으면 사양을 먼저 고친다.
    SPEC_FLOOR = 1.0

    def test_the_module_default_is_not_below_the_spec_floor(self):
        self.assertGreaterEqual(
            DOMAIN_INTERVAL, self.SPEC_FLOOR,
            "DOMAIN_INTERVAL 이 %s 초다 — 사양의 윤리 하한 %s 초 아래다"
            % (DOMAIN_INTERVAL, self.SPEC_FLOOR))

    def test_a_domain_never_gets_a_faster_interval_than_the_floor(self):
        """기본값만이 아니라 **실제로 쓰이는 값**을 잰다.

        상수가 1.0 이어도 `set_delay` 로 도메인마다 더 짧게 줄 수 있으면 같은 구멍이다.
        robots 가 **더 긴** 간격을 요구하면 그것을 따르는 것이 맞고(그래서 하한만 본다),
        **더 짧은** 요청은 예의가 아니라 남의 서버 사정일 뿐이라 안 따른다.

        **이 갈래는 오늘 처음부터 초록이었다** — `set_delay` 가 `max(interval, seconds)`
        로 단조 증가라 이미 막혀 있다. 그러니 이것은 **고친 것이 아니라 붙든 것**이고,
        여기 적는 이유는 그 성질이 주석에만 있었기 때문이다. 주석은 리팩터링을 못 막는다.
        """
        f = Frontier()
        self.assertGreaterEqual(f.interval("a.test"), self.SPEC_FLOOR)
        f.set_delay("a.test", 0.05)  # robots 가 짧게 요구해도
        self.assertGreaterEqual(
            f.interval("a.test"), self.SPEC_FLOOR,
            "robots 가 요구한 짧은 간격을 그대로 받았다 — 하한이 없다")
        f.set_delay("b.test", 5.0)   # 더 긴 요구는 그대로 따른다
        self.assertEqual(f.interval("b.test"), 5.0)


class BackoffRecoveryTest(unittest.TestCase):
    """**백오프는 성공하면 되돌아온다.** 안 그러면 나쁜 1분이 실행 전체를 벌한다.

    계획 84 가 429 백오프를 `set_delay` 로 걸었는데 그것은 **단조 증가**다 — robots 가
    선언한 `Crawl-delay` 를 지키려고 일부러 그렇게 만든 자리다. 그래서 429 를 다섯 번
    받으면 2→4→8→16→32 로 상한을 넘어 **도메인이 통째로 버려지고, 그 뒤 서버가 멀쩡해져도
    영영 안 돌아온다.**

    실물에서 이것이 문제가 된다: 위키미디어 6도메인이 같은 서버라 순간적으로 429 가
    몰리는데, 그 순간 때문에 남은 크롤 내내 그 도메인들을 못 간다.

    **벌점을 robots 간격과 분리한다** — robots 가 요구한 값은 내려가면 안 되고
    (그것이 `set_delay` 단조성의 이유다), 우리가 스스로 매긴 벌점은 내려가야 한다.
    """

    def test_a_penalty_widens_the_interval(self):
        f = Frontier()
        f.penalise("a.test")
        self.assertGreater(f.interval("a.test"), DOMAIN_INTERVAL)

    def test_success_relieves_the_penalty(self):
        f = Frontier()
        f.penalise("a.test")
        f.penalise("a.test")
        widened = f.interval("a.test")
        f.relieve("a.test")
        self.assertLess(f.interval("a.test"), widened, "성공했는데 벌점이 그대로다")

    def test_relief_never_goes_below_a_robots_delay(self):
        """**robots 가 요구한 간격은 벌점 회복이 못 깎는다.** 이것이 분리한 이유다."""
        f = Frontier()
        f.set_delay("a.test", 5.0)
        f.penalise("a.test")
        for _ in range(10):
            f.relieve("a.test")
        self.assertGreaterEqual(f.interval("a.test"), 5.0,
                                "벌점 회복이 robots 간격을 깎았다 — robots 위반이다")

    def test_relief_never_goes_below_the_ethics_floor(self):
        f = Frontier()
        for _ in range(10):
            f.relieve("a.test")
        self.assertGreaterEqual(f.interval("a.test"), 1.0)

    def test_enough_penalties_still_drop_the_domain(self):
        """**손을 떼는 길은 남는다.** 회복이 있다고 영원히 두드리면 안 된다."""
        f = Frontier()
        f.add(["http://a.test/x"])
        for _ in range(10):
            alive = f.penalise("a.test")
        self.assertFalse(alive, "계속 거절당하는 도메인을 안 버렸다")

    def test_a_penalty_does_not_leak_into_the_robots_delay(self):
        """**벌점이 robots 칸으로 새면 회복이 영영 불가능하다.**

        `set_delay` 는 단조 증가다. 그것이 `interval()`(벌점 포함)을 읽으면 429 벌점이
        robots 칸에 **굳어** `relieve` 가 못 내린다 — 실물 탐침이 잡았다: 429 셋 뒤
        200 이 아홉 번 와도 간격이 8.0초에 머물렀다. **단위 테스트가 둘을 따로만 봐서
        이 상호작용을 못 봤다**(계획 89 e2e 3절).
        """
        f = Frontier()
        f.penalise("a.test")
        f.penalise("a.test")          # 벌점 4.0
        f.set_delay("a.test", None)   # robots 는 아무 말도 안 했다
        f.relieve("a.test")
        f.relieve("a.test")           # 벌점이 사라져야 한다
        self.assertEqual(f.interval("a.test"), DOMAIN_INTERVAL,
                         "벌점이 robots 칸에 굳어 회복이 안 된다")
