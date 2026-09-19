"""`scripts/verdict.sh` 가 **판정을 마지막 줄로** 옮기는지 실제로 돌려서 본다.

`digest.md ## 반복 실패` 최다 항목(「러너의 판정 줄을 가린다」 **35회**)이 이 파일이
존재하는 이유다. 막으려는 시도 셋이 전부 문장이었고 셋 다 뚫렸다 — 조항, 조항 조이기,
「러너를 파이프 왼쪽에 두지 않는다」. 항목 자신의 결론이 「문장은 소진됐다」다.

**사라지는 것이 셋이고 원인이 다르다**(2026-09-19 반복 625 실측 · `design_verdict-last.md`):

1. `Ran/OK` 줄 — 판정은 stderr(**무버퍼**)인데 테스트 stdout 은 파이프 아래 **블록
   버퍼**라 프로세스가 끝날 때 한꺼번에 밀려 나온다. **순서가 뒤집혀** 판정이 위로
   밀려난다. `-b` 는 이 중 **초록 절반만** 덮는다 — 실패한 테스트의 출력은 안 삼키므로
   **빨간 날 정확히 눈이 먼다.**
2. 판정 전부 — `2>/dev/null`. 판정이 stderr 라 재지향이 통째로 버린다.
3. `rc` — 파이프 오른쪽 명령의 종료 코드가 `$?` 가 된다. **출력 길이와 무관한 파이프
   그 자체의 성질**이다.

그래서 이 자는 **소스를 읽지 않고 실제로 실행한다.** 계약이 「이렇게 쓰여 있다」가
아니라 「이렇게 **동작한다**」라서다 — 낱말을 세는 가드로는 ③을 영영 못 잰다.

가짜 러너를 쓰는 이유는 진짜 전수를 부르면 **전수 안에서 전수가 도는** 모양이 되기
때문이다(계획 101 이 같은 자리에서 피한 길). 재는 것은 래퍼지 러너가 아니다.

ponytail: zsh 전용이다. 이 저장소의 유일한 쉘 스크립트가 이미 zsh 고, `bash` 분기를
두면 **아무 테스트에도 안 걸리는 코드**가 된다.
"""

import os
import pathlib
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts" / "verdict.sh"

# 가짜 러너 — 실패한 전수의 모양이다. stdout 이 길고, 판정은 stderr 고, 종료 코드가 1 이다.
# 200줄인 이유: 실제 위반 표본이 `tail -3`~`tail -40` 이라 그 전부를 넘겨야 순서 역전이
# **관찰 가능**해진다. 적게 잡으면 「운으로 살아남는」 대조군을 재게 된다(반복 625 실측).
NOISE_LINES = 200
FAKE_RUNNER = """\
import sys
for i in range(%d):
    print("crawl log %%d" %% i)
sys.stderr.write("Ran 812 tests in 25.0s\\n\\nFAILED (failures=3)\\n")
sys.exit(1)
""" % NOISE_LINES


