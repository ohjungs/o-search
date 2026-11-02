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
**한 물리 줄 안에 두 번**). 설계 근거는 `docs/design_history_099.md`.

**실물 핀은 «수» 가 아니라 «관계» 를 못박는다** — 파일이 자라면 수는 움직이므로
`text.count` 와 자의 판정이 **같이** 움직이는지를 본다(`REPORT_NAME` 의 드리프트가
남긴 교훈 · `index.md` 행 수를 리터럴로 박지 않는 것과 같은 이유).
"""
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "mutate.py")
LIVE = os.path.join(ROOT, "tests", "test_docs.py")


def check(path, anchor):
    """`--check` 한 번. `(rc, 마지막 줄, 전체 stdout)`."""
    done = subprocess.run([sys.executable, SCRIPT, "--check", str(path), anchor],
                          capture_output=True, text=True)
    out = done.stdout.rstrip("\n")
    return done.returncode, out.split("\n")[-1], out


def read_live():
    """실물 대조는 **적용기와 같은 읽기**로 한다 — `read_exact` 와 짝이다."""
    return pathlib.Path(LIVE).read_bytes().decode("utf-8")


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
        # 같은 줄을 두 번 찍지 않고 **몇 회인지** 댄다(백지 패스의 자잘 지적).
        self.assertIn("(2회)", out)

    def test_a_multi_line_anchor_is_counted(self):
        rc, last, out = check(self.write("가\n나\n다\n가\n나\n"), "가\n나\n")
        assert_verdict(self, rc, 2, last, out)

    def test_a_multi_line_anchor_can_be_unique(self):
        rc, last, _ = check(self.write("가\n나\n다\n나\n"), "가\n나\n")
        self.assertEqual(0, rc, last)

    def test_a_missing_anchor_is_refused_with_a_different_message(self):
        """0 과 다수는 **사람이 할 일이 다르다** — 0 은 다시 뜨고 다수는 넓힌다.

        **수가 다른 것으로는 안 된다** — 변이 M3(0건 분기 삭제)이 그 단언에서
        살아남았다. 0건이 다수 분기로 흘러도 「앵커 0곳」이라 문구가 달라지므로
        `assertNotEqual` 은 조용하다. 가르는 것은 **처방 낱말**이라 그것을 단언한다
        (`[R127-2]` 「실패 메시지가 한 부류 전용 처방을 달고 있었다」와 같은 자리 —
        썩은 앵커에 「넓혀라」는 **틀린 방향**이다).
        """
        rc0, last0, out0 = check(self.write("가\n나\n"), "없는것")
        rcN, lastN, outN = check(self.write("가\n가\n"), "가")
        assert_verdict(self, rc0, 2, last0, out0)
        assert_verdict(self, rcN, 2, lastN, outN)
        self.assertIn("썩었다", last0)
        self.assertNotIn("넓혀", last0)
        self.assertIn("넓혀", lastN)

    def test_overlapping_occurrences_are_counted_like_str_count(self):
        """**설계 계약 1번** — 세는 수가 `str.count` 와 같아야 한다.

        `"aaa".count("aa")` 는 **1** 이고 적용기(`str.replace`)도 한 번만 바꾼다.
        보폭을 1 로 두면 둘로 세어 **적용기와 갈린다** — 변이 M1 이 그 자리에서
        살아남아 이 테스트가 생겼다. 갈리는 판정은 이 자가 닫으려는 사고의 새 통로다.
        """
        text = "가가가\n"
        self.assertEqual(1, text.count("가가"), "전제가 깨졌다")
        rc, last, _ = check(self.write(text), "가가")
        self.assertEqual(0, rc, last)

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
        done = subprocess.run([sys.executable, SCRIPT, "--check"],
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
        """앵커 셋 중 첫째가 **반복 792 의 M8 그대로**다 — 그때는 「생존」이었다.

        그 앵커가 언젠가 유일해지면 `assertGreater` 가 빨개진다. 그때 할 일은
        **다른 중복 앵커로 가는 것**이고, 실물 중복이 0 이 되는 날은 이 자가 필요
        없어지는 날이다(2026-11-02 실측: 중복 종류 158개 · 중복이 든 줄 18.3%).
        """
        text = read_live()
        self.assertGreater(text.count("if not missing:"), 1,
                           "실물 중복 앵커가 사라졌다 — 이 테스트의 앵커를 갈아야 한다")
        for anchor in ("if not missing:", "def scope_touched(root=ROOT):", "zzz없는앵커"):
            want = text.count(anchor)
            rc, last, out = check(LIVE, anchor)
            self.assertEqual(0 if want == 1 else 2, rc,
                             "앵커 %r 는 적용기가 %d 로 센다 — %s" % (anchor, want, last))
            self.assertTrue(last.startswith("── "), "판정 줄이 없다: %r" % last)
            if want != 1:
                self.assertIn(str(want), out, out)


def mutate(path, anchor, replacement, cmd):
    """적용 → 실행 → 복원 한 번. `(rc, 마지막 줄, stdout, stderr)`."""
    done = subprocess.run([sys.executable, SCRIPT, str(path), anchor, replacement, "--"] + cmd,
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
        self.tally = pathlib.Path(self.dir.name, "판수.txt")

    def seeing(self, rc):
        """대상 파일을 **실행 시점에** 베껴 두고 주어진 코드로 끝나는 명령."""
        return [sys.executable, "-c",
                "import pathlib,sys;p,m,r=sys.argv[1:4];"
                "pathlib.Path(m).write_text(pathlib.Path(p).read_text());"
                "sys.exit(int(r))",
                str(self.target), str(self.marker), str(rc)]

    def test_a_dying_mutant_is_zero(self):
        """**픽스처를 고쳤다 — 옛 것(`seeing(1)`)은 더 이상 죽음이 아니다.**

        무조건 실패하는 명령은 이 계획이 닫는 **거짓 죽음 그 자체**라서 무해 대조판
        에서도 빨갛고 `2` 로 떨어진다. 즉 이 저장소의 「죽음」 픽스처가 **그 구멍을
        스스로 품고 있었다.** 죽음은 「원본에서 초록이고 변이에서만 빨강」이다.
        """
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.biting("변이"))
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

    def biting(self, needle):
        """대상 파일에 `needle` 이 **있을 때만** 실패하는 명령. 판 수를 센다.

        **`seeing(1)` 은 더 이상 「죽음」을 흉낼 수 없다** — 무조건 실패하는 명령은
        이 계획이 닫는 **거짓 죽음 그 자체**라서 무해 대조판에서도 빨갛고 `2` 로
        떨어진다. 죽음은 「원본에서 초록이고 변이에서만 빨강」이다.

        `needle=""` 로 부르면 `"" in s` 가 늘 참이라 **무조건 실패**가 된다 —
        옛 픽스처를 한 helper 로 함께 든다.
        """
        return [sys.executable, "-c",
                "import pathlib,sys;p,m,t,n=sys.argv[1:5];"
                "s=pathlib.Path(p).read_text();"
                "pathlib.Path(m).write_text(s);"
                "f=pathlib.Path(t);f.write_text((f.read_text() if f.exists() else '')+'x');"
                "sys.exit(1 if n in s else 0)",
                str(self.target), str(self.marker), str(self.tally), needle]

    def touchy(self, original):
        """**건드린 것만으로** 빨개지는 명령 — `tests/test_docs.py` 의 `ScopeTest` 흉내다.

        원본과 바이트가 같으면 초록, 한 바이트라도 다르면 빨강이다. 그 자가 읽는 것이
        `git diff --name-only` 의 **파일 집합**이라 **무엇으로 바꿨는지와 무관**한 것과
        같은 성질이다. **이 꼴이 ㉡(심기 전 베이스라인)으로 못 잡히는 자리다** —
        건드리기 전에는 초록이라 베이스라인 검사를 통과한 뒤 「죽음」이 난다.
        """
        return [sys.executable, "-c",
                "import pathlib,sys;p,t,o=sys.argv[1:4];"
                "f=pathlib.Path(t);f.write_text((f.read_text() if f.exists() else '')+'x');"
                "sys.exit(0 if pathlib.Path(p).read_bytes()==o.encode('utf-8') else 1)",
                str(self.target), str(self.tally), original]

    def runs(self):
        """대조판을 넣은 뒤 명령이 **몇 판** 돌았나."""
        return len(self.tally.read_text(encoding="utf-8")) if self.tally.exists() else 0

    def test_a_command_red_on_any_touch_is_not_measured(self):
        """**이 계획의 머리** — 2026-11-03 반복 805 가 실물로 재현한 거짓 죽음이다.

        칸 밖 파일에 docstring 산문 한 낱말을 더하고 전수를 돌리니 `ScopeTest` 가
        빨개져 `── 변이 **죽음** … rc=0` 이 났다(실측 · 역추적으로 범인 확정).
        뜻이 없는 변경인데 「이 자리를 무는 테스트가 있다」로 읽혔다.
        """
        original = self.target.read_text(encoding="utf-8")
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.touchy(original))
        assert_verdict(self, rc, 2, last, out)
        self.assertIn("건드린 것만으로", last)
        self.assertNotIn("죽음", last, "거짓 죽음을 죽음과 같은 말로 적었다")

    def test_a_command_red_without_the_mutation_is_not_measured(self):
        """㉡ 이 닫으려던 **일반형**도 같은 분기가 닫는다 — 이미 빨간 명령·오타·누락."""
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.biting(""))
        assert_verdict(self, rc, 2, last, out)

    def test_death_and_touch_blindness_never_share_an_exit_code(self):
        """「죽음」과 「건드림 때문이었다」가 **같은 코드로 나오는 길이 없다.**

        `test_survival_and_refusal_never_share_an_exit_code` 와 같은 벽이고,
        이 계획은 그것을 판정의 **반대쪽**에 세운다.
        """
        original = self.target.read_text(encoding="utf-8")
        died, _, _, _ = mutate(self.target, "앵커", "변이", self.biting("변이"))
        blind, _, _, _ = mutate(self.target, "앵커", "변이", self.touchy(original))
        self.assertEqual(0, died)
        self.assertEqual(2, blind)

    def test_the_refusal_names_both_ways_out(self):
        """거부 문구가 **할 일을 말하는가** — 이 저장소 최다 재발의 반대쪽이다.

        `[R131-2]` 계열의 사고는 「실패 메시지가 틀린 방향을 알려준다」였다. 「건드린
        것만으로 빨갛다」는 관찰만으로는 호출자가 할 일을 모른다 — 길이 둘뿐이고
        (㉠ 대상 모듈만 돌린다 · 칸에 그 파일을 적는다) 설계가 그 둘을 명시했다.
        문구가 흐려지면 자는 조용히 쓸모를 잃는다.

        **실물 합성으로는 안 잰다** — 「칸 밖 추적 파일을 변이하면 전수가 빨개진다」를
        단위 스위트 안에서 재려면 **추적되는 파일을 건드려야** 한다(2026-11-03 반복 807
        이 손으로 실측했다: 같은 판이 반복 805 엔 `rc=0` 죽음 · 지금은 `rc=2`).
        그것을 전수 안에 두면 매 실행이 트리를 흔들고 테스트 순서에 기대게 된다 —
        데이터 안전이라 사다리로 타협하지 않는다(`rules/dev.md` 2절). 실물 합성은
        e2e phase 가 `docs/e2e/mutant-baseline-red/result.md` 에서 잰다.
        """
        original = self.target.read_text(encoding="utf-8")
        _, last, _, _ = mutate(self.target, "앵커", "변이", self.touchy(original))
        self.assertIn("대상 모듈만", last)
        self.assertIn("칸에 그 파일을 적는다", last)

    def test_the_control_does_not_run_when_the_mutant_survives(self):
        """**생존 경로의 비용은 0 이다** — 설계 계약 2번.

        생존은 「변이를 심은 채로 초록이 났다」이고, 그것이 이미 「이 파일을 건드리는
        것은 빨강을 만들지 않는다」의 증명이라 대조판이 필요 없다.
        """
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.biting("없는것"))
        assert_verdict(self, rc, 1, last, out)
        self.assertEqual(1, self.runs(), "생존인데 대조판이 돌았다")

    def test_the_control_runs_once_on_death(self):
        """죽음일 때만 **한 판** 더 돈다 — 두 판도 세 판도 아니다."""
        rc, last, out, _ = mutate(self.target, "앵커", "변이", self.biting("변이"))
        assert_verdict(self, rc, 0, last, out)
        self.assertEqual(2, self.runs())

    def test_the_file_is_restored_after_the_control_run(self):
        """쓰기 주기가 둘이 됐어도 **복원 계약은 안 깨진다** — 설계 계약 4번."""
        before = self.target.read_bytes()
        original = self.target.read_text(encoding="utf-8")
        for cmd in (self.biting("변이"), self.touchy(original), self.biting("")):
            mutate(self.target, "앵커", "변이", cmd)
            self.assertEqual(before, self.target.read_bytes())

    def test_the_command_sees_the_mutated_file(self):
        """**생존 경로로 잰다** — 죽음이면 대조판이 `marker` 를 원본으로 덮는다."""
        mutate(self.target, "앵커", "변이", self.seeing(0))
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

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0,
                     "root 는 0444 에도 쓸 수 있어 이 축을 못 재운다")
    def test_a_failed_restore_shouts_and_is_not_measured(self):
        """복원 실패를 **조용히 끝내지 않는다** — 더러운 트리를 0 으로 끝내는 길이 없다.

        `chmod 0444` 가 **소유자** 쓰기를 막는다는 전제 위에 서 있다 — root 로 돌리면
        그 전제가 거짓이라 거짓 빨강이 난다(백지 패스의 자잘 지적 · 컨테이너 CI).
        건너뛴 수는 출력에 보이므로 조용히 사라지지 않는다.
        """
        self.addCleanup(lambda: self.target.chmod(0o644))
        block_writes = [sys.executable, "-c",
                    "import os,sys;os.chmod(sys.argv[1], 0o444);sys.exit(1)",
                    str(self.target)]
        rc, last, out, err = mutate(self.target, "앵커", "변이", block_writes)
        self.assertEqual(2, rc, "%s\n%s" % (last, out))
        self.assertTrue(err.strip(), "stderr 가 조용하다")
        self.assertIn("rc=2", last)
        # 되쓰지 못했으니 변이가 남아 있다 — 그 사실을 자가 말했는지가 이 테스트다
        self.assertIn("변이", self.target.read_text(encoding="utf-8"))

    def test_an_unplanted_mutation_is_not_a_verdict(self):
        """**이 저장소가 손으로 쓰던 규약이 여기 있다** — 백지 패스가 잡았다.

        `docs/plan_history_037.md:151` 「모든 변이는 심기 전에 `mutated != original`
        로 **실제로 심어진 것을 먼저 단언**한다」(`plan_history_035.md:145` 도 같다).
        손버릇을 기제로 옮기면서 **그 단언만 빠졌고**, 치환이 앵커와 같으면 아무것도
        안 심긴 채 명령이 돌아 「생존 … 이것은 판정이다」가 났다(실측 `rc=1`).
        """
        before = self.target.read_bytes()
        rc, last, out, _ = mutate(self.target, "앵커", "앵커", self.seeing(0))
        assert_verdict(self, rc, 2, last, out)
        self.assertIn("심기지 않았다", last)
        self.assertFalse(self.marker.exists(), "안 심겼는데 명령이 돌았다")
        self.assertEqual(before, self.target.read_bytes())

    def test_the_judge_reads_the_same_bytes_the_applier_writes(self):
        """**설계 계약 1번의 뿌리** — `read_text` 는 CRLF 를 LF 로 바꿔 둘을 가른다.

        백지 패스 실측: CRLF 파일 + 여러 줄 앵커에서 `--check` 는 「앵커 유일」인데
        적용기는 **0곳**을 바꾸고 명령이 **원본**을 보고 「생존 … 판정이다」가 났다.
        읽는 자리를 `read_exact` 하나로 모아 뿌리에서 닫았다.
        """
        크알프 = pathlib.Path(self.dir.name, "크알프.py")
        크알프.write_bytes("머리\r\n앵커\r\n꼬리\r\n".encode("utf-8"))
        rc, last, out = check(크알프, "머리\n앵커")
        assert_verdict(self, rc, 2, last, out)
        rc2, last2, out2, _ = mutate(크알프, "머리\n앵커", "변이", self.seeing(0))
        assert_verdict(self, rc2, 2, last2, out2)

    def test_a_non_utf8_file_is_not_measured_rather_than_surviving(self):
        """역추적으로 새면 `rc=1` 이고 그것은 **생존 코드**다 — 바닥 그물이 받는다."""
        나쁜 = pathlib.Path(self.dir.name, "나쁜.py")
        나쁜.write_bytes(b"\xff\xfe\xff")
        rc, last, out = check(나쁜, "가")
        assert_verdict(self, rc, 2, last, out)

    @unittest.skipIf(not hasattr(signal, "SIGTERM"), "신호가 없는 플랫폼")
    def test_a_signal_restores_the_file_and_does_not_pass(self):
        """**docstring 이 한 약속이 뚫리던 자리다** — 실측 `rc=143` · 변이가 남고 조용.

        기본 처리기는 `finally` 를 안 돌린다. `scripts/verdict.sh` 가 같은 사고를
        `trap 'stopped 143' TERM` 으로 막고 그 주석에 「막으려던 사고를 정리 코드가
        **새 경로로 재현**했다」를 적어 뒀다 — 사다리 2번이 가리킨 선례다.
        """
        before = self.target.read_bytes()
        child = subprocess.Popen(
            [sys.executable, SCRIPT, str(self.target), "앵커", "변이", "--",
             sys.executable, "-c", "import time;time.sleep(30)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 10
        while self.target.read_bytes() == before and time.time() < deadline:
            time.sleep(0.05)
        self.assertNotEqual(before, self.target.read_bytes(), "변이가 안 심겼다")
        child.send_signal(signal.SIGTERM)
        out, _ = child.communicate(timeout=30)
        last = out.rstrip("\n").split("\n")[-1]
        self.assertEqual(2, child.returncode, out)
        self.assertTrue(last.startswith("── "), last)
        self.assertEqual(before, self.target.read_bytes(), "변이가 파일에 남았다")

    def test_the_verdict_is_the_last_line(self):
        for cmd_rc in (0, 1):
            _, last, _, _ = mutate(self.target, "앵커", "변이", self.seeing(cmd_rc))
            self.assertTrue(last.startswith("── "), last)

    def test_a_missing_separator_is_refused_at_parse_time(self):
        """`--` 가 없으면 **인자를 읽는 자리에서** 거부한다.

        **`rc=2` 만 재면 안 된다** — 변이 M10(`--` 검사 삭제)이 거기서 살아남았다.
        검사를 빼면 `argv[5:]` 가 명령으로 읽혀 `["-c", "pass"]` 를 돌리려다 **실패해서**
        2 가 나온다. 즉 그 2 는 거부가 아니라 사고다. 더 나쁜 꼴도 실재한다 —
        `mutate.py <파일> <앵커> <치환> 쓰레기 ls` 는 「쓰레기」를 조용히 삼키고 `ls`
        를 돌려 **판정(0/1)을 낸다.** 이 계획이 닫는 병(재지 못한 것이 판정으로
        둔갑한다)과 같은 것이라 **문구로 못박는다.**
        """
        for 꼬리 in ([sys.executable, "-c", "pass"], ["쓰레기", "true"]):
            done = subprocess.run([sys.executable, SCRIPT, str(self.target), "앵커", "변이"]
                                  + 꼬리, capture_output=True, text=True)
            last = done.stdout.rstrip("\n").split("\n")[-1]
            self.assertEqual(2, done.returncode, done.stdout)
            self.assertTrue(last.startswith("── "), last)
            self.assertIn("인자", last)
            self.assertFalse(self.marker.exists(), "거부했는데 명령이 돌았다")

    def test_an_empty_command_is_not_measured(self):
        rc, last, _, _ = mutate(self.target, "앵커", "변이", [])
        self.assertEqual(2, rc, last)
        self.assertTrue(last.startswith("── "), last)


if __name__ == "__main__":
    unittest.main()
