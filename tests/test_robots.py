import unittest
from unittest import mock

from websearch import robots


def _cache_with(fetch):
    c = robots.RobotsCache()
    c._fetch_robots = fetch  # 네트워크 차단 (project.md 한도)
    return c


class TestRobotsCache(unittest.TestCase):
    def test_allows_when_robots_permits(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nAllow: /"))
        self.assertTrue(c.allowed("http://a.com/page"))

    def test_blocks_when_robots_disallows(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nDisallow: /secret"))
        self.assertFalse(c.allowed("http://a.com/secret/x"))
        self.assertTrue(c.allowed("http://a.com/open"))

    def test_allows_when_robots_missing(self):
        c = _cache_with(lambda base: (404, ""))
        self.assertTrue(c.allowed("http://a.com/page"))

    def test_blocks_when_robots_fetch_fails(self):
        c = _cache_with(lambda base: (503, ""))
        self.assertFalse(c.allowed("http://a.com/page"))

    def test_fetches_once_per_domain(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nAllow: /"))
        c = _cache_with(fetch)
        c.allowed("http://a.com/1")
        c.allowed("http://a.com/2")
        self.assertEqual(fetch.call_count, 1)


class TestCrawlDelay(unittest.TestCase):
    def test_reports_declared_delay(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 3\nAllow: /"))
        self.assertEqual(c.delay("http://a.com/page"), 3.0)

    def test_no_directive_reports_none(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nAllow: /"))
        self.assertIsNone(c.delay("http://a.com/page"))

    def test_fractional_delay_is_not_lost(self):
        # stdlib 은 isdigit 검사로 "3.5" 를 조용히 버린다 — 그러면 1초로 떨어져
        # 사이트가 요청한 것보다 3.5배 빠르게 때린다. 윤리 축에서 이건 위반이다
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 3.5"))
        self.assertEqual(c.delay("http://a.com/page"), 3.5)

    def test_missing_robots_has_no_delay(self):
        c = _cache_with(lambda base: (404, ""))
        self.assertIsNone(c.delay("http://a.com/page"))

    def test_shares_one_robots_fetch_with_allowed(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nCrawl-delay: 2"))
        c = _cache_with(fetch)
        c.allowed("http://a.com/1")
        self.assertEqual(c.delay("http://a.com/2"), 2.0)
        self.assertEqual(fetch.call_count, 1)

    def test_fallback_takes_the_slowest_line_in_our_group(self):
        # 한 그룹이 여러 번 말하면 가장 느린 것을 고른다 — 느린 쪽으로만 틀린다.
        # 남의 그룹(other)은 우리 값이 아니므로 보지 않는다
        c = _cache_with(lambda base: (200, "User-agent: other\nCrawl-delay: 30.5\n\n"
                                           "User-agent: *\nCrawl-delay: 2.5\n"
                                           "Crawl-delay: 7.5"))
        self.assertEqual(c.delay("http://a.com/page"), 7.5)

    def test_malformed_delay_never_speeds_us_up(self):
        # robots.txt 는 원격 입력이다. 망가진 값에 예외를 내면 크롤 전체가 죽고,
        # 마음대로 빠르게 잡으면 윤리 위반이다. 규칙은 하나 — **느린 쪽으로만 틀린다.**
        # 숫자가 없으면 지시 없음(호출부가 기본 1초), 숫자가 앞에 있으면 그 값을 쓴다
        # ("5s" 를 5초로 읽는 것은 1초로 떨어지는 것보다 사이트 뜻에 가깝다)
        for value, want in [("abc", None), ("", None), ("-5", None),
                            ("5s", 5.0), ("2 # 주석", 2.0)]:
            with self.subTest(value=value):
                c = _cache_with(lambda base, v=value: (200, "User-agent: *\nCrawl-delay: %s" % v))
                self.assertEqual(c.delay("http://a.com/page"), want)

    def test_fallback_ignores_other_agents_groups(self):
        # 폴백은 "우리에게 적용되는 그룹"만 본다. 남의 그룹(86400)을 집으면
        # 1.5초면 지킬 수 있는 사이트를 통째로 버리게 된다 (frontier.MAX_DELAY)
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 1.5\n\n"
                                           "User-agent: AhrefsBot\nCrawl-delay: 86400\n"))
        self.assertEqual(c.delay("http://a.com/page"), 1.5)

    def test_our_own_group_wins_over_wildcard(self):
        c = _cache_with(lambda base: (200, "User-agent: websearchbot\nCrawl-delay: 4.5\n\n"
                                           "User-agent: *\nCrawl-delay: 0.5\n"))
        self.assertEqual(c.delay("http://a.com/page"), 4.5)

    def test_exponent_notation_is_not_read_as_one_second(self):
        # "1e3" 의 앞 숫자만 집으면 1000초를 요구한 사이트를 1초로 때린다
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 1e3"))
        self.assertEqual(c.delay("http://a.com/page"), 1000.0)


class TestOneServerOneRobotsDocument(unittest.TestCase):
    """`robots.txt` 를 **서버당 한 번**만 받는가 (계획 017 기대 5).

    실측(고치기 전): `LOCALHOST` 와 `localhost` 링크가 섞이면 같은 서버의
    `robots.txt` 를 **두 번** 받고, 그 두 번째가 선언한 간격을 안 지키고 나간다.
    받는 것 자체가 요청이라 이것도 예의 계약 안이다.
    """

    def _counting(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nCrawl-delay: 3"))
        return fetch, _cache_with(fetch)

    def test_host_case_does_not_fetch_it_twice(self):
        fetch, c = self._counting()
        c.allowed("http://a.com/1")
        c.allowed("http://A.COM/2")
        self.assertEqual(fetch.call_count, 1)

    def test_the_declaration_reaches_the_other_spelling(self):
        # 두 번 안 받는 것만으로는 부족하다 — 받아 둔 값이 다른 표기에도 읽혀야 한다
        _, c = self._counting()
        self.assertEqual(c.delay("http://a.com/1"), 3.0)
        self.assertEqual(c.delay("http://A.COM/2"), 3.0)
        self.assertEqual(c.known_delay("http://A.COM/2"), 3.0)

    def test_default_port_is_the_same_document(self):
        fetch, c = self._counting()
        c.allowed("http://a.com/1")
        c.allowed("http://a.com:80/2")
        self.assertEqual(fetch.call_count, 1)

    def test_the_other_scheme_is_its_own_document(self):
        # **대조군.** `robots.txt` 는 스킴별 문서다 — 한쪽 선언을 다른 쪽에 쓰면
        # 없는 지시를 지어내는 것이고, 016 이 그 자리를 이미 정리했다
        fetch, c = self._counting()
        c.allowed("http://a.com/1")
        c.allowed("https://a.com/2")
        self.assertEqual(fetch.call_count, 2)

    def test_a_real_port_is_its_own_document(self):
        # **대조군.** 포트가 다르면 다른 서버고 `robots.txt` 도 각자의 것이다
        fetch, c = self._counting()
        c.allowed("http://a.com:8001/1")
        c.allowed("http://a.com:8002/2")
        self.assertEqual(fetch.call_count, 2)

    def test_it_asks_the_address_it_keyed_by(self):
        # 열쇠와 실제로 GET 하는 주소가 갈리면, 한 번만 받되 **엉뚱한 곳에서** 받는다
        fetch, c = self._counting()
        c.allowed("http://A.COM:80/1")
        self.assertEqual(fetch.call_args[0][0], "http://a.com")


class TestABrokenUrlDoesNotKillTheCrawl(unittest.TestCase):
    """열쇠를 만들다 던지면 크롤이 통째로 죽는다 (백지 리뷰 지적 #1).

    `urlsplit` 은 닫히지 않은 IPv6 리터럴에 ValueError 를 던진다. 그 예외가
    워커에서 나면 `crawl._store_result` 의 `except` 가 잡지만, **그 복구 경로가
    다시 `known_delay(url)` 을 부른다** — 같은 예외가 두 번째로 나면 아무도 안
    잡는다. 링크 하나가 크롤 전체를 끝낸다.
    """

    BROKEN = ["http://[::1/x", "http://u:p@[::1/x", "http://b.test:abc/1", ""]

    def test_no_call_raises(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 3"))
        for url in self.BROKEN:
            with self.subTest(url=url):
                c.allowed(url)
                c.delay(url)
                c.known_delay(url)

    def test_a_broken_url_gets_its_own_slot(self):
        # 멀쩡한 서버의 값을 물려받으면 안 된다 — 조용히 남의 지시를 쓰는 꼴이다
        self.assertNotEqual(robots._base("http://[::1/x"), robots._base("http://b.test/1"))

    def test_credentials_are_not_part_of_the_key_even_when_broken(self):
        # 폴백 경로도 userinfo 를 뗀다 — 안 떼면 열쇠에 비밀번호가 실려 다닌다
        self.assertNotIn("p@", robots._base("http://u:p@[::1/x"))


class TestRobotsRequestIdentifiesUs(unittest.TestCase):
    def test_robots_txt_request_carries_our_user_agent(self):
        # robots.txt 를 익명으로 가져오면, UA 별로 다른 robots 를 내주는 사이트가
        # 우리에게 맞는 규칙을 못 준다. 페이지 요청과 같은 이름으로 물어야 한다
        with mock.patch("urllib.request.urlopen") as opener:
            opener.return_value.__enter__ = lambda s: s
            opener.return_value.__exit__ = lambda s, *a: False
            opener.return_value.status = 200
            opener.return_value.read.return_value = b"User-agent: *\nAllow: /"
            robots.RobotsCache()._fetch_robots("http://a.com")
        req = opener.call_args[0][0]
        self.assertEqual(req.get_header("User-agent"), robots.USER_AGENT)
        self.assertEqual(req.full_url, "http://a.com/robots.txt")


class TestKnownDelay(unittest.TestCase):
    """`known_delay()` 는 **캐시만 본다** — 메인 스레드가 부를 수 있는 유일한 조회다.

    동시화 설계 계약 4(메인 스레드는 네트워크를 안 한다). `delay()` 와 달리 아직 안 받은
    도메인에 대해 robots.txt 를 받으러 나가지 않는다 (design_crawl-politeness.md 1-1절).
    """

    def test_returns_none_without_touching_the_network(self):
        fetch = mock.Mock(return_value=(200, "User-agent: *\nCrawl-delay: 5"))
        c = _cache_with(fetch)
        self.assertIsNone(c.known_delay("http://a.com/page"))
        self.assertEqual(fetch.call_count, 0, "캐시 조회가 robots.txt 를 받으러 나갔다")

    def test_returns_the_delay_once_it_is_cached(self):
        # 긍정 짝. 위 테스트만 있으면 "언제나 None" 으로도 통과한다
        fetch = mock.Mock(return_value=(200, "User-agent: *\nCrawl-delay: 5"))
        c = _cache_with(fetch)
        c.allowed("http://a.com/page")          # 여기서 받는다
        self.assertEqual(c.known_delay("http://a.com/other"), 5.0)
        self.assertEqual(fetch.call_count, 1, "캐시가 있는데 또 받았다")

    def test_returns_none_when_robots_declares_no_delay(self):
        # "모른다" 와 "지시가 없다" 는 둘 다 None 이고, 둘 다 호출부의 기본값이 답이다
        c = _cache_with(lambda base: (200, "User-agent: *\nAllow: /"))
        c.allowed("http://a.com/page")
        self.assertIsNone(c.known_delay("http://a.com/page"))

    def test_does_not_leak_another_domains_delay(self):
        c = _cache_with(lambda base: (200, "User-agent: *\nCrawl-delay: 5"))
        c.allowed("http://slow.com/page")
        self.assertIsNone(c.known_delay("http://other.com/page"))


class _Resp:
    """`read(n)` 을 실제로 지키는 가짜 응답. mock 은 인자를 무시해 상한을 못 잰다."""

    def __init__(self, body, status=200):
        self.body, self.status, self.asked = body, status, None

    def read(self, n=-1):
        self.asked = n
        return self.body if n < 0 else self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fetch(body):
    resp = _Resp(body)
    with mock.patch("urllib.request.urlopen", return_value=resp):
        return robots.RobotsCache()._fetch_robots("http://a.com")[1], resp


def _fetch_body(body):
    return _fetch(body)[0]


class TestRobotsBodyIsBounded(unittest.TestCase):
    """robots.txt 는 **우리가 크기를 정하지 않은 남의 바이트**다 — `fetcher` 는 이미
    `MAX_BYTES` 로 막는데 여기만 안 막혀 있었다(digest 후보 `[5]`)."""

    def test_a_huge_robots_txt_does_not_come_into_memory_whole(self):
        body, resp = _fetch(b"User-agent: *\nDisallow: /x\n" + b"# pad\n" * 200_000)
        # **읽고 나서 자르면 늦다** — 이미 메모리에 들어와 있다. `read` 에 준 수를 본다
        self.assertGreater(resp.asked, 0)
        self.assertLessEqual(resp.asked, robots.MAX_ROBOTS_BYTES + 1)
        self.assertLessEqual(len(body), robots.MAX_ROBOTS_BYTES)

    def test_the_cut_line_is_dropped_not_half_parsed(self):
        # 반쪽 `Disallow: /sec` 는 원문(`/secret`)보다 **덜** 막는다 — 잘린 줄은 버린다
        head = b"User-agent: *\nDisallow: /a\n"
        pad = b"#" + b"p" * 98 + b"\n"
        body = _fetch_body(head + pad * (robots.MAX_ROBOTS_BYTES // 100) + b"Disallow: /secret")
        self.assertEqual(body.rsplit("\n", 1)[-1], "#" + "p" * 98)  # 마지막 줄이 온전하다
        self.assertNotIn("Disallow: /sec", body.split("Disallow: /a")[1])

    def test_a_normal_robots_txt_keeps_its_last_line(self):
        # 상한을 안 넘으면 아무것도 안 자른다. 끝 개행이 없는 파일이 흔하다
        body = _fetch_body(b"User-agent: *\nCrawl-delay: 5")
        self.assertEqual(body, "User-agent: *\nCrawl-delay: 5")
