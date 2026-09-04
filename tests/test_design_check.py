"""검사기 `e2e/design_check.py` 의 3번 축(대비)이 **무엇을 어느 자로 재는지**를 고정한다.

계획 43 이 넣은 셋 — 비텍스트 자(3.0) · 포커스 링 짝 · 뒤집은 커버리지 강제 — 은
전부 e2e 파일 안에 있고, 그 파일은 제품 CSS 가 통과하는 한 종료 0 이다. 그래서
**비텍스트 축을 통째로 지워도, `NO_PAIR` 에 `--focus` 를 몰래 넣어도 종료 0 이다.**
린트형 검사는 자기를 붙드는 단언이 없으면 조용히 죽는다 — `token_maps` 의 다크 블록
가드가 그것 때문에 생겼고(그 파일 첫머리), 계획 42 리뷰가 같은 형태를 한 번 더 짚었다.
여기 있는 것이 그 단언이다.

**제품 색값을 기대값으로 들지 않는다**(`design_focus-contrast.md ## 계약`) — 검사기 옆에
값을 따로 들면 색을 고쳐도 옛 값으로 통과를 내준다. 붙드는 것은 **어느 자로 재는가**다.
다만 아래 셋은 **비틀 자리를 가리키느라** 색 리터럴을 적는다(`--focus:#ea580c` 등).
가리키는 것과 기대하는 것은 다르다 — 그 자리가 사라지면 `twist` 가 단언으로 죽으므로
옛 값으로 조용히 통과하는 길은 없다.
입력은 전부 제품 CSS 를 최소한만 비튼 것이고(`test_quality_eval.py` 와 같은 방식),
비틀기가 실제로 심어졌는지 먼저 단언한다.
"""

import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "e2e"))

from design_check import check_contrast          # noqa: E402
from websearch.serve import CSS                  # noqa: E402


def run(css):
    """(기준 위반 목록, 측정 불능 목록, 화면 출력)."""
    fail, unmeasurable, out = [], [], io.StringIO()
    with contextlib.redirect_stdout(out):
        check_contrast(css, fail, unmeasurable)
    return fail, unmeasurable, out.getvalue()


# 링을 그리는 제품 규칙 그대로. **색값이 아니라 규칙의 모양**이라 드리프트 대상이 아니다 —
# 자리가 사라지면 `twist` 가 먼저 빨개진다.
RING_RULE = (".sb input:focus-visible,.sb button:focus-visible,a:focus-visible{"
             "outline:3px solid var(--focus);\noutline-offset:2px}")


