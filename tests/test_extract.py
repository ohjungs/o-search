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

    def test_inline_tags_do_not_split_words(self):
        # 리뷰 발견: 태그 경계마다 공백을 넣어 Kimchi 가 "Kim chi" 로 쪼개졌다 → 검색 실패
        _, text = extract_text("<p>Kim<b>chi</b> 와 H<sub>2</sub>O</p>")
        self.assertEqual(text, "Kimchi 와 H2O")

    def test_block_tags_separate_words(self):
        _, text = extract_text("<p>가</p><p>나</p><div>다</div>라<br>마")
        self.assertEqual(text, "가 나 다 라 마")

    def test_title_keeps_inline_markup(self):
        # 리뷰 발견: <title> 안의 <b> 가 제목을 자르고 나머지를 본문으로 흘렸다
        title, text = extract_text("<title>김치 <b>백과</b> 사전</title><p>본문</p>")
        self.assertEqual(title, "김치 백과 사전")
        self.assertEqual(text, "본문")

    def test_nested_skip_tags(self):
        # 계획 스텝 1 완료 기준의 "중첩" 케이스
        _, text = extract_text("<noscript><style>.a{}</style>안보임</noscript><p>보임</p>")
        self.assertEqual(text, "보임")

    def test_control_characters_stripped(self):
        # 신뢰 경계: 크롤한 콘텐츠가 터미널 제어열을 그대로 싣고 나가면 결과를 위조할 수 있다
        _, text = extract_text("<p>정상\x1b]0;PWNED\x07글\x00\x9b2J</p>")
        self.assertFalse(any(ord(c) < 0x20 or 0x7F <= ord(c) < 0xA0 for c in text))
        self.assertIn("정상", text)

    def test_broken_html_no_raise(self):
        title, text = extract_text("<title>t<p>글<<<div")
        self.assertIn("글", text)
