"""`scripts/merge-to-main.sh` 의 유일한 계약: **전수가 빨가면 main 을 안 민다.**

2026-09-11 에 이 절차를 손으로 조립하다 `... && 전수 ; git push` 로 연쇄가 끊겨
**전수가 실패했는데 푸시가 됐다.** 그날은 실패 원인이 문서 상한이라 무해했지만 구조는
「빨간 main 을 민다」였다. 손으로 조립하는 절차는 언젠가 반드시 한 번 틀린다.

**진짜 git 으로 잰다** — 목으로는 「연쇄가 끊겼나」를 못 본다. 원격은 로컬 bare 저장소라
네트워크를 안 쓴다.
"""
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "merge-to-main.sh")


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


class MergeScriptTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.remote = os.path.join(self.dir.name, "원격.git")
        self.work = os.path.join(self.dir.name, "work")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.remote], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", self.work], check=True)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            git(self.work, "config", k, v)
        pathlib.Path(self.work, "a.txt").write_text("1\n")
        git(self.work, "add", "-A"); git(self.work, "commit", "-qm", "init")
        git(self.work, "remote", "add", "origin", self.remote)
        git(self.work, "push", "-q", "-u", "origin", "main")
        git(self.work, "checkout", "-qb", "loop/시험")
        pathlib.Path(self.work, "a.txt").write_text("2\n")
        git(self.work, "add", "-A"); git(self.work, "commit", "-qm", "변경")

    def _run(self, test_cmd):
        return subprocess.run(["zsh", SCRIPT], cwd=self.work, capture_output=True, text=True,
                              env={**os.environ, "MERGE_TEST_CMD": test_cmd,
                                   "GIT_TERMINAL_PROMPT": "0"})

    def _remote_main(self):
        return git(self.remote, "rev-parse", "main").stdout.strip()

    def test_a_red_suite_does_not_move_main(self):
        before = self._remote_main()
        r = self._run("false")
        self.assertNotEqual(r.returncode, 0, "빨간데 성공으로 끝났다")
        self.assertEqual(self._remote_main(), before,
                         "전수가 빨간데 main 이 움직였다 — 연쇄가 끊겼다")

    def test_a_green_suite_moves_main(self):
        """음성 대조 — 이것이 없으면 「아무것도 안 미는 스크립트」도 위 테스트를 통과한다."""
        before = self._remote_main()
        r = self._run("true")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotEqual(self._remote_main(), before, "초록인데 main 이 안 움직였다")

    def test_a_non_loop_branch_is_refused(self):
        git(self.work, "checkout", "-q", "main")
        r = self._run("true")
        self.assertEqual(r.returncode, 2)

    # ── 0건 축 (계획 108) ──────────────────────────────────────────────────
    # `unittest` 는 **0건을 돌려도 `rc=0`** 을 주므로 39행의 `[ $trc -eq 0 ]` 에는
    # 빈 전수가 초록으로 보인다. 위의 세 테스트는 그 구멍을 안 본다 — 「빨가면 안
    # 민다」만 재고, 0건은 빨갛지 않기 때문이다. 아래 둘은 **층이 다르다**: ①은
    # 「래퍼를 타면 0건이 실제로 병합을 막는가」(행동), ②는 「기본값이 그 래퍼를
    # 타는가」(배선). ①만 있으면 배선이 빠져도 초록이고, ②만 있으면 문자열만 맞다.

    def test_b_zero_tests_through_the_wrapper_does_not_move_main(self):
        """래퍼를 탄 0건은 `rc=2` 라 `main` 이 안 움직인다.

        **실물 `scripts/verdict.sh` 를 부른다** — 가짜로 `exit 2` 를 주면 「0건을
        판정할 줄 아는가」가 아니라 「2 를 받으면 멈추는가」만 재게 된다. 모집단이
        비는 자리는 테스트 파일이 하나도 없는 임시 디렉터리로 만든다.
        """
        empty = os.path.join(self.dir.name, "빈곳")
        os.mkdir(empty)
        verdict = os.path.join(ROOT, "scripts", "verdict.sh")
        before = self._remote_main()
        r = self._run("%s python3 -m unittest discover -b -s %s" % (verdict, empty))
        self.assertIn("모집단 0", r.stdout,
                      "래퍼가 0건을 사고로 읽지 않았다\n" + r.stdout + r.stderr)
        self.assertNotEqual(r.returncode, 0, "0건인데 성공으로 끝났다\n" + r.stdout)
        self.assertEqual(self._remote_main(), before,
                         "모집단이 0 인데 main 이 움직였다 — 빈 전수가 문을 통과했다")

    def test_b_the_default_suite_goes_through_the_wrapper(self):
        """배선 — 기본 `TEST_CMD` 가 `verdict.sh` 를 탄다.

        위 테스트는 `MERGE_TEST_CMD` 주입으로 재므로 **기본값이 래퍼를 안 타도
        초록이다.** 사람이 병합할 때 쓰는 것은 기본값이라 그 줄을 직접 읽는다.
        환경 변수 배정보다 **뒤**인지도 본다 — 앞에 오면 배정이 명령 이름으로
        읽혀 `rc=127` 이다(`scripts/verdict.sh:7-11` 의 실측).
        """
        lines = [ln for ln in pathlib.Path(SCRIPT).read_text(encoding="utf-8").splitlines()
                 if ln.startswith("TEST_CMD=")]
        self.assertEqual(len(lines), 1, "TEST_CMD 기본값 줄을 하나로 못 집었다")
        cmd = lines[0]
        self.assertIn("verdict.sh", cmd,
                      "기본 전수가 래퍼를 안 탄다 — 0건이 rc=0 으로 병합을 통과한다")
        self.assertLess(cmd.index("PYTHONPATH=src"), cmd.index("verdict.sh"),
                        "래퍼가 환경 변수 배정보다 앞에 있다 — rc=127 이 된다")


if __name__ == "__main__":
    unittest.main()
