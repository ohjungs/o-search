import unittest

from websearch import links


class TestExtract(unittest.TestCase):
    def test_relative_href_made_absolute(self):
        got = links.extract("http://a.com/dir/page", '<a href="../up">x</a>')
        self.assertEqual(got, ["http://a.com/up"])

    def test_fragment_stripped(self):
        got = links.extract("http://a.com/", '<a href="/p#sec">x</a>')
        self.assertEqual(got, ["http://a.com/p"])

    def test_non_http_schemes_dropped(self):
        html = '<a href="mailto:x@y.z">m</a><a href="javascript:void(0)">j</a><a href="ftp://f/">f</a>'
        self.assertEqual(links.extract("http://a.com/", html), [])

    def test_duplicates_removed_order_kept(self):
        html = '<a href="/b">1</a><a href="/a">2</a><a href="/b#f">3</a>'
        got = links.extract("http://a.com/", html)
        self.assertEqual(got, ["http://a.com/b", "http://a.com/a"])

    def test_href_missing_or_empty_ignored(self):
        self.assertEqual(links.extract("http://a.com/", '<a>x</a><a href="">y</a>'), [])

    def test_broken_html_does_not_raise(self):
        got = links.extract("http://a.com/", '<a href="/ok"><div><<<')
        self.assertEqual(got, ["http://a.com/ok"])
