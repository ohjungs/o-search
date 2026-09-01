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

        이 줄이 안 찍히면 아래 아홉 변이가 전부 "우연히" 통과하는 상태로 돌아간 것이다.
        값(2px)은 안 붙든다 — 붙들면 검사기 옆에 옛 값을 하나 더 두는 꼴이 된다.
        """
        fail, unmeasurable, out = run(CSS)
        self.assertEqual((fail, unmeasurable), ([], []), out)
        self.assertIn("포커스 링 규칙 1개 · outline var(--focus) · offset ", out)

    def test_ring_that_is_not_drawn_is_unmeasurable(self):
        """링을 죽이는 변이는 **측정 불능**이다 — 무효가 된 3.56:1 을 안 찍는다.

        계획 44 착수 탐침에서 앞 여섯이 **전부 종료 0 으로 살아남았다**. 색만 재는
        검사기는 그 색이 아무 데도 안 그려지는 것을 못 본다. 기준 위반(1)이 아니라
        측정 불능(2)인 이유는 설계서 `## 갈림길 A` — 찍은 숫자 자체가 무효가 된다.

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
        ):
            with self.subTest(name):
                fail, unmeasurable, out = run(self.twist(old, new))
                self.assertEqual(fail, [], out)
                self.assertEqual(len(unmeasurable), 1, out)
                self.assertIn(expect, unmeasurable[0])
                # 요점은 판정이 아니라 **안 찍는 것**이다 — 링이 없는데 링의 대비를
                # 화면에 내놓으면 사람이 그 숫자를 근거로 다음 판단을 한다.
                self.assertNotIn("--focus", out)


if __name__ == "__main__":
    unittest.main()
