import unittest

from websearch.extract import extract_text


class TestExtractText(unittest.TestCase):
    def test_title_and_body(self):
        title, text = extract_text("<html><title>제목</title><body><p>본문 내용</p></body></html>")
        self.assertEqual(title, "제목")
        self.assertEqual(text, "본문 내용")

    def test_script_style_excluded(self):
        html = "<title>t</title><script>var x=1;</script><style>.a{}</style><p>보이는 글</p><noscript>ns</noscript>"
        _, text = extract_text(html)
        self.assertEqual(text, "보이는 글")

    def test_whitespace_normalized(self):
        _, text = extract_text("<p>줄\n\n바꿈</p>  <div>  많은   공백 </div>")
        self.assertEqual(text, "줄 바꿈 많은 공백")

    def test_missing_title_empty_string(self):
        title, text = extract_text("<p>본문만</p>")
        self.assertEqual(title, "")
        self.assertEqual(text, "본문만")

    def test_broken_html_no_raise(self):
        title, text = extract_text("<title>t<p>글<<<div")
        self.assertIn("글", text)
