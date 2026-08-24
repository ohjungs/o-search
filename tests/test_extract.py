import unittest

from websearch.extract import extract_text, is_noindex


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


class TestIsNoindex(unittest.TestCase):
    """색인 거부 선언 판정. 크롤 윤리 축 — 오탐(색인 못 함)보다 미탐(색인함)이 더 나쁘다."""

    def test_noindex(self):
        self.assertTrue(is_noindex('<html><head><meta name="robots" content="noindex"></head></html>'))

    def test_none_means_noindex(self):
        self.assertTrue(is_noindex('<meta name="robots" content="none">'))

    def test_case_and_spacing_and_list(self):
        self.assertTrue(is_noindex('<META NAME="ROBOTS" CONTENT="NOINDEX, NOFOLLOW">'))
        self.assertTrue(is_noindex('<meta   name = "robots"   content = " NoIndex , nofollow " >'))
        self.assertTrue(is_noindex("<meta name=robots content=noindex>"))

    def test_index_follow_is_allowed(self):
        self.assertFalse(is_noindex('<meta name="robots" content="index, follow">'))

    def test_no_meta_is_allowed(self):
        self.assertFalse(is_noindex("<html><title>t</title><p>본문</p></html>"))

    def test_other_bot_name_ignored(self):
        # 이 크롤러의 UA 는 자기 이름을 쓴다 — googlebot 지시는 우리 것이 아니다
        self.assertFalse(is_noindex('<meta name="googlebot" content="noindex">'))

    def test_word_in_body_is_not_a_directive(self):
        # 오탐 금지: 본문이 noindex 를 설명만 해도 색인이 막히면 안 된다
        self.assertFalse(is_noindex("<p>this page explains the noindex meta tag</p>"))

    def test_second_meta_counts(self):
        html = '<meta name="viewport" content="width=device-width"><meta name="robots" content="noindex">'
        self.assertTrue(is_noindex(html))

    def test_broken_html_still_detected(self):
        self.assertTrue(is_noindex('<html><head><title>t<meta name="robots" content="noindex"><body><p>hi'))

    def test_empty_html_no_raise(self):
        self.assertFalse(is_noindex(""))

    def test_commented_or_escaped_meta_is_not_a_directive(self):
        # 갭 탐색: 오탐은 문서를 조용히 사라지게 한다 — 주석과 이스케이프된 예제는 지시가 아니다
        self.assertFalse(is_noindex('<!-- <meta name="robots" content="noindex"> --><p>본문</p>'))
        self.assertFalse(is_noindex('<code>&lt;meta name="robots" content="noindex"&gt;</code>'))

    def test_substring_is_not_a_directive(self):
        self.assertFalse(is_noindex('<meta name="robots" content="noindexing">'))

    def test_empty_or_missing_content(self):
        self.assertFalse(is_noindex('<meta name="robots" content="">'))
        self.assertFalse(is_noindex('<meta name="robots">'))
