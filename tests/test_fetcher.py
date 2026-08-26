import io
import unittest
from unittest import mock

import urllib.error
import urllib.request

from websearch import fetcher


def _resp(status=200, ctype="text/html; charset=utf-8", body=b"<html>hi</html>",
          final_url="http://a.com/"):
    r = mock.Mock()
    r.status = status
    r.headers = mock.Mock()
    r.headers.get = lambda k, d="": {"Content-Type": ctype}.get(k, d)
    r.headers.get_content_charset = lambda: (
        ctype.split("charset=")[1] if "charset=" in ctype else None)
    r.geturl = lambda: final_url
    r.read.return_value = body
    r.__enter__ = lambda s: s
    r.__exit__ = lambda s, *a: False
    return r


class TestFetch(unittest.TestCase):
    def test_success_returns_html(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp()):
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(got.status, 200)
        self.assertEqual(got.html, "<html>hi</html>")

    def test_non_html_content_type_dropped(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp(ctype="application/pdf")):
            got = fetcher.fetch("http://a.com/f.pdf")
        self.assertEqual(got.status, 200)
        self.assertIsNone(got.html)

    def test_http_error_returns_status_no_html(self):
        err = urllib.error.HTTPError("http://a.com/", 404, "nf", {}, io.BytesIO(b""))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(got.status, 404)
        self.assertIsNone(got.html)

    def test_timeout_retries_then_gives_up(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("timeout")) as m:
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(m.call_count, 3)  # 1 + 재시도 2
        self.assertEqual(got.status, 0)
        self.assertIsNone(got.html)

    def test_scheme_less_url_fails_without_traceback(self):
        got = fetcher.fetch("example.com")
        self.assertEqual(got, fetcher.FetchResult(0, None, None))

    def test_final_url_after_redirect_reported(self):
        with mock.patch("urllib.request.urlopen", return_value=_resp(final_url="http://b.com/f")):
            got = fetcher.fetch("http://a.com/r")
        self.assertEqual(got.url, "http://b.com/f")

    def test_charset_from_header_respected(self):
        body = "한글".encode("euc-kr")
        with mock.patch("urllib.request.urlopen",
                        return_value=_resp(ctype="text/html; charset=euc-kr", body=body)):
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(got.html, "한글")

    def test_read_capped_at_max_bytes(self):
        r = _resp()
        with mock.patch("urllib.request.urlopen", return_value=r):
            fetcher.fetch("http://a.com/")
        r.read.assert_called_once_with(fetcher.MAX_BYTES)

    def test_non_ascii_path_fails_quietly_without_retry(self):
        # urlopen 안에서 요청 줄을 ascii 로 인코딩하다 UnicodeEncodeError 가 난다.
        # 연결 전에 터지므로 서버 없이도 재현된다. wraps 로 진짜 urlopen 을 부르면서 횟수만 센다.
        with mock.patch("urllib.request.urlopen",
                        wraps=urllib.request.urlopen) as m:
            got = fetcher.fetch("http://127.0.0.1:9/위키/대한민국")
        self.assertEqual(got, fetcher.FetchResult(0, None, None))
        self.assertEqual(m.call_count, 1)  # 재시도하지 않는다

    def test_non_ascii_host_fails_quietly_without_retry(self):
        # IDN 호스트는 Host 헤더를 latin-1 로 인코딩하다 터진다. 역시 연결 전이다.
        with mock.patch("urllib.request.urlopen",
                        wraps=urllib.request.urlopen) as m:
            got = fetcher.fetch("http://한글도메인.test/")
        self.assertEqual(got, fetcher.FetchResult(0, None, None))
        self.assertEqual(m.call_count, 1)

    def test_retry_succeeds_second_try(self):
        with mock.patch("urllib.request.urlopen", side_effect=[OSError("t"), _resp()]):
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(got.status, 200)
        self.assertEqual(got.html, "<html>hi</html>")
