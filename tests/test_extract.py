import unittest

from websearch.extract import extract_blocks, extract_text, is_noindex


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


def texts(html):
    """블록 텍스트만 — 태그가 논점이 아닌 단언에서 쓴다."""
    return [text for _tag, text in extract_blocks(html)]


class TestExtractBlocks(unittest.TestCase):
    """본문을 문단 단위로 끊는다. 색인 경로(`extract_text`)는 지나가지 않는다."""

    def test_block_boundaries(self):
        blocks = extract_blocks("<title>제목</title><p>첫 문단</p><p>둘째 문단</p>")
        self.assertEqual(blocks, [("p", "첫 문단"), ("p", "둘째 문단")])

    def test_join_equals_body(self):
        # 불변식 — 이것이 깨지면 색인 본문과 문단이 다른 텍스트가 된다.
        # 변이 M1(버퍼 비우기 삭제)이 여기서 죽는다: 블록이 누적돼 조인이 길어진다
        html = ("<title>요리</title><h2>김치</h2><p>어제 김치를 담갔다</p>"
                "<ul><li>배추</li><li>고춧가루</li></ul><div>끝</div>")
        self.assertEqual(" ".join(texts(html)), extract_text(html)[1])

    def test_each_block_carries_the_tag_that_made_it(self):
        # 이름표는 «열려 있는 가장 안쪽 블록 태그» 다. 소비자에게 내는 값이라
        # 맞아야 하지만 **근거를 고르는 자는 안 읽는다** — 이름표로 동점을 가르면
        # `<footer><p>` 를 문단으로 보고 더 틀린다(리뷰 6 · 12/19 대 15/19).
        # 이름표를 «직전 시작 태그» 로 붙이는 변이는 여기서 죽는다 — `</p>` 로
        # 끊기는 블록의 주인은 `<footer>` 가 아니라 `<p>` 다
        html = ("<nav><a href=/>김치</a></nav><article><p>본문 문단</p></article>"
                "<footer>맨 끝</footer>")
        self.assertEqual(extract_blocks(html),
                         [("nav", "김치"), ("p", "본문 문단"), ("footer", "맨 끝")])

    def test_the_label_survives_a_title_and_a_closing_tag(self):
        # 리뷰 6 [R6-2] — 이름표가 새는 자리 둘. ① `<title>` 은 부모가 블록을 **안 끊고**
        # early-return 하는데 이름표만 갈아 끼워져, 앞 문단이 `title` 로 나왔다.
        # ② 이름표가 닫는 태그에서 복원되지 않아 `</p>` 뒤의 꼬리 텍스트가 `p` 로
        # 나왔다 — 텍스트는 맞고 이름표만 틀리는 **거짓양성**이라 눈으로는 안 보인다
        self.assertEqual(extract_blocks("<p>김치찌개 하나<title>제목</title>"),
                         [("p", "김치찌개 하나")])
        self.assertEqual(extract_blocks("<article><p>본문</p>꼬리 텍스트</article>"),
                         [("p", "본문"), ("article", "꼬리 텍스트")])
        # 같은 이름이 겹치면 **안쪽부터** 닫는다 — `<div>` 중첩은 실물 HTML 의 기본형이라
        # 바깥부터 닫으면 한 번의 `</div>` 로 주인이 통째로 날아간다(변이 D 가 여기서 죽는다)
        self.assertEqual(extract_blocks("<article><div><div>가</div>나</div>다</article>"),
                         [("div", "가"), ("div", "나"), ("article", "다")])

    def test_last_block_survives_broken_html(self):
        # 변이 M2(마지막 flush 삭제)가 여기서 죽는다. 정상 HTML 은 닫는 태그가
        # flush 를 대신해 주므로 **닫히지 않은** 태그로 재야 한다
        self.assertEqual(extract_blocks("<p>가<p>나<div>다"),
                         [("p", "가"), ("p", "나"), ("div", "다")])

    def test_empty_blocks_are_not_returned(self):
        self.assertEqual(texts("<p>가</p><p></p><p>   </p><p>나</p>"), ["가", "나"])

    def test_a_line_break_is_not_a_paragraph_boundary(self):
        # 갈림길 6 — `<br>` 은 **줄바꿈**이지 문단이 아니다. `extract.py:7` 이 그것을
        # `_INLINE_TAGS` 에서 뺀 것은 색인에 공백 한 칸을 넣기 위해서인데, 블록 쪽이
        # 같은 자리를 경계로 읽어 한 문단이 낱말 조각으로 흩어졌다 — 그러면 4자짜리
        # 조각이 근거 자리를 이긴다(리뷰 4 실측)
        self.assertEqual(texts("<p>오늘은<br>김치찌개<br>내일은 된장찌개</p>"),
                         ["오늘은 김치찌개 내일은 된장찌개"])
        # 색인 쪽은 한 글자도 안 바뀐다 — 불변식이 그것을 못박는다
        html = "<p>가<br>나</p><p>다</p>"
        self.assertEqual(texts(html), ["가 나", "다"])
        self.assertEqual(" ".join(texts(html)), extract_text(html)[1])

    def test_the_other_two_spellings_of_a_line_break_are_not_boundaries_either(self):
        # `<br/>` 은 `handle_startendtag`, `</br>` 는 `handle_endtag` 로 들어온다 —
        # 시작 태그만 고치면 나머지 둘에서 같은 결함이 그대로 산다
        self.assertEqual(texts("<p>가<br/>나<br />다</p>"), ["가 나 다"])
        self.assertEqual(texts("<p>가</br>나</p>"), ["가 나"])

    def test_a_tag_that_sits_inside_a_paragraph_is_not_a_boundary_either(self):
        # 리뷰 5 — `<br>` **하나만** 경계에서 뺐더니 같은 성질의 형제가 그대로 남아
        # 한 문단을 조각냈다. `_INLINE_TAGS` 에서 빠진 phrasing 태그와 `_SKIP_TAGS`
        # 셋이 그 형제이고, 문단 안에 낀 광고·트래킹 `<script>`·`<img>` 는 실물
        # HTML 에서 `<br>` 보다 흔하다. 조각나면 4자짜리 조각이 근거 자리를 이긴다.
        # 단언은 «한 블록 + 그 블록이 곧 색인 본문» 이라 태그 하나를 집합에서 빼는
        # 변이가 전부 여기서 죽는다(블록이 둘로 갈린다)
        for name, html in [
            ("br", "<p>김치찌개는 한국의 대표 음식이다<br>배추로 만든다</p>"),
            ("script", "<p>김치찌개는 한국의 대표 음식이다<script>ad()</script>배추로 만든다</p>"),
            ("style", "<p>김치찌개는 한국의 대표 음식이다<style>.x{}</style>배추로 만든다</p>"),
            ("img", "<p>김치찌개는 한국의 대표 음식이다<img src=k.jpg>배추로 만든다</p>"),
            ("del/ins", "<p>김치찌개는 <del>일본</del><ins>한국</ins>의 대표 음식이다</p>"),
            ("label", "<p>김치찌개 <label>이름</label> 한국의 대표 음식이다</p>"),
            ("font", "<p>김치찌개는 <font color=red>매운</font> 한국 음식이다</p>"),
        ]:
            with self.subTest(shape=name):
                # 낱말이 붙는가(`김치찌개된장찌개`)는 **여기서 안 묻는다** — 그것은
                # `_INLINE_TAGS` 를 넓히는 일이라 색인 본문이 바뀌고 재색인이다
                self.assertEqual(texts(html), [extract_text(html)[1]])

    def test_inline_markup_does_not_split_a_block(self):
        # `extract_text` 와 같은 계약 — 인라인 태그는 단어 안에 끼어든다
        self.assertEqual(texts("<p>Kim<b>chi</b> 와 H<sub>2</sub>O</p>"),
                         ["Kimchi 와 H2O"])

    def test_script_and_style_are_not_blocks(self):
        self.assertEqual(
            texts("<p>보이는 글</p><script>var x=1;</script><style>.a{}</style>"),
            ["보이는 글"])

    def test_title_is_not_a_block(self):
        self.assertEqual(texts("<title>제목</title><p>본문</p>"), ["본문"])

    def test_no_body_is_an_empty_list(self):
        self.assertEqual(extract_blocks(""), [])
        self.assertEqual(extract_blocks("<title>제목만</title>"), [])

    def test_control_only_block_is_dropped_and_that_breaks_the_join(self):
        # 불변식의 **유일한 알려진 위반**을 현 동작 그대로 고정한다. 통짜 정규화는
        # 제어문자 블록 자리에 겹공백을 남기고(`'가  나'`), 블록 쪽은 빈 블록을 버린다.
        # 고치려면 `_normalize` 를 바꿔야 하고 그것이 **색인 본문을 바꾼다** — 안 고친다
        html = "<p>가</p><p>\x01</p><p>나</p>"
        self.assertEqual(texts(html), ["가", "나"])
        self.assertEqual(extract_text(html)[1], "가  나")


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

    def test_space_separated_directives(self):
        # 리뷰 발견: 쉼표로만 쪼개 content="noindex nofollow" 를 놓쳤다 — 미탐
        self.assertTrue(is_noindex('<meta name="robots" content="noindex nofollow">'))
        self.assertTrue(is_noindex('<meta name="robots" content="nofollow noindex">'))

    def test_substring_is_not_a_directive(self):
        self.assertFalse(is_noindex('<meta name="robots" content="noindexing">'))

    def test_empty_or_missing_content(self):
        self.assertFalse(is_noindex('<meta name="robots" content="">'))
        self.assertFalse(is_noindex('<meta name="robots">'))
