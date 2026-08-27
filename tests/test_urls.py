import unittest

from websearch import urls


class TestAsciiUrlUntouched(unittest.TestCase):
    def test_query_and_fragment_kept(self):
        u = "http://h/a?b=c&d=e#f"
        self.assertEqual(urls.to_ascii(u), u)

    def test_port_and_ipv6_kept(self):
        for u in ["http://h:8080/x", "http://[::1]:8080/x", "http://u:pw@h/x"]:
            with self.subTest(url=u):
                self.assertEqual(urls.to_ascii(u), u)

    def test_empty_query_marker_kept(self):
        # urlsplit/urlunsplit 왕복은 빈 '?' 와 '#' 를 삼킨다. ASCII 는 손대지 않는다는
        # 규칙이 없으면 여기서 조용히 URL 이 바뀐다 (계약 1)
        for u in ["http://h/x?", "http://h/x#"]:
            with self.subTest(url=u):
                self.assertEqual(urls.to_ascii(u), u)

    def test_percent_encoded_not_double_encoded(self):
        u = "http://h/%EA%B0%80.html"
        self.assertEqual(urls.to_ascii(u), u)  # % 가 %25 가 되면 안 된다


class TestNonAsciiEncoded(unittest.TestCase):
    def test_path_percent_encoded(self):
        self.assertEqual(urls.to_ascii("http://h/위키/대한민국"),
                         "http://h/%EC%9C%84%ED%82%A4/%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD")

    def test_separators_survive_in_query_and_fragment(self):
        self.assertEqual(urls.to_ascii("http://h/검색?q=김치&n=1#단면"),
                         "http://h/%EA%B2%80%EC%83%89?q=%EA%B9%80%EC%B9%98&n=1#%EB%8B%A8%EB%A9%B4")

    def test_idempotent(self):
        once = urls.to_ascii("http://h/위키/대한민국")
        self.assertEqual(urls.to_ascii(once), once)

    def test_empty_query_marker_kept(self):
        # ASCII 쪽과 같은 규칙 — 끝의 빈 '?'·'#' 가 사라지면 같은 페이지가 두 키가 된다
        self.assertEqual(urls.to_ascii("http://h/가?"), "http://h/%EA%B0%80?")
        self.assertEqual(urls.to_ascii("http://h/가#"), "http://h/%EA%B0%80#")
        self.assertEqual(urls.to_ascii("http://h/가?#f"), "http://h/%EA%B0%80?#f")

    def test_tab_stripped_like_urlsplit(self):
        # urlsplit 이 탭·개행을 떼므로 호스트 치환의 전제가 유지된다
        self.assertEqual(urls.to_ascii("http://한글도메인.test/가\t나"),
                         "http://xn--bj0bj3i97fq8o5lq.test/%EA%B0%80%EB%82%98")

    def test_two_spellings_converge(self):
        # 계획의 핵심 목표 — pages 에 /가.html 과 /%EA%B0%80.html 이 2행으로 남지 않는다
        self.assertEqual(urls.to_ascii("http://h/가.html"),
                         urls.to_ascii("http://h/%EA%B0%80.html"))


class TestIdnHost(unittest.TestCase):
    def test_host_punycoded_path_kept(self):
        self.assertEqual(urls.to_ascii("http://한글도메인.test/"),
                         "http://xn--bj0bj3i97fq8o5lq.test/")

    def test_port_kept(self):
        self.assertEqual(urls.to_ascii("http://한글도메인.test:8080/x"),
                         "http://xn--bj0bj3i97fq8o5lq.test:8080/x")

    def test_userinfo_kept(self):
        self.assertEqual(urls.to_ascii("http://u:pw@한글도메인.test/"),
                         "http://u:pw@xn--bj0bj3i97fq8o5lq.test/")


class TestUnconvertible(unittest.TestCase):
    def test_surrogate_gives_none(self):
        for u in ["http://h/" + chr(0xD800),
                  b"http://h/\xed\xa0\x80".decode("utf-8", "surrogateescape")]:
            with self.subTest(url=u.encode("utf-8", "backslashreplace")):
                self.assertIsNone(urls.to_ascii(u))

    def test_empty_label_host_gives_none(self):
        self.assertIsNone(urls.to_ascii("http://가..나/"))

    def test_overlong_label_gives_none(self):
        self.assertIsNone(urls.to_ascii("http://" + "가" * 64 + ".test/"))

    def test_never_raises(self):
        # 크롤 루프를 죽인 원인이 여기서 새어 나온 예외다 (설계 계약 3)
        for u in ["", "가", "http://", "http:///x", "://h/가", "http://[::1/가",
                  "https://h/가?a=나#다", "//h/가", "http://h/가%", "\ud800",
                  "http://" + "가" * 300 + "/"]:
            with self.subTest(url=u.encode("utf-8", "backslashreplace")):
                got = urls.to_ascii(u)
                self.assertTrue(got is None or got.isascii())


