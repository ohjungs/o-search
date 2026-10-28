# -*- coding: utf-8 -*-
"""계획 126 e2e — `dup_def_gap` 을 **사용자가 하는 그대로** 돌린다.

함수 단위는 테스트 phase 가 이미 쟀다. 여기서 재는 것은 **체크아웃에서 문서화된 명령을
쳤을 때** 자가 실제로 무나/조용한가다. 그래서 매 시나리오가 `git archive HEAD` 사본을
새로 뜨고 `project.md` 에 적힌 러너(`python3 -m unittest discover -b tests`)를 맨몸으로 친다.

**판정을 파이프로 읽지 않는다** — `subprocess` 로 `returncode` 를 직접 받는다
(`digest ## 반복 실패` 최다 재발: 「`&&` 가 읽는 rc 는 파이프 끝 것이다」).

쓰는 법: `python3 docs/e2e/dup-def-dead-twin/scenario.py <저장소>`
0 = 전 시나리오 통과 · 1 = 하나라도 실패 · 2 = 재지 못했다.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

RUNNER = [sys.executable, "-m", "unittest", "discover", "-b", "tests"]
TARGET = "tests/test_docs.py"


def checkout(repo):
    """추적되는 것만 뜬 사본 — 이 기계 로컬 상태(추적 밖 `docs/reports/`)에 안 기댄다."""
    out = pathlib.Path(tempfile.mkdtemp(prefix="e2e126_")) / "repo"
    out.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(repo), "archive", "HEAD"],
                         capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(out)], input=tar.stdout, check=True)
    return out


def run(tree):
    """러너를 맨몸으로 친다. `(rc, 합친 출력)`."""
    # **환경을 물려받는다.** 처음엔 네 변수만 준 깨끗한 env 로 돌렸는데 전수 한 판이
    # 23초 → 수 분으로 늘어 10분 상한에 걸렸다(실측). 변이 하네스는 `os.environ` 을
    # 물려받아 16판이 멀쩡히 돌았으므로 차이는 거기다 — 재는 것은 「문서화된 명령이
    # 이 체크아웃에서 무나」지 「빈 환경에서 도나」가 아니라 물려받는 쪽이 맞다.
    env = dict(os.environ, PYTHONPATH="src", PYTHONDONTWRITEBYTECODE="1",
               PYTHONPYCACHEPREFIX=tempfile.mkdtemp(prefix="pyc126_"))
    r = subprocess.run(RUNNER, cwd=tree, env=env, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def plant(tree, old, new, where=TARGET):
    f = tree / where
    t = f.read_text(encoding="utf-8")
    if t.count(old) != 1:
        raise AssertionError("심을 자리를 못 찾았다(적중 %d): %r" % (t.count(old), old[:60]))
    f.write_text(t.replace(old, new, 1), encoding="utf-8")


DEAD_TWIN = '''def archive_gap(index_text, live_names):
    """되살린 죽은 쌍둥이 — `verdict` 가 정의되지 않은 이름이다(계획 126 반사실)."""
    for slug, status, _ in VERDICT_ROW.findall(index_text):
        if not is_done(status):
            continue
        cell = verdict.strip()
        if VERDICT_DATE.fullmatch(cell):
            return "엉뚱한 자가 산다"
    return None


def archive_gap(index_text, live_names):'''


def main(repo):
    results = []

    # ── S1 깨끗한 사본에서 전수가 초록이다 (이 기계 로컬 상태에 안 기댄다)
    tree = checkout(repo)
    rc, out = run(tree)
    ok = rc == 0 and "OK" in out
    results.append(("S1 깨끗한 사본 전수 초록", ok,
                    [l for l in out.splitlines() if l.startswith(("OK", "Ran ", "FAILED"))]))
    shutil.rmtree(tree.parent)

    # ── S2 죽은 쌍둥이를 되살리면 빨강이고 이름·두 줄 번호를 인쇄한다
    tree = checkout(repo)
    plant(tree, "def archive_gap(index_text, live_names):", DEAD_TWIN)
    rc, out = run(tree)
    named = "archive_gap" in out
    both_lines = out.count("와 :") >= 1
    ok = rc != 0 and named and both_lines
    hit = [l.strip() for l in out.splitlines() if "같은 스코프에 같은 이름" in l]
    results.append(("S2 되살린 쌍둥이 → 빨강 · 이름·두 줄 번호", ok, hit[:1]))
    shutil.rmtree(tree.parent)

    # ── S3 다른 파일(`src/`)의 중복도 잡는다 — 모집단이 한 파일에 한정되지 않는다
    tree = checkout(repo)
    victim = tree / "src/websearch/flags.py"
    victim.write_text(victim.read_text(encoding="utf-8")
                      + "\n\ndef _e2e_twin():\n    pass\n\n\ndef _e2e_twin():\n    pass\n",
                      encoding="utf-8")
    rc, out = run(tree)
    ok = rc != 0 and "_e2e_twin" in out and "flags.py" in out
    hit = [l.strip() for l in out.splitlines() if "_e2e_twin" in l]
    results.append(("S3 src/ 의 중복도 잡는다", ok, hit[:1]))
    shutil.rmtree(tree.parent)

    # ── S4 음성 대조 — 서로 다른 클래스의 같은 이름은 조용하다 (regex 처방이 틀리던 자리)
    tree = checkout(repo)
    victim = tree / "src/websearch/flags.py"
    victim.write_text(victim.read_text(encoding="utf-8")
                      + "\n\nclass _E2EA:\n    def go(self):\n        pass\n"
                        "\n\nclass _E2EB:\n    def go(self):\n        pass\n",
                      encoding="utf-8")
    rc, out = run(tree)
    ok = rc == 0
    results.append(("S4 다른 클래스의 같은 이름 → 조용", ok,
                    [l for l in out.splitlines() if l.startswith(("OK", "FAILED"))]))
    shutil.rmtree(tree.parent)

    # ── S5 모집단 한 덩이가 사라지면 「위반 0」이 아니라 하한이 문다
    tree = checkout(repo)
    shutil.rmtree(tree / "src")
    rc, out = run(tree)
    floored = "하한" in out and "순회가 죽은 것" in out
    results.append(("S5 src/ 를 치우면 하한이 문다(「위반 0」이 아니다)",
                    rc != 0 and floored,
                    [l.strip() for l in out.splitlines() if "하한" in l][:1]))
    shutil.rmtree(tree.parent)

    # ── S6 거짓 초록 채널 회귀 — 리뷰 ① 이 닫은 것이 다시 열리면 e2e 가 본다
    tree = checkout(repo)
    plant(tree,
          "        gap = dup_def_gap(\n"
          "            [(path.relative_to(ROOT), path.read_text(encoding=\"utf-8\")) for path in paths])",
          "        _sources = ((path.relative_to(ROOT), path.read_text(encoding=\"utf-8\"))\n"
          "                    for path in paths)\n"
          "        _ = sum(1 for _ in _sources)  # 반사실: 먼저 세는 코드\n"
          "        gap = dup_def_gap(_sources)")
    plant(tree, "def archive_gap(index_text, live_names):", DEAD_TWIN)
    rc, out = run(tree)
    # **기대는 초록이다.** 쌍둥이가 살아 있는데도 초록이면 채널이 열린 것이고, 그것이
    # 곧 「리뷰 ① 의 괄호 한 쌍이 하중을 받는다」의 증거다. 여기서 빨강이 나오면
    # 반사실이 안 심긴 것이므로(심기 실패는 예외로 터진다) 시나리오가 **못 쟀다**는 뜻이다.
    ok = rc == 0
    results.append(("S6 반사실: 제너레이터로 되돌리면 쌍둥이가 살아도 초록이다(채널 증명)",
                    ok, [l for l in out.splitlines() if l.startswith(("OK", "FAILED"))]))
    shutil.rmtree(tree.parent)

    print("계획 126 e2e — `dup_def_gap`\n")
    bad = 0
    for name, ok, detail in results:
        print("  %s %s" % ("통과" if ok else "실패", name))
        for d in detail:
            print("        %s" % d)
        bad += 0 if ok else 1
    print("\n시나리오 %d/%d 통과" % (len(results) - bad, len(results)))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(pathlib.Path(sys.argv[1]).resolve()))
