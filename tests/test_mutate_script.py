"""`scripts/mutate.py` 의 계약 — **판정 술어가 적용기와 같은가.**

2026-11-01 반복 792 에 변이 M8 이 **거짓 생존**을 냈다. 앵커 `if not missing:` 가
`tests/test_docs.py` 에 둘이라 `str.replace(앵커, …, 1)` 이 **남의 함수**를 고쳤고,
남의 함수의 테스트는 그 변경에 무던해 전수가 초록이라 「생존」으로 읽혔다 — 재지 못한
것이 판정으로 둔갑했다. 「생존」은 「테스트가 약하다」로 읽히고 그 판정이 다음 테스트를
더 짜게 만들므로, 틀린 입력이 테스트 설계로 흘러든다.

**이 파일이 무는 것은 「줄을 세지 않는다」다.** 적용은 부분문자열을 바꾸므로 판정도
부분문자열을 세야 한다. `grep -c` 꼴(줄 셈)로는 실물 `tests/test_docs.py` 에서
**`grep -c = 1` 인데 적용기는 둘을 보는 자리가 7개**이고, 그중 하나가 하필
`dup_def_gap` 의 픽스처다(`"class A:\n    def go(self):\n …"` — `go(self):\n` 가
**한 물리 줄 안에 두 번**). 설계 근거는 `docs/design_mutant-anchor-unique.md`.

**실물 핀은 «수» 가 아니라 «관계» 를 못박는다** — 파일이 자라면 수는 움직이므로
`text.count` 와 자의 판정이 **같이** 움직이는지를 본다(`REPORT_NAME` 의 드리프트가
남긴 교훈 · `index.md` 행 수를 리터럴로 박지 않는 것과 같은 이유).
"""
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "mutate.py")
LIVE = os.path.join(ROOT, "tests", "test_docs.py")


def check(path, anchor):
    """`--check` 한 번. `(rc, 마지막 줄, 전체 stdout)`."""
    done = subprocess.run(["python3", SCRIPT, "--check", str(path), anchor],
                          capture_output=True, text=True)
    out = done.stdout.rstrip("\n")
    return done.returncode, out.split("\n")[-1], out


def assert_verdict(case, rc, want, last, out):
    """판정 줄까지 요구한다 — **없는 스크립트도 `rc=2` 를 낸다.**

    TDD 2번에서 실제로 봤다: 자를 쓰기 전에 거부 단언 다섯이 **공짜로 통과**했다
    (`python3` 가 파일을 못 열어 2 로 끝난다). `rc` 만 보는 단언은 「재는 자가
    없는 것」과 「자가 거부한 것」을 못 가른다 — 이 저장소 최다 재발이다.
    """
    case.assertEqual(want, rc, "%s\n%s" % (last, out))
    case.assertTrue(last.startswith("── "), "판정 줄이 없다: %r" % last)
    case.assertIn("rc=%d" % want, last)


