import io
import unittest
from unittest import mock

import urllib.error

from websearch import fetcher


def _resp(status=200, ctype="text/html; charset=utf-8", body=b"<html>hi</html>"):
    r = mock.Mock()
    r.status = status
    r.headers = {"Content-Type": ctype}
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

    def test_retry_succeeds_second_try(self):
        with mock.patch("urllib.request.urlopen", side_effect=[OSError("t"), _resp()]):
            got = fetcher.fetch("http://a.com/")
        self.assertEqual(got.status, 200)
        self.assertEqual(got.html, "<html>hi</html>")
