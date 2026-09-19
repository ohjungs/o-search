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

import pathlib
import subprocess
import tempfile
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


if __name__ == "__main__":
    unittest.main()