class TestDomainKey(unittest.TestCase):
    """예의 계약이 세는 단위. **같은 서버는 한 칸이다.**

    URL 동일성이 아니다 — `http://A.com/` 과 `http://a.com/` 은 이 뒤에도 두 번
    수집되고 두 행으로 저장된다(digest `[5]`, 별개의 수술). 여기서 같아지는 것은
    **간격을 세는 칸** 하나뿐이다.
    """

    def test_host_case_does_not_make_a_new_server(self):
        self.assertEqual(urls.domain_key("http://B.test/1"),
                         urls.domain_key("http://b.test/2"))

    def test_default_port_is_the_same_server(self):
        self.assertEqual(urls.domain_key("http://b.test:80/1"),
                         urls.domain_key("http://b.test/2"))
        self.assertEqual(urls.domain_key("https://b.test:443/1"),
                         urls.domain_key("https://b.test/2"))

    def test_the_other_scheme_default_port_is_not_stripped(self):
        # `http://h:443` 은 443 이 http 의 기본이 아니라 **다른 서버**다.
        # 스킴을 안 보고 포트만 지우면 여기서 갈린다
        self.assertNotEqual(urls.domain_key("http://b.test:443/1"),
                            urls.domain_key("http://b.test/2"))
        self.assertNotEqual(urls.domain_key("https://b.test:80/1"),
                            urls.domain_key("https://b.test/2"))

    def test_a_real_port_still_makes_its_own_server(self):
        # **대조군.** 이것이 없으면 "전부 한 칸으로 합치기" 로도 위 테스트가 통과한다.
        # `e2e/perf_crawl.py` 의 도메인 12개가 전부 이쪽이다
        self.assertNotEqual(urls.domain_key("http://b.test:8001/1"),
                            urls.domain_key("http://b.test:8002/1"))
        self.assertNotEqual(urls.domain_key("http://b.test:8001/1"),
                            urls.domain_key("http://b.test/1"))

    def test_two_hosts_are_still_two_servers(self):
        self.assertNotEqual(urls.domain_key("http://a.test/1"),
                            urls.domain_key("http://b.test/1"))

    def test_credentials_are_not_part_of_the_server(self):
        self.assertEqual(urls.domain_key("http://u:p@b.test/1"),
                         urls.domain_key("http://b.test/2"))

    def test_ipv6_literal_survives_whole(self):
        # `[::1]` 의 콜론은 포트 구분자가 아니다 — 여기서 자르면 주소가 망가진다
        self.assertEqual(urls.domain_key("http://[::1]:80/1"),
                         urls.domain_key("http://[::1]/2"))
        self.assertNotEqual(urls.domain_key("http://[::1]:8080/1"),
                            urls.domain_key("http://[::1]/2"))
        self.assertIn("::1", urls.domain_key("http://[::1]/2"))

    def test_an_unreadable_port_does_not_raise(self):
        """`urlsplit(...).port` 는 여기서 ValueError 를 던진다 — 크롤 루프가 죽는다.

        지금 열쇠를 만드는 `netloc` 은 **절대 안 던진다**. 그 성질을 잃지 않는 것이
        이 계획에서 새로 생길 수 있는 유일한 크래시 경로다.
        """
        for url in ["http://b.test:abc/1", "http://b.test:99999/1",
                    "http://b.test:/1", "http://:80/1", "http://[::1/1",
                    "", "http://", "not a url"]:
            with self.subTest(url=url):
                self.assertIsInstance(urls.domain_key(url), str)

    def test_it_is_idempotent_on_its_own_output(self):
        # 열쇠를 다시 URL 로 만들어 넣어도 같은 값이어야 한다 — 아니면 어느 자리에서
        # 부르느냐에 따라 칸이 갈린다
        key = urls.domain_key("http://B.test:80/1")
        self.assertEqual(urls.domain_key("http://" + key + "/2"), key)


if __name__ == "__main__":
    unittest.main()