def run_zsh(command, cwd):
    """`zsh -c` 로 한 줄을 돌리고 `(stdout, rc)`. `communicate()` 로 자식을 걷는다."""
    done = subprocess.run(
        ["/bin/zsh", "-c", command], cwd=str(cwd),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return done.stdout, done.returncode


class VerdictLastTest(unittest.TestCase):
    """계약 넷을 하나씩 친다 (`design_verdict-last.md` 「계약」 절)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fake = pathlib.Path(self.tmp.name) / "fake_runner.py"
        self.fake.write_text(FAKE_RUNNER, encoding="utf-8")
        self.call = '%s python3 %s' % (WRAPPER, self.fake)

    def assert_verdict(self, shape, out):
        """마지막 줄 하나에 `Ran`·`FAILED`·`rc=1` 이 다 있나."""
        last = out.strip().split("\n")[-1] if out.strip() else ""
        for token in ("Ran 812 tests", "FAILED (failures=3)", "rc=1"):
            self.assertIn(token, last,
                          "%s 아래에서 마지막 줄이 판정을 안 실었다 — 읽힌 마지막 줄은 %r 다."
                          " 계약 1: `tail -1` 로 잘라도 `Ran`·`OK|FAILED`·`rc` 셋이 다 있어야"
                          " 한다 (`design_verdict-last.md`)" % (shape, last))

    def test_verdict_survives_a_pipe(self):
        """손실 ① — stdout 이 블록 버퍼로 밀려 나와도 판정이 마지막이다."""
        out, _ = run_zsh("%s | tail -1" % self.call, ROOT)
        self.assert_verdict("`| tail -1`", out)

    def test_verdict_survives_dropping_stderr(self):
        """손실 ② — 판정을 stdout 으로 찍으므로 `2>/dev/null` 이 못 버린다."""
        out, _ = run_zsh("%s 2>/dev/null | tail -1" % self.call, ROOT)
        self.assert_verdict("`2>/dev/null | tail -1`", out)

    def test_rc_is_the_wrapped_command_not_the_pipe(self):
        """손실 ③ — 파이프 아래에서도 `rc=1` 이 **글자로** 남는다.

        여기가 이 파일의 중심이다. `rc` 는 파이프가 먹으면 되살릴 길이 없으므로
        **숫자를 출력에 실어 보내는 것**이 유일한 처방이다. 래퍼가 `tee` 의 종료
        코드를 실으면 `rc=0` 이 되어 **실패가 통과로 보인다** — 막으려는 그 사고다.
        """
        out, _ = run_zsh("%s 2>&1 | tail -3" % self.call, ROOT)
        self.assertIn("rc=1", out,
                      "파이프 아래에서 `rc=1` 이 안 보인다 — 래퍼가 `tee` 의 종료 코드를"
                      " 실었으면 `rc=0` 이다. 계약 2 (`design_verdict-last.md`). 읽힌 것: %r"
                      % (out[-200:],))

    def test_bare_exit_code_is_preserved(self):
        """계약 3 — 파이프 없이 쓰면 래퍼 자신의 종료 코드도 감싼 명령의 것이다."""
        _, rc = run_zsh(self.call, ROOT)
        self.assertEqual(1, rc, "맨몸 호출의 종료 코드가 감싼 명령의 것이 아니다")

    def test_output_is_not_reduced(self):
        """계약 4 — 원래 출력을 **안 줄인다.**

        ⑳ 이 도달한 지점이다: 방아쇠 「출력이 길다」의 나머지 절반은 **「빨간 쪽이
        길다」**이고 그건 줄이면 안 되는 쪽이다. 이 설계가 바꾸는 것은 길이가 아니라
        순서다 — 요약하는 래퍼를 만들면 이 자가 막으려던 것을 자기가 한다.
        """
        out, _ = run_zsh(self.call, ROOT)
        kept = sum(1 for ln in out.split("\n") if ln.startswith("crawl log "))
        self.assertEqual(NOISE_LINES, kept,
                         "래퍼가 원래 출력을 줄였다 — %d줄 중 %d줄만 남았다" % (NOISE_LINES, kept))

    def test_the_fake_runner_actually_makes_the_problem(self):
        """**0 을 세면서 통과하지 않는다** — 가짜 러너가 진짜로 그 모양인지 먼저 본다.

        래퍼 **없이** 같은 파이프를 태우면 판정이 실제로 사라져야 한다. 안 사라지면
        위 넷은 「고쳐서 통과」가 아니라 **애초에 깨진 적 없는 것을 잰 것**이다.
        """
        out, _ = run_zsh("python3 %s 2>&1 | tail -3" % self.fake, ROOT)
        self.assertNotIn("Ran 812 tests", out,
                         "가짜 러너가 순서 역전을 재현하지 못했다 — 이 파일이 재는 사고가"
                         " 이 기계에서 안 난다는 뜻이라, 위 단언들은 증거가 아니다. 읽힌 것: %r"
                         % (out,))


class VerdictGapTest(unittest.TestCase):
    """테스트 phase 갭 탐색(`rules/test.md` 3절)이 찾은 것들.

    **점수 8 미만도 넣었다.** 규칙은 「8 이상만 이번 스텝」인데, 이 파일이 재는 것은
    제품이 아니라 **재는 자 자신**이라 기준을 낮췄다 — 여기가 조용히 틀리면 이 저장소의
    모든 판정이 함께 틀린다. 각 4줄이라 비용도 그 값을 안 넘는다.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def fake(self, body):
        path = pathlib.Path(self.tmp.name) / "runner.py"
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_green_run_also_ends_with_the_verdict(self):
        """**갭 ⑥ · 8점** — 위의 넷은 전부 **빨간** 러너로만 쟀다.

        실제 실행의 대부분은 초록이고, `rc=0` 경로는 단 한 줄도 안 밟히고 있었다.
        `exit $rc` 가 초록에서 틀리면 **통과가 실패로 보이고**, 그건 밤을 통째로 세운다.
        """
        runner = self.fake("import sys\nsys.stderr.write('Ran 3 tests in 0.1s\\n\\nOK\\n')\n")
        out, _ = run_zsh("%s python3 %s | tail -1" % (WRAPPER, runner), ROOT)
        self.assertIn("Ran 3 tests", out)
        self.assertIn("OK", out)
        self.assertIn("rc=0", out)
        # 파이프 아래의 rc 는 `tail` 의 것이라 **늘 0 이다** — 단언해도 못 깨진다(리뷰 지적).
        # 래퍼 자신의 종료 코드는 파이프 없이 봐야 재는 값이 된다.
        _, bare_rc = run_zsh("%s python3 %s" % (WRAPPER, runner), ROOT)
        self.assertEqual(0, bare_rc, "초록인데 래퍼가 0 이 아닌 값으로 끝났다")

    def test_a_command_with_no_verdict_words_still_carries_rc(self):
        """**갭 ⑥ · 7점** — 설계의 천장(`design_verdict-last.md` 「천장」)을 계약으로 바꾼다.

        `grep` 이 묶여 있는 `Ran|OK|FAILED` 는 `unittest` 의 표기다. e2e 22종은 그
        낱말을 안 쓰므로 판정 칸이 비는데, **그때도 `rc` 는 남아야** 래퍼가 e2e 에서
        쓸모 있다. 문서에만 적힌 천장은 다음 사람이 고치면서 조용히 무너진다.
        """
        runner = self.fake("print('크롤 완료')\n")
        out, _ = run_zsh("%s python3 %s | tail -1" % (WRAPPER, runner), ROOT)
        self.assertIn("rc=0", out.strip().split("\n")[-1],
                      "판정 낱말이 없는 명령에서 마지막 줄이 `rc` 를 안 실었다: %r" % (out,))

    def test_the_log_file_does_not_survive(self):
        """**갭 ③ · 7점** — `trap` 이 임시 로그를 지우는가.

        이 저장소는 자원 누수에 한 번 데었다(반복 586 의 `ResourceWarning` 12건).
        래퍼는 **모든 실행마다** 도므로 안 지우면 `$TMPDIR` 이 조용히 쌓인다.
        """
        box = pathlib.Path(self.tmp.name) / "tmpdir"
        box.mkdir()
        runner = self.fake("print('x')\n")
        run_zsh("TMPDIR=%s %s python3 %s" % (box, WRAPPER, runner), ROOT)
        leftover = sorted(p.name for p in box.iterdir())
        self.assertEqual([], leftover, "임시 로그가 남았다: %r" % (leftover,))

    def test_arguments_survive_intact_including_the_empty_one(self):
        """**갭 ② · 6점** — `"$@"` 의 인용이 살아 있나.

        **첫 판은 이빨이 없었다.** 공백 든 인자로 쟀는데 `"$@"` → `$@` 변이가 **살아남았다**
        — zsh 는 따옴표 없는 배열 확장을 **단어 분할하지 않는다**(bash 와 다르다).
        실제로 갈리는 것은 **빈 인자**다: 인용을 벗기면 `("하나", "", "둘")` 이 2개가 된다
        (실측). 그래서 재는 자리를 공백에서 **빈 인자**로 옮겼다 — 빈 인자는 실제로 온다
        (`-k ''` · 빈 환경 변수 전개).
        """
        runner = self.fake("import sys\nprint('받은 것:', len(sys.argv) - 1, sys.argv[1:])\n")
        out, _ = run_zsh('%s python3 %s "두 낱말" "" 끝' % (WRAPPER, runner), ROOT)
        self.assertIn("받은 것: 3 ['두 낱말', '', '끝']", out,
                      "인자가 그대로 안 넘어갔다 — 빈 것이 사라졌거나 공백에서 쪼개졌다: %r" % (out,))

    def test_calling_it_with_nothing_is_an_error_not_a_green(self):
        """**갭 ① · 6점** — 가드절이 실제로 무는가.

        빈 호출이 `rc=0` 으로 끝나면 **아무것도 안 돌리고 초록**이다. ㉓ 과 같은 모양
        (0 을 세면서 통과)이라 값이 점수보다 크다.
        """
        out, rc = run_zsh("%s" % WRAPPER, ROOT)
        self.assertEqual(2, rc, "빈 호출의 종료 코드가 2 가 아니다 — 출력: %r" % (out,))


class VerdictReviewTest(unittest.TestCase):
    """리뷰 phase(백지 패스 A)가 낸 결함 셋을 계약으로 굳힌다.

    셋 다 **고친 뒤에 쓴 자**다 — TDD 순서를 어긴 것이 아니라, 리뷰가 찾은 결함은
    「실패하는 테스트」가 아니라 **읽어서 찾은 것**이기 때문이다(`rules/review.md`).
    대신 셋 다 **고치기 전 코드로 되돌려 빨강을 확인**하고 넣었다.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def fake(self, body):
        path = pathlib.Path(self.tmp.name) / "runner.py"
        path.write_text(body, encoding="utf-8")
        return path

    def test_an_interrupted_run_does_not_end_green(self):
        """**결함 ① · 심각도 8** — Ctrl-C 가 `── rc=0` 을 찍고 0 으로 끝났다.

        `trap '…' EXIT INT TERM` 한 줄로 셋을 함께 받으면 INT 가 **트랩만 돌리고**
        셸이 이어서 정상 경로로 빠져나간다. **막으려던 사고(초록으로 보이는 실패)를
        정리 코드가 새 경로로 재현한 것**이라 값이 가장 크다.
        """
        started = pathlib.Path(self.tmp.name) / "started"
        runner = self.fake(
            "import pathlib, time\n"
            "pathlib.Path(%r).write_text('x')\n"
            "time.sleep(30)\n" % str(started))
        child = subprocess.Popen(
            ["/bin/zsh", str(WRAPPER), "python3", str(runner)], cwd=str(ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, start_new_session=True)
        self.addCleanup(child.kill)
        deadline = time.time() + 10
        while not started.exists() and time.time() < deadline:
            time.sleep(0.05)
        self.assertTrue(started.exists(), "가짜 러너가 뜨지 못했다 — 잰 것이 없다")
        # 진짜 Ctrl-C 처럼 **프로세스 그룹 전체**에 보낸다. 래퍼에게만 보내면
        # 터미널이 하는 일과 달라져 재는 상황이 아니게 된다.
        os.killpg(child.pid, signal.SIGINT)
        out, _ = child.communicate(timeout=10)
        self.assertEqual(130, child.returncode,
                         "중단인데 종료 코드가 130 이 아니다 — 출력: %r" % (out,))
        self.assertNotIn("rc=0", out, "중단을 초록으로 찍었다: %r" % (out,))
        self.assertIn("중단됨", out, "중단을 판정과 구별해 찍지 않았다: %r" % (out,))

    def test_the_log_body_cannot_forge_the_verdict(self):
        """**결함 ② · 심각도 6** — `^OK` · `^FAILED` 로 열어 두면 본문이 판정을 위조한다.

        크롤 로그에 `OKAY …` 나 `FAILED to fetch …` 가 흔하다. 그것이 마지막 줄에
        실리면 **사람이 초록/빨강을 반대로 읽는다** — 이 계획이 없애려던 바로 그 사고다.
        """
        runner = self.fake(
            "print('OKAY the crawl finished')\nprint('FAILED to fetch http://x')\n")
        out, _ = run_zsh("%s python3 %s | tail -1" % (WRAPPER, runner), ROOT)
        last = out.strip().split("\n")[-1]
        self.assertEqual("── rc=0", last, "본문이 판정 칸에 섞였다: %r" % (last,))

    def test_a_broken_tmpdir_is_an_error_not_a_green(self):
        """**결함 ⑤ · 심각도 7** — `mktemp` 가 실패하면 빈 `$log` 로 나아갔다.

        그러면 `tee` 도 `grep` 도 조용히 빗나가 **판정 칸이 빈 채로 초록**이 된다.
        판정을 마지막 줄로 옮기는 자가 판정을 지우는 경로를 갖고 있으면 안 된다.
        """
        runner = self.fake("print('x')\n")
        out, rc = run_zsh("TMPDIR=%s/없는칸 %s python3 %s"
                          % (self.tmp.name, WRAPPER, runner), ROOT)
        self.assertEqual(2, rc, "임시 로그를 못 만들었는데 2 로 안 끝났다: %r" % (out,))
        self.assertNotIn("rc=0", out, "임시 로그가 없는데 초록을 찍었다: %r" % (out,))


class ZeroPopulationTest(unittest.TestCase):
    """계획 107 — **0건으로 끝난 전수는 초록이 아니다** (`design_zero-population.md`).

    같은 항목(「러너의 판정 줄을 가린다」)의 **서른일곱째**인데 사라진 것이 다르다.
    앞의 셋은 판정 줄·`rc` 가 사라졌는데 여기는 **둘 다 멀쩡하고 참이다** — 0건을
    돌렸으니 0건이 통과다. **가려진 것은 출력이 아니라 모집단**이라 위의 계약 넷은
    전부 통과하면서 사고가 난다. 그래서 재는 자리가 하나 더 필요하다.

    설계가 고른 처방이 둘이라 재는 자도 둘이다 — 뿌리의 덫(`tests/__init__.py`)과
    래퍼의 판정(`Ran 0 tests` → `rc=2`). 하나만으로는 안 되는 이유는 설계 비교표에 있다.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def fake(self, body):
        path = pathlib.Path(self.tmp.name) / "runner.py"
        path.write_text(body, encoding="utf-8")
        return path

    # 0건으로 끝난 전수의 모양 — 판정도 `rc` 도 멀쩡하다. 그것이 문제다.
    EMPTY_RUN = ("import sys\n"
                 "sys.stderr.write('Ran 0 tests in 0.000s\\n\\nOK\\n')\n")

    def test_the_bare_sweep_does_not_find_an_empty_population(self):
        """**처방 B** — 시작 디렉터리를 빠뜨린 전수가 0건이 아니라 전부를 본다.

        그날 친 명령이 이것이다(`PYTHONPATH=src python3 -m unittest discover -b`).
        `tests/` 에 `__init__.py` 가 없어 탐색이 안 내려갔고 **초록으로 답했다.**
        여기서는 **세기만 한다** — 진짜로 돌리면 전수 안에서 전수가 도는 모양이 된다
        (계획 101·`VerdictLastTest` 가 같은 자리에서 피한 길).
        """
        env = dict(os.environ, PYTHONPATH="src")
        done = subprocess.run(
            ["python3", "-c",
             "import unittest; print(unittest.TestLoader().discover('.').countTestCases())"],
            cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        found = int((done.stdout.strip() or "-1").split("\n")[-1])
        self.assertGreaterEqual(
            found, 826,
            "시작 디렉터리 없는 전수가 %d건을 본다 — 사람이 그렇게 치면 `Ran 0 tests` ·"
            " `OK` · rc 0 이 나온다. 0건을 돌렸으니 0건이 통과다"
            " (`tests/__init__.py` 가 없어 탐색이 안 내려간다). stderr: %r"
            % (found, done.stderr[-200:]))

    def test_a_zero_count_sweep_is_not_reported_green(self):
        """**처방 A** — 래퍼가 `Ran 0 tests` 를 판정이 아니라 사고로 읽는다.

        계획 106 의 래퍼는 감싼 명령의 `rc` 를 그대로 싣는데 그 `rc` 가 0 이라
        **이 자리를 못 덮는다**(탐침 1 실측: `── Ran 0 tests in 0.000s OK rc=0`).
        이 저장소의 관용구에서 **2 는 판정이 아니라 「재지 못했다」** 이고 0건이 그것이다.
        """
        runner = self.fake(self.EMPTY_RUN)
        out, _ = run_zsh("%s python3 %s | tail -1" % (WRAPPER, runner), ROOT)
        last = out.strip().split("\n")[-1] if out.strip() else ""
        self.assertIn("모집단 0", last,
                      "0건인데 마지막 줄이 그 말을 안 한다 — 읽힌 것: %r" % (last,))
        self.assertIn("rc=2", last,
                      "0건 전수를 `rc=0` 으로 실었다 — 읽힌 것: %r" % (last,))
        _, bare_rc = run_zsh("%s python3 %s" % (WRAPPER, runner), ROOT)
        self.assertEqual(2, bare_rc, "0건인데 래퍼가 초록으로 끝났다 — 「재지 못했다」가 2 다")

    def test_a_red_run_keeps_its_own_exit_code(self):
        """**덧쓰지 않는다** — 수집 단계에서 죽어 0건인 경우는 이미 빨갛다.

        거기까지 2 로 바꾸면 **원래 코드를 잃는다**(설계 「계약」 3번). 오늘도 초록인
        자인데, 처방을 넓게 쓰면 바로 여기가 죽으므로 스텝 2 의 울타리다.
        """
        runner = self.fake(self.EMPTY_RUN + "sys.exit(1)\n")
        out, rc = run_zsh("%s python3 %s" % (WRAPPER, runner), ROOT)
        self.assertEqual(1, rc, "0건이라고 빨간 실행의 종료 코드를 덮어썼다: %r" % (out[-200:],))
        self.assertIn("rc=1", out, "마지막 줄이 원래 코드를 안 실었다: %r" % (out[-200:],))

    def test_the_real_runner_is_measured_too_not_only_fakes(self):
        """**갭 ⑦ · 8점** — 위의 전부가 **가짜 러너**다. 진짜 명령 꼴로 한 번 잰다.

        설계가 「범위 밖」으로 둔 나머지 길(**잘못된 `-k` 필터**)이 여기다 —
        `tests/__init__.py` 는 그 길을 못 막고 래퍼만 막는다. 가짜로만 재면
        「우리 러너가 정말 그 표기를 내는가」를 영영 안 물은 채 초록이 된다.

        **전수를 돌리는 것이 아니다** — 아무것도 안 맞는 필터라 수집만 하고 0건으로
        끝난다(실측 0.17초). 전수 안에서 전수가 도는 모양이 아니다.
        """
        out, rc = run_zsh(
            "PYTHONPATH=src %s python3 -m unittest discover -b -s tests -k 없는이름_없음"
            % WRAPPER, ROOT)
        last = out.strip().split("\n")[-1] if out.strip() else ""
        self.assertIn("Ran 0 tests", last, "진짜 러너의 0건 표기가 바뀌었다: %r" % (last,))
        self.assertIn("모집단 0", last, "진짜 러너의 0건을 안 물었다: %r" % (last,))
        self.assertEqual(2, rc, "아무것도 안 맞는 필터가 초록으로 끝났다: %r" % (last,))


if __name__ == "__main__":
    unittest.main()
