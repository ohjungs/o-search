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


def mutate(path, anchor, replacement, cmd):
    """적용 → 실행 → 복원 한 번. `(rc, 마지막 줄, stdout, stderr)`."""
    done = subprocess.run(["python3", SCRIPT, str(path), anchor, replacement, "--"] + cmd,
                          capture_output=True, text=True)
    out = done.stdout.rstrip("\n")
    return done.returncode, out.split("\n")[-1], out, done.stderr


class MutateApplyTest(unittest.TestCase):
    """적용·실행·복원 — **복원은 데이터 안전이라 사다리로 타협하지 않는다.**

    `git restore` 를 부르지 않는다: `rules/plan.md` 3-1절이 「`restore .` 를 쓰면 남의
    미커밋 변경까지 날아간다」고 적은 자리이고, 변이는 **작업 중인 트리**에서 돈다.
    원본 바이트를 들고 있다가 되쓰는 것이 설계 계약 4번이다.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.target = pathlib.Path(self.dir.name, "대상.py")
        self.target.write_text("머리\n앵커\n꼬리\n", encoding="utf-8")
        self.marker = pathlib.Path(self.dir.name, "본것.txt")

    def seeing(self, rc):
        """대상 파일을 **실행 시점에** 베껴 두고 주어진 코드로 끝나는 명령."""
        return ["python3", "-c",
                "import pathlib,sys;p,m,r=sys.argv[1:4];"
                "pathlib.Path(m).write_text(pathlib.Path(p).read_text());"
                "sys.exit(int(r))",
                str(self.target), str(self.marker), str(rc)]

    def test_a_dying_mutant_is_zero(self):
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.seeing(1))
        self.assertEqual(0, rc, "%s\n%s" % (last, out))
        self.assertIn("rc=0", last)

    def test_a_surviving_mutant_is_one(self):
        """**생존은 기준 위반이다** — 「이 자리를 무는 테스트가 없다」가 그 뜻이다."""
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.seeing(0))
        self.assertEqual(1, rc, "%s\n%s" % (last, out))
        self.assertIn("rc=1", last)

    def test_survival_and_refusal_never_share_an_exit_code(self):
        """이 계획이 닫는 병이 **종료 코드 쪽에서 되살아나는 것**을 막는다."""
        survived, _, _, _ = mutate(self.target, "앵커", "변이", self.seeing(0))
        refused, _, _, _ = mutate(self.target, "없는앵커", "변이", self.seeing(0))
        self.assertEqual(1, survived)
        self.assertEqual(2, refused)

    def test_the_command_sees_the_mutated_file(self):
        mutate(self.target, "앵커", "변이", self.seeing(1))
        self.assertEqual("머리\n변이\n꼬리\n", self.marker.read_text(encoding="utf-8"))

    def test_the_file_is_restored_byte_for_byte(self):
        before = self.target.read_bytes()
        for cmd_rc in (0, 1):
            mutate(self.target, "앵커", "변이", self.seeing(cmd_rc))
            self.assertEqual(before, self.target.read_bytes())

    def test_a_refused_anchor_never_runs_the_command(self):
        """거부면 명령을 **안 돌린다** — 돌리면 재지 못한 것으로 판정을 만든다."""
        self.target.write_text("앵커\n앵커\n", encoding="utf-8")
        before = self.target.read_bytes()
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.seeing(1))
        self.assertEqual(2, rc, "%s\n%s" % (last, out))
        self.assertFalse(self.marker.exists(), "거부했는데 명령이 돌았다")
        self.assertEqual(before, self.target.read_bytes())

    def test_a_failed_restore_shouts_and_is_not_measured(self):
        """복원 실패를 **조용히 끝내지 않는다** — 더러운 트리를 0 으로 끝내는 길이 없다."""
        self.addCleanup(lambda: self.target.chmod(0o644))
        block_writes = ["python3", "-c",
                    "import os,sys;os.chmod(sys.argv[1], 0o444);sys.exit(1)",
                    str(self.target)]
        rc, last, out, err = mutate(self.target, "앵커", "변이", block_writes)
        self.assertEqual(2, rc, "%s\n%s" % (last, out))
        self.assertTrue(err.strip(), "stderr 가 조용하다")
        self.assertIn("rc=2", last)
        # 되쓰지 못했으니 변이가 남아 있다 — 그 사실을 자가 말했는지가 이 테스트다
        self.assertIn("변이", self.target.read_text(encoding="utf-8"))

    def test_the_verdict_is_the_last_line(self):
        for cmd_rc in (0, 1):
            _, last, _, _ = mutate(self.target, "앵커", "변이", self.seeing(cmd_rc))
            self.assertTrue(last.startswith("── "), last)

    def test_a_missing_separator_is_not_measured(self):
        done = subprocess.run(["python3", SCRIPT, str(self.target), "앵커", "변이",
                               "python3", "-c", "pass"],
                              capture_output=True, text=True)
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertTrue(done.stdout.rstrip("\n").split("\n")[-1].startswith("── "))

    def test_an_empty_command_is_not_measured(self):
        rc, last, _, _ = mutate(self.target, "앵커", "변이", [])
        self.assertEqual(2, rc, last)
        self.assertTrue(last.startswith("── "), last)


if __name__ == "__main__":
    unittest.main()
