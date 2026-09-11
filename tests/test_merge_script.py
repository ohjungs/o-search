"""`scripts/merge-to-main.sh` 의 유일한 계약: **전수가 빨가면 main 을 안 민다.**

2026-09-11 에 이 절차를 손으로 조립하다 `... && 전수 ; git push` 로 연쇄가 끊겨
**전수가 실패했는데 푸시가 됐다.** 그날은 실패 원인이 문서 상한이라 무해했지만 구조는
「빨간 main 을 민다」였다. 손으로 조립하는 절차는 언젠가 반드시 한 번 틀린다.

**진짜 git 으로 잰다** — 목으로는 「연쇄가 끊겼나」를 못 본다. 원격은 로컬 bare 저장소라
네트워크를 안 쓴다.
"""
import os
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
        open(os.path.join(self.work, "a.txt"), "w").write("1\n")
        git(self.work, "add", "-A"); git(self.work, "commit", "-qm", "init")
        git(self.work, "remote", "add", "origin", self.remote)
        git(self.work, "push", "-q", "-u", "origin", "main")
        git(self.work, "checkout", "-qb", "loop/시험")
        open(os.path.join(self.work, "a.txt"), "w").write("2\n")
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


if __name__ == "__main__":
    unittest.main()
