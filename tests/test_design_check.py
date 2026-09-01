"""검사기 `e2e/design_check.py` 의 3번 축(대비)이 **무엇을 어느 자로 재는지**를 고정한다.

계획 43 이 넣은 셋 — 비텍스트 자(3.0) · 포커스 링 짝 · 뒤집은 커버리지 강제 — 은
전부 e2e 파일 안에 있고, 그 파일은 제품 CSS 가 통과하는 한 종료 0 이다. 그래서
**비텍스트 축을 통째로 지워도, `NO_PAIR` 에 `--focus` 를 몰래 넣어도 종료 0 이다.**
린트형 검사는 자기를 붙드는 단언이 없으면 조용히 죽는다 — `token_maps` 의 다크 블록
가드가 그것 때문에 생겼고(그 파일 첫머리), 계획 42 리뷰가 같은 형태를 한 번 더 짚었다.
여기 있는 것이 그 단언이다.

**제품 색값은 여기 적지 않는다**(`design_focus-contrast.md ## 계약`) — 검사기 옆에
값을 따로 들면 색을 고쳐도 옛 값으로 통과를 내준다. 붙드는 것은 **어느 자로 재는가**다.
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
        lines = [ln for ln in out.splitlines() if "--focus" in ln]
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


if __name__ == "__main__":
    unittest.main()
