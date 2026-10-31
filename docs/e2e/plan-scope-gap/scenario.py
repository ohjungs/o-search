#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""계획 130 e2e — 계획서 「건드릴 파일」 칸을 읽는 자.

계획서(아카이브 전 `plan_plan-scope-gap` · 지금은 `docs/plan_history_102.md`)의
「e2e 시나리오」 4종을 **그대로** 돌린다.
`rc=0` 이면 4/4, 아니면 실패한 시나리오를 인쇄한다. `rc=2` 는 **재지 못했다**다.

사용자가 하는 그대로 한다 — 저장소 사본을 만들고, 문서를 손으로 비틀고,
**전수 명령을 맨몸으로 쳐서** 판정 줄을 읽는다. 함수를 직접 부르지 않는다
(그것은 테스트 phase 가 이미 했다).

**사본은 `git clone` 이다.** 이 자는 git 을 읽으므로 `.git` 없는 사본에서는
건너뛴다 — 그 꼴로 시나리오를 돌리면 「조용하다」가 통과로 보인다.
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
PLAN_SLUG = re.compile(r"^plan: ([A-Za-z0-9_-]+)", re.M)


def live_plan(repo):
    """사본의 활성 계획서 경로 — 없으면 **재지 못했다**(`rc=2`).

    **계획이 아카이브되면 이 자는 못 잰다** — 가드가 «활성» 계획만 판정하므로
    아카이브된 계획서를 비틀어도 아무 일이 안 일어난다. 그 판에서 「조용하다」를
    통과로 읽으면 안 되므로 판정이 아니라 측정 불능으로 끝낸다.
    """
    status = (pathlib.Path(repo) / "docs" / "status.md").read_text(
        encoding="utf-8")
    slug = PLAN_SLUG.search(status)
    if not slug:
        print("status.md 에 `plan:` 이 없다 — 재지 못했다")
        sys.exit(2)
    plan = pathlib.Path(repo) / "docs" / ("plan_%s.md" % slug.group(1))
    if not plan.exists():
        print("활성 계획서가 없다(아카이브됐다) — 재지 못했다:", plan.name)
        sys.exit(2)
    return plan


def clone(dst):
    """저장소 사본. 로컬 `main` 은 안 만든다 — `origin/main` 떨굼이 받는다."""
    done = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks",
                           str(ROOT), dst], capture_output=True, text=True)
    if done.returncode != 0:
        print("사본을 못 만들었다 — 재지 못했다:", done.stderr.strip())
        sys.exit(2)


def suite(repo):
    """사본에서 전수를 돌리고 `(rc, 출력)`."""
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = tempfile.mkdtemp()
    done = subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-b", "tests"], cwd=repo, env=env,
                          capture_output=True, text=True)
    return done.returncode, done.stderr


def scenario_1():
    """사건 재연 — 칸에서 `README.md` 를 지우면 그 파일을 대며 빨개진다."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        clone(repo)
        plan = live_plan(repo)
        text = plan.read_text(encoding="utf-8")
        marker = "`tests/test_docs.py` **와 `README.md`**"
        if marker not in text:
            return False, "계획서의 칸이 기대한 꼴이 아니다 — 재지 못했다"
        plan.write_text(text.replace(marker, "`tests/test_docs.py`", 1),
                        encoding="utf-8")
        rc, out = suite(repo)
    if rc == 0:
        return False, "칸에서 README.md 를 지웠는데 전수가 초록이다"
    if "README.md" not in out:
        return False, "빨개졌지만 README.md 를 대지 않는다"
    if plan.name not in out:
        return False, "빨개졌지만 어느 계획서인지 대지 않는다"
    return True, "전수가 빨강 · README.md 와 계획서 이름을 댄다"


def scenario_2():
    """오늘 축 — 손대지 않은 사본에서 조용하다(이 계획서 자신이 입력이다)."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        clone(repo)
        rc, out = suite(repo)
    if rc != 0:
        return False, "손대지 않은 사본에서 전수가 빨갛다"
    # **건너뛴 수를 «수» 로 못박는다** — 「조용하다」만 보면 실물 축이 건너뛴 초록과
    # 구별이 안 된다. 사본에 기대하는 둘은 게이트 ⑱ ㉢ 짝뿐이다(`docs/reports/` 가
    # `.gitignore` 라 사본에 없다). 이 계획의 둘은 `.git` 과 `origin/main` 이 있어 돈다.
    if "skipped=2" not in out:
        return False, ("건너뛴 수가 2가 아니다 — 실물 축이 건너뛴 초록일 수 있다: "
                       + " / ".join(l for l in out.split("\n")
                                    if l.startswith(("OK", "FAILED"))))
    return True, "전수 초록 · 건너뛴 수 2(게이트 ⑱ ㉢ 짝뿐) · 실물 축 둘이 돌았다"


def scenario_3():
    """오탐 축 — 옛 꼴(`## 범위`) 계획서는 「재지 못했다」로 신고한다."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        clone(repo)
        plan = live_plan(repo)
        plan.write_text("# 계획 130\n\n## 범위\n\n- 자 하나를 세운다\n",
                        encoding="utf-8")
        rc, out = suite(repo)
    if rc == 0:
        return False, "칸이 없는 계획서인데 전수가 조용하다"
    if "재지 못했다" not in out:
        return False, "빨개졌지만 「재지 못했다」가 아니라 위반으로 읽혔다"
    return True, "전수가 빨강 · 「재지 못했다」로 신고한다"


def scenario_4():
    """회귀 — 기존 문서 가드 일곱과 e2e 18종."""
    guards = ("ArchiveGapTest", "VerdictGapTest", "StepGapTest",
              "IndexStatusVocabTest", "ReadBudgetGapTest", "DupDefGapTest",
              "CompileWarnGapTest")
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    done = subprocess.run([sys.executable, "-m", "unittest", "-b"]
                          + ["tests.test_docs.%s" % g for g in guards],
                          cwd=str(ROOT), env=env, capture_output=True, text=True)
    if done.returncode != 0:
        return False, "문서 가드 일곱이 빨갛다:\n" + done.stderr[-2000:]
    roster = [p.stem for p in sorted((ROOT / "e2e").glob("*_e2e.py"))]
    roster.append("design_check")
    broken = []
    for name in roster:
        one = subprocess.run([sys.executable, str(ROOT / "e2e" / (name + ".py"))],
                             cwd=str(ROOT), env=env, capture_output=True, text=True)
        if one.returncode != 0:
            broken.append("%s rc=%d" % (name, one.returncode))
    if broken:
        return False, "e2e 가 빨갛다: " + " ".join(broken)
    return True, "문서 가드 일곱 rc=0 · e2e %d종 rc=0" % len(roster)


def main():
    scenarios = (("S1 사건 재연", scenario_1), ("S2 오늘 축", scenario_2),
                 ("S3 오탐 축", scenario_3), ("S4 회귀", scenario_4))
    passed = 0
    for name, run in scenarios:
        ok, why = run()
        print("%-12s %s — %s" % (name, "통과" if ok else "실패", why))
        passed += 1 if ok else 0
    print("시나리오 %d/%d" % (passed, len(scenarios)))
    return 0 if passed == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