class ContrastAxisTest(unittest.TestCase):
    def twist(self, old, new):
        """제품 CSS 를 한 곳만 비튼다. 비틀 자리가 실재하는지 먼저 단언한다."""
        self.assertIn(old, CSS, "비틀 자리가 CSS 에서 사라졌다: %s" % old)
        return CSS.replace(old, new)

    def test_focus_ring_is_measured_against_the_nontext_floor(self):
        """제품 CSS 에서 `--focus` 가 **두 맵 모두** 기준 3.0 으로 재진다.

        축을 지우거나 `NO_PAIR` 에 `--focus` 를 넣으면 이 행이 안 찍혀 여기서 빨개진다 —
        검사기 쪽은 둘 다 종료 0 이라 아무 말도 하지 않는다. 값은 안 붙든다.
        """
        fail, unmeasurable, out = run(CSS)
        self.assertEqual((fail, unmeasurable), ([], []), out)
        # 규칙 요약 줄에도 --focus 가 있으므로 **재는 행만** 센다(`on` 이 있는 행).
        lines = [ln for ln in out.splitlines() if "--focus" in ln and " on " in ln]
        self.assertEqual(len(lines), 2, "라이트·다크 두 행이어야 한다:\n%s" % out)
        for line in lines:
            self.assertIn("기준 3.0", line)

    def test_color_token_without_pair_or_reason_is_unmeasurable(self):
        """짝도 사유도 없는 새 색 토큰은 **측정 불능**이다 — 기준 위반(1)이 아니다.

        이름을 안 보므로 `--fg-` 밖의 이름도, 다크에만 선언된 것도 걸린다.
        접두어 허용 목록으로 되돌아가면 여기가 빨개진다.
        """
        for where, old in (("라이트", "--line:#e5ddd8;"), ("다크", "--line:#3a2a22;")):
            with self.subTest(where):
                fail, unmeasurable, out = run(
                    self.twist(old, old + "--ring:#abcdef;"))
                self.assertEqual(fail, [], out)
                self.assertEqual(len(unmeasurable), 1, out)
                self.assertIn("--ring", unmeasurable[0])

    def test_nontext_pair_below_three_fails(self):
        """비텍스트 자가 실제로 3.0 이다 — 낮추면 이 미달이 조용히 통과가 된다.

        `#f97316` 은 계획 43 이 고친 옛 라이트 값이고 흰 배경에서 2.80:1 이다.
        """
        fail, unmeasurable, out = run(self.twist("--focus:#ea580c", "--focus:#f97316"))
        self.assertEqual(unmeasurable, [], out)
        self.assertEqual(len(fail), 1, out)
        self.assertIn("--focus/--bg-page", fail[0])
        self.assertIn("< 3.0", fail[0])

    def test_text_pair_keeps_the_four_point_five_floor(self):
        """두 자가 한 루프에 섞였다 — 텍스트가 비텍스트 자로 재지면 여기서 빨개진다.

        `#ea580c` 는 흰 배경에서 3.56:1 이라 3.0 은 넘고 4.5 는 못 넘는다.
        """
        fail, unmeasurable, out = run(self.twist("--fg-muted:#6b6b6b", "--fg-muted:#ea580c"))
        self.assertEqual(unmeasurable, [], out)
        self.assertEqual(len(fail), 1, out)
        self.assertIn("--fg-muted/--bg-page", fail[0])
        self.assertIn("< 4.5", fail[0])

    def test_product_css_reports_the_ring_rule(self):
        """제품 CSS 에서 링을 그리는 규칙이 **읽혀서 화면에 찍힌다.**

        이 줄이 안 찍히면 아래 열아홉 변이가 전부 "우연히" 통과하는 상태로 돌아간 것이다.
        값(2px)은 안 붙든다 — 붙들면 검사기 옆에 옛 값을 하나 더 두는 꼴이 된다.
        """
        fail, unmeasurable, out = run(CSS)
        self.assertEqual((fail, unmeasurable), ([], []), out)
        self.assertIn("포커스 링 규칙 1개 · outline var(--focus) · offset ", out)

    def test_ring_that_is_not_drawn_is_unmeasurable(self):
        """링을 죽이는 변이는 **측정 불능**이다 — 무효가 된 3.56:1 을 안 찍는다.

        계획 44 착수 탐침이 심은 여섯(V1·V2·V3·**V4**·V5·V6)이 **전부 종료 0 으로
        살아남았다**. 그중 V4 는 설계가 천장으로 빼서 여기 없고, **V7 은 탐침이 아니라
        설계가 따로 심어 본 셋(V7·V8·V10) 중 하나다.** 색만 재는 검사기는 그 색이
        아무 데도 안 그려지는 것을 못 본다. 기준 위반(1)이 아니라 측정 불능(2)인
        이유는 설계서 `## 갈림길 A` — 찍은 숫자 자체가 무효가 된다.

        **뒤 셋은 테스트 phase 가 더했다.** 설계는 *"규칙 수 세기 하나에 V7·V8·V10
        셋이 걸린다"* 고 적었는데 개발이 붙든 것은 V7 하나였고, `:focus` 셀렉터 조건은
        설계 첫 문단의 네 조건 중 하나면서 계약의 메시지 갈래에는 없어 개발이 계약
        밖에서 만든 가드다(`history_current.md` 개발 1/1 의 ⓐ) — 셋 다 지워도 나머지
        단언은 전부 초록이었다.
        """
        for name, old, new, expect in (
            ("V1 규칙 통째 삭제", RING_RULE, "", "규칙이 0개"),
            ("V2 outline:none", "outline:3px solid var(--focus)", "outline:none",
             "색 토큰을 안 쓴다"),
            ("V3 다른 토큰을 그린다", "solid var(--focus)", "solid var(--line)",
             "그려지는 색 --line"),
            ("V5 offset 제거", ";\noutline-offset:2px}", "}", "outline-offset"),
            ("V6 offset 0", "outline-offset:2px", "outline-offset:0", "outline-offset"),
            ("V7 뒤 규칙이 덮는다", ".hits{list-style:none",
             "a:focus{outline:none}\n.hits{list-style:none", "규칙이 2개"),
            # 뒤 규칙이 `outline:none` 이 아니라 **폭만** 0 으로 덮는 갈래. OUTLINE_RE 가
            # `outline-width` 를 세는 것이 여기 걸려 있다 — 축약형만 세면 살아남는다.
            ("V8 뒤 규칙이 폭을 0 으로 덮는다", ".hits{list-style:none",
             "a:focus{outline-width:0}\n.hits{list-style:none", "규칙이 2개"),
            # 덮어쓰기가 **at-rule 안**에 있는 갈래. RULE_RE 가 다크 블록 안쪽 규칙을
            # 따로 세지 못하면(바깥 `@media…{` 짝에 먹히면) 규칙은 1개로 보이고 통과한다.
            ("V10 다크 블록 안에서 덮는다", "--focus:#fdba74}}",
             "--focus:#fdba74}\na:focus{outline:none}}", "규칙이 2개"),
            # 규칙도 색도 offset 도 멀쩡한데 **포커스가 아닐 때만** 그린다. 마우스에는
            # 링이 보이고 키보드에는 안 보이므로 색 넷을 다 봐도 안 걸린다.
            ("V11 셀렉터가 포커스용이 아니다", ":focus-visible", ":hover",
             "포커스용이 아니다"),
            # 아래 둘은 계획 49 스텝 1. 셀렉터에 `:focus` 라는 **문자열**은 남는데
            # 링이 그려지는 조건은 키보드 포커스가 아닌 갈래다 — 부분 문자열 가드가
            # 둘 다 통과시켰다(설계서 1절 표 ⓒⓓ, 후보 C 만 종료 2).
            # ⓒ 는 극성이 뒤집혔다: 포커스가 **아닐 때만** 그린다.
            ("ⓒ 셀렉터 :not(:focus-visible)", ":focus-visible",
             ":not(:focus-visible)", "포커스용이 아니다"),
            # ⓓ 는 자식이 받은 포커스라 링이 부모 상자에 그려진다 — 낱말 경계로 가른다.
            ("ⓓ 셀렉터 :focus-within", ":focus-visible", ":focus-within",
             "포커스용이 아니다"),
            # 아래 셋은 **테스트 phase 가 찾은 ⓒⓓ 의 형제 구멍**이다 — 셋 다 종료 0 으로
            # 살아남아 3.56:1 을 찍고 있었다(갭 탐침 실측). 셀렉터에 `:focus-visible` 이
            # 낱말로 남아 있는데 링은 포커스받은 요소에 안 그려지는 갈래라, 조건 5 가
            # `:not(…)` 을 **한 겹만·소문자로만** 지운 것이 그대로 구멍이 됐다.
            # ⓔ 는 ⓒ 를 괄호 한 겹으로 감싼 것뿐이고, ⓕ 는 ⓓ 와 의미가 같고
            # (링이 조상 상자로 간다), ⓖ 는 CSS 가 셀렉터 이름의 대소문자를 안 가린다.
            ("ⓔ 셀렉터 :not(:is(:focus-visible))", ":focus-visible",
             ":not(:is(:focus-visible))", "포커스용이 아니다"),
            ("ⓕ 셀렉터 :has(:focus-visible)", ":focus-visible",
             ":has(:focus-visible)", "포커스용이 아니다"),
            ("ⓖ 셀렉터 대문자 :NOT(:focus-visible)", ":focus-visible",
             ":NOT(:focus-visible)", "포커스용이 아니다"),
            # offset 의 **세 번째** 갈래. 주석은 «없는 것과 0 과 음수는 같은 결과다» 인데
            # 붙들려 있던 것은 앞 둘(V5·V6)뿐이었다. 음수를 거절하는 일은
            # `float(re.match(r"[\d.]*", offset).group() or 0)` 이 `-` 앞에서 빈 문자열을
            # 내는 데 기대고 있다 — 순진한 `float(offset.rstrip("px"))` 로 바뀌면
            # 음수만 조용히 통과한다.
            ("V12 offset 음수", "outline-offset:2px", "outline-offset:-2px",
             "outline-offset"),
            # 아래 넷은 계획 49 스텝 2. 규칙 하나 · 셀렉터 · 색 · offset 이 **전부
            # 멀쩡한데** 링이 at-rule 안에 있어 라이트 화면에 늘 그려지지는 않는다.
            # ⓐⓑ 가 계획서가 죽이러 온 둘이고, F3·F4 는 설계가 실측으로 찾아낸
            # 나머지 둘이다(설계서 1절 표) — **at-rule 의 prelude 를 안 읽는 것**이
            # 후보 C 를 고른 이유라, 「이 조건은 괜찮다」는 화이트리스트가 생기면
            # F3·F4 가 먼저 빨개진다.
            ("ⓐ 다크 @media 안에서만 그린다", RING_RULE,
             "@media(prefers-color-scheme:dark){" + RING_RULE + "}", "at-rule 안에 있다"),
            ("ⓑ @media print 안", RING_RULE,
             "@media print{" + RING_RULE + "}", "at-rule 안에 있다"),
            ("F3 @media (forced-colors:active) 안", RING_RULE,
             "@media (forced-colors:active){" + RING_RULE + "}", "at-rule 안에 있다"),
            ("F4 @layer 안", RING_RULE,
             "@layer base{" + RING_RULE + "}", "at-rule 안에 있다"),
            # 아래 일곱은 계획 52. 셀렉터에 `:focus-visible` 이 **낱말로 남아 있는데**
            # 링은 포커스받은 요소가 아니라 **옆·아래 상자**에 그려지는 갈래다 — 조건 5 가
            # 셀렉터를 한 덩어리로 봐서 「어느 compound 에 붙었나」를 안 읽은 자리다.
            # 앞 넷이 결합자 4종(자손·`>`·`+`·`~`), 다섯째가 공백 낀 `>`,
            # 여섯째가 쉼표 목록(조각 하나만 포커스여도 통과했다),
            # 일곱째는 투명한 `:is()` 안의 포커스 뒤에 결합자가 붙은 것이다.
            ("결합자 자손", ":focus-visible", ":focus-visible .hint",
             "포커스용이 아니다"),
            ("결합자 >", ":focus-visible", ":focus-visible>.hint", "포커스용이 아니다"),
            ("결합자 +", ":focus-visible", ":focus-visible+.hint", "포커스용이 아니다"),
            ("결합자 ~", ":focus-visible", ":focus-visible~.hint", "포커스용이 아니다"),
            ("결합자 > 양옆 공백", ":focus-visible", ":focus-visible > .hint",
             "포커스용이 아니다"),
            ("쉼표 목록의 한 조각만 포커스", ":focus-visible", ":focus-visible,.x",
             "포커스용이 아니다"),
            (":is(…) 안의 포커스 뒤 결합자", ":focus-visible", ":is(:focus-visible) .hint",
             "포커스용이 아니다"),
        ):
            with self.subTest(name):
                fail, unmeasurable, out = run(self.twist(old, new))
                self.assertEqual(fail, [], out)
                self.assertEqual(len(unmeasurable), 1, out)
                self.assertIn(expect, unmeasurable[0])
                # 요점은 판정이 아니라 **안 찍는 것**이다 — 링이 없는데 링의 대비를
                # 화면에 내놓으면 사람이 그 숫자를 근거로 다음 판단을 한다.
                self.assertNotIn("--focus", out)

    def test_transparent_pseudo_classes_still_draw_the_ring(self):
        """조건 5 의 **넓어지는 쪽** 표다 — 아래 넷은 링을 포커스받은 요소에 그대로
        그리는 정상 CSS 라 종료 0 이어야 한다.

        위 변이 표가 「링이 딴 데 그려지면 죽는다」를 붙들고, 이 표가 「그 가름이
        정상 CSS 를 안 잡아먹는다」를 붙든다. `:is()`·`:where()` 는 **투명하다** —
        안의 `:focus-visible` 은 여전히 이 요소가 받는다. 그래서 「괄호가 보이면
        지운다」로 넓히면 앞 둘이 먼저 빨개진다. 셋째는 괄호 **밖**에 남은 포커스가
        살아남는지를 본다(`:not(…)` 을 지우다 뒤까지 먹으면 여기서 걸린다).
        넷째는 CSS 가 셀렉터 이름의 대소문자를 안 가린다는 것이다 — ⓖ 와 짝이라,
        대문자를 그냥 거절하는 쪽으로 닫으면 이 줄이 오탐을 잡아낸다.

        **뒤 여덟은 계획 52 가 더했다** — 위 미탐 표가 「결합자 뒤에 그리면 죽는다」로
        가르는 순간, 그 가름이 **괄호·대괄호 안의 결합자와 쉼표**를 셀렉터의 것으로
        착각하면 정상 CSS 가 종료 2 로 빨개진다(설계서 2절이 세 대안을 가른 여섯 행이
        전부 이쪽이다). `[class~=btn]` 의 `~` 는 결합자가 아니라 속성 연산자고,
        마지막 둘은 가르기 전에 조각을 `strip()` 하지 않으면 마지막 compound 가
        빈 문자열이 되는 자리다(`RULE_RE` 가 여는 중괄호 앞을 통째로 준다).
        """
        for name, old, new in (
            (":is(…) 는 투명하다", ":focus-visible", ":is(:focus-visible)"),
            (":where(…) 도 투명하다", ":focus-visible", ":where(:focus-visible)"),
            ("괄호 밖의 포커스는 남는다", ":focus-visible", ":not(.no-ring):focus-visible"),
            ("대문자도 같은 셀렉터다", ":focus-visible", ":FOCUS-VISIBLE"),
            (":not(…) 안의 결합자", ":focus-visible", ":focus-visible:not(.x + .y)"),
            (":is(…) 안의 결합자", ":focus-visible", ":focus-visible:is(.x + .y)"),
            (":is(…) 안의 쉼표", ":focus-visible", ":is(.x, .y):focus-visible"),
            (":not(…) 안의 쉼표", ":focus-visible", ":focus-visible:not(.x, .y)"),
            (":is(…) 안의 쉼표와 결합자", ":focus-visible", ":is(.x, .y > .z):focus-visible"),
            ("속성 선택자의 ~= 는 결합자가 아니다", ":focus-visible",
             ":focus-visible[class~=btn]"),
            ("앞 compound 도 포커스다", ":focus-visible", ":focus-visible a:focus-visible"),
            ("꼬리 공백", ":focus-visible", ":focus-visible "),
            ("줄바꿈 낀 쉼표", ":focus-visible,.sb", ":focus-visible,\n.sb"),
        ):
            with self.subTest(name):
                fail, unmeasurable, out = run(self.twist(old, new))
                self.assertEqual((fail, unmeasurable), ([], []), out)
                self.assertIn("포커스 링 규칙 1개", out)

    def test_brace_counting_is_not_fooled_by_comments_or_strings(self):
        """조건 6 은 **중괄호를 세서** 링 규칙이 at-rule 밖인지를 본다 — 그 세기의
        함정이 주석과 문자열이다. 정상 CSS 의 아래 다섯 모양은 전부 종료 0 이어야 한다.

        여는 중괄호 하나가 주석 안에 있으면(둘째 줄) 세기가 어긋나 「at-rule 안」이라는
        **거짓 판정**이 난다. `content:"}"` 도 같다. 오탐이 종료 2 라 조용하지는 않지만,
        멈추는 검사기는 안 도는 검사기다 — 진짜 CSS 에 주석 하나 못 적게 된다.

        위 변이 표가 「at-rule 안이면 죽는다」를 붙들고, 이 표가 「그 세기가 CSS 를
        읽을 줄 안다」를 붙든다. 둘 중 하나만 있으면 조건 6 은 반쪽이다.
        """
        for name, old, new in (
            ("주석 안의 중괄호 짝", RING_RULE, "/* 예: a{color:red} */\n" + RING_RULE),
            ("주석 안의 여는 중괄호 하나", RING_RULE, "/* 여는 것 { 하나 */\n" + RING_RULE),
            ("content 문자열 안의 닫는 중괄호", RING_RULE,
             '.hit h2::after{content:"}"}\n' + RING_RULE),
            ("줄바꿈·공백", RING_RULE, "\n\n  " + RING_RULE.replace("{", " {\n  ", 1)),
            ("@media 블록이 링 규칙 뒤에 온다", RING_RULE,
             RING_RULE + "\n@media print{.pager{display:none}}"),
        ):
            with self.subTest(name):
                fail, unmeasurable, out = run(self.twist(old, new))
                self.assertEqual((fail, unmeasurable), ([], []), out)
                self.assertIn("포커스 링 규칙 1개", out)


if __name__ == "__main__":
    unittest.main()