class AnchorCountTest(unittest.TestCase):
    """세는 술어 — 부분문자열이지 줄이 아니다."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write(self, text):
        p = pathlib.Path(self.dir.name, "대상.py")
        p.write_text(text, encoding="utf-8")
        return p

    def test_a_unique_anchor_passes(self):
        rc, last, _ = check(self.write("가\n나\n다\n"), "나")
        self.assertEqual(0, rc, last)
        self.assertTrue(last.startswith("── "), last)
        self.assertIn("rc=0", last)

    def test_two_occurrences_on_separate_lines_are_refused(self):
        rc, last, out = check(self.write("가\n나\n가\n"), "가")
        assert_verdict(self, rc, 2, last, out)
        # 걸린 자리를 **모두** 댄다 — 하나만 대면 사람이 다시 찾는다
        self.assertIn("1", out)
        self.assertIn("3", out)

    def test_two_occurrences_on_one_line_are_refused(self):
        """**이 파일의 존재 이유다.** 줄을 세는 판정은 여기서 1 을 돌려준다."""
        rc, last, out = check(self.write("머리\n가가\n꼬리\n"), "가")
        assert_verdict(self, rc, 2, last, out)
        self.assertIn("2", out)

    def test_a_multi_line_anchor_is_counted(self):
        rc, last, out = check(self.write("가\n나\n다\n가\n나\n"), "가\n나\n")
        assert_verdict(self, rc, 2, last, out)

    def test_a_multi_line_anchor_can_be_unique(self):
        rc, last, _ = check(self.write("가\n나\n다\n나\n"), "가\n나\n")
        self.assertEqual(0, rc, last)

    def test_a_missing_anchor_is_refused_with_a_different_message(self):
        """0 과 다수는 **사람이 할 일이 다르다** — 0 은 앵커가 썩었고 다수는 좁혀야 한다."""
        rc0, last0, out0 = check(self.write("가\n나\n"), "없는것")
        rcN, lastN, outN = check(self.write("가\n가\n"), "가")
        assert_verdict(self, rc0, 2, last0, out0)
        assert_verdict(self, rcN, 2, lastN, outN)
        self.assertNotEqual(last0, lastN)

    def test_check_never_writes_the_file(self):
        """거부든 통과든 **한 바이트도** 안 바뀐다 — 판정이 적용보다 먼저 돈다."""
        for text, anchor in (("가\n나\n", "나"), ("가\n가\n", "가"), ("가\n", "없는것")):
            p = self.write(text)
            before = p.read_bytes()
            check(p, anchor)
            self.assertEqual(before, p.read_bytes())

    def test_a_missing_file_is_not_measured_rather_than_passing(self):
        rc, last, out = check(pathlib.Path(self.dir.name, "없는파일.py"), "가")
        assert_verdict(self, rc, 2, last, out)

    def test_too_few_arguments_are_not_measured(self):
        done = subprocess.run(["python3", SCRIPT, "--check"],
                              capture_output=True, text=True)
        out = done.stdout.rstrip("\n")
        assert_verdict(self, done.returncode, 2, out.split("\n")[-1], out)

    def test_the_verdict_survives_tail_one(self):
        """`scripts/verdict.sh` 관례 — `| tail -1` 을 붙여도 판정이 산다."""
        p = self.write("가\n가\n")
        done = subprocess.run(
            "python3 %s --check %s 가 | tail -1" % (SCRIPT, p),
            shell=True, capture_output=True, text=True)
        self.assertIn("rc=2", done.stdout)


class AnchorCountLiveTest(unittest.TestCase):
    """실물 `tests/test_docs.py` 위에서 **적용기와 같이 움직이는가.**

    수를 리터럴로 박지 않는다 — 파일이 자라면 수가 움직이고, 그때 못은 거짓 RED 를
    낸다(`REPORT_NAME` 드리프트의 교훈). 박는 것은 **관계** 다.
    """

    def test_the_verdict_agrees_with_the_applier_on_the_live_file(self):
        text = pathlib.Path(LIVE).read_text(encoding="utf-8")
        for anchor in ("if not missing:", "def scope_touched(root=ROOT):", "zzz없는앵커"):
            want = text.count(anchor)
            rc, last, out = check(LIVE, anchor)
            self.assertEqual(0 if want == 1 else 2, rc,
                             "앵커 %r 는 적용기가 %d 로 센다 — %s" % (anchor, want, last))
            self.assertTrue(last.startswith("── "), "판정 줄이 없다: %r" % last)
            if want != 1:
                self.assertIn(str(want), out, out)

    def test_the_known_duplicate_anchor_is_still_duplicated(self):
        """반복 792 의 M8 을 그대로 다시 부른다 — 이 자가 서기 전에는 「생존」이었다.

        이 앵커가 언젠가 유일해지면 이 테스트는 빨개진다. 그때 할 일은 **다른 중복
        앵커로 바꾸는 것**이고, 그 수가 0 이 되는 날은 이 자가 필요 없어지는 날이다
        (오늘 실측: 중복 종류 158개 · 중복이 차지한 줄 18.3%).
        """
        text = pathlib.Path(LIVE).read_text(encoding="utf-8")
        self.assertGreater(text.count("if not missing:"), 1,
                           "실물 중복 앵커가 사라졌다 — 이 테스트의 앵커를 갈아야 한다")
        rc, last, out = check(LIVE, "if not missing:")
        assert_verdict(self, rc, 2, last, out)


if __name__ == "__main__":
    unittest.main()
