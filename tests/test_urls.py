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


if __name__ == "__main__":
    unittest.main()
