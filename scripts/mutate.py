#!/usr/bin/env python3
"""변이 앵커가 파일에 **정확히 하나**인지 적용 전에 잰다.

왜 있나 — 2026-11-01 반복 792 에 변이 M8 이 **거짓 생존**을 냈다. 앵커
`if not missing:` 가 `tests/test_docs.py` 에 둘이라 `str.replace(앵커, …, 1)` 이
**남의 함수**를 고쳤고, 남의 함수는 그 변경에 무던해 전수가 초록이라 「생존」으로
읽혔다. 「생존」은 「테스트가 약하다」로 읽히고 그 판정이 다음 테스트를 더 짜게
만들므로, **재지 못한 것이 테스트 설계로 흘러든다.**

**세는 술어가 적용기와 같아야 한다.** `grep -c` 는 **줄**을 세고 적용기는
**부분문자열**을 센다 — 실물 `tests/test_docs.py` 에서 둘이 갈리는 자리가 7개이고
그중 하나가 하필 `dup_def_gap` 의 픽스처다(`"class A:\n    def go(self):\n …"` —
`go(self):\n` 가 **한 물리 줄 안에 두 번**). 그래서 여기서는 `str.count` 와 **같은
수**가 나오게 센다(겹치는 적중은 세지 않는다 — `count` 의 규약이다).

쓰는 법:

    scripts/mutate.py --check <파일> <앵커>              # 판정만 · 안 쓴다
    scripts/mutate.py <파일> <앵커> <치환> -- <명령…>     # 적용 → 실행 → 복원

종료 코드는 이 저장소 관용구를 따른다 — **`2` 는 판정이 아니라 「재지 못했다」** 다.

| | `0` | `1` | `2` |
|---|---|---|---|
| `--check` | 앵커가 유일하다 | — | 0곳·여럿·못 읽었다 |
| 적용 | **변이 죽음**(테스트가 문다) | **변이 생존**(무는 테스트가 없다) | 재지 못했다 |

**`2` 가 「생존」과 섞이지 않는 것이 이 자의 요점이다** — 거짓 생존은 재지 못한 것을
판정으로 읽은 사고였다. 그래서 신호·예외·심기지 않은 변이가 전부 `2` 로 나간다.
**읽을 때는 `| tail -1` 만 쓴다** — 적용 경로는 `--check` 의 판정 줄을 먼저 찍으므로
`grep rc=0` 은 생존을 죽음으로 읽는다.
판정은 **stdout 의 마지막 한 줄**로 다시 찍으므로 `| tail -1` 을 붙여도 산다
(`scripts/verdict.sh` 와 같은 관례).

**이 자가 재지 않는 것 둘** (백지 패스가 짚었다 — 적어 두지 않으면 판정으로 읽힌다):

- **베이스라인은 이제 자가 본다**(계획 132). 「죽음」이 나면 **무해 대조판**을 한 판 더
  돌려(원본 끝에 개행 하나) 그 빨강이 변이의 **뜻** 때문인지 파일을 **건드린 것** 때문인지
  가른다 — 건드림 쪽이면 `2` 다. 이미 빨간 전수 · `PYTHONPATH` 누락 · 오타 난 명령 ·
  `timeout` 의 124 도 대조판에서 빨가므로 같은 `2` 로 떨어진다. **생존 경로는 대조판을
  돌리지 않는다** — 비용이 0 이고, 생존이 곧 「건드림은 빨강을 안 만든다」의 증명이다.
  **남은 천장 둘**: ① 대조판 결과를 캐시하지 않으므로 같은 (파일·명령) 쌍을 N판 돌리면
  대조판도 N번 돈다 ② **죽음이면 감싼 명령이 두 판 돈다** — 명령이 산출물(커버리지 파일 ·
  로그 · 결과서)을 쓰면 **마지막 쓰기는 대조판의 것**이라 남은 산출물이 변이를 안 비춘다.
  변이본의 산출물을 봐야 하면 이어쓰기로 받거나 대상 모듈만 돌린다(백지 패스가 짚었다).
- **한 번에 하나.** 같은 파일에 둘이 겹치면 뒤엣것이 **앞엣것의 변이본**을 원본으로 집어
  복원이 변이를 영구화한다. 동시에 돌리려면 파일을 갈라야 한다.

설계는 `docs/design_history_099.md` · 계약은 그 문서의 「계약」 절.
"""
import pathlib
import signal
import subprocess
import sys

USAGE = ("쓰는 법: scripts/mutate.py --check <파일> <앵커>"
         "  또는  scripts/mutate.py <파일> <앵커> <치환> -- <명령…>")


class Stopped(Exception):
    """신호로 끊겼다 — 복원을 돌리기 위해 예외로 올린다.

    기본 처리기는 `finally` 를 안 돌리고 즉시 죽인다. 실측(백지 패스): `SIGTERM`
    으로 끊으니 `rc=143` 에 **변이가 파일에 남고 stderr 가 조용했다** — 이 자의
    docstring 이 한 약속(「더러운 트리를 0 으로 끝내는 길이 없다」)이 뚫리는 자리다.
    `scripts/verdict.sh` 가 `trap 'stopped 143' TERM` 으로 같은 것을 막고, 그
    주석이 「막으려던 사고를 정리 코드가 **새 경로로 재현**했다」를 적어 뒀다.
    """


def _stop(signum, frame):
    raise Stopped("신호 %d" % signum)


def read_exact(path):
    """**적용기와 같은 글**을 돌려준다 — 바이트를 읽어 디코드한다.

    `read_text` 를 쓰면 안 된다: universal newlines 가 `\\r\\n` 을 `\\n` 으로 바꿔
    **판정과 적용이 다른 글을 본다.** 실측(백지 패스): CRLF 파일에 여러 줄 앵커를
    주니 `--check` 는 「앵커 유일」인데 적용기는 0곳을 바꾸고 명령이 **원본**을 보고
    「생존 … 이것은 판정이다」가 났다 — **설계 계약 1번이 바로 그 자리에서 깨졌다.**
    읽는 자리를 하나로 모아 뿌리에서 닫는다.
    """
    return pathlib.Path(path).read_bytes().decode("utf-8")


def anchor_sites(text, anchor):
    """앵커가 든 줄 번호 전부. **`text.count(anchor)` 와 같은 수**를 돌려준다.

    겹치는 적중을 안 세는 것이 `str.count` 의 규약이라 보폭을 `len(anchor)` 로
    둔다 — 보폭 1 로 두면 `"aa"` 를 `"aaa"` 에서 둘로 세어 **적용기와 갈린다**.
    적용기와 갈리는 판정은 이 자가 닫으려는 사고의 새 통로다.
    """
    sites, at = [], text.find(anchor)
    while at != -1:
        sites.append(text.count("\n", 0, at) + 1)
        at = text.find(anchor, at + len(anchor))
    return sites


def verdict(say, rc):
    """판정을 마지막 한 줄로 찍고 종료 코드를 돌려준다."""
    print("── %s rc=%d" % (say, rc))
    return rc


def check(path, anchor):
    """앵커 유일성만 본다. **파일을 쓰지 않는다.**"""
    if not anchor:
        return verdict("앵커가 빈 문자열이다 — 재지 못했다", 2)
    try:
        text = read_exact(path)
    except OSError as err:
        return verdict("파일을 못 읽었다(%s) — 재지 못했다" % (err.strerror or err), 2)
    sites = anchor_sites(text, anchor)
    if len(sites) == 1:
        return verdict("앵커 유일 — %s:%d" % (path, sites[0]), 0)
    if not sites:
        return verdict("앵커 0곳 — **썩었다**. 파일이 움직였으니 앵커를 다시 뜬다"
                       " (좁히는 것이 아니다) — 재지 못했다", 2)
    print("앵커가 %d곳에 있다 — 적용은 **첫 하나**만 바꾸므로 나머지가 조용히 남고,"
          " 그 초록은 「생존」이 아니라 「재지 못했다」다. 걸린 자리:" % len(sites))
    for at in sorted(set(sites)):
        n = sites.count(at)
        print("  %s:%d%s" % (path, at, " (%d회)" % n if n > 1 else ""))
    return verdict("앵커 %d곳 — 유일해지도록 **넓혀** 다시 뜬다(앞뒤 줄을 붙인다)"
                   " — 재지 못했다" % len(sites), 2)


def control_red(target, original, cmd):
    """**무해 대조판** — 원본을 뜻 없이 건드린 채 같은 명령을 한 판 돌린다.

    `True` 빨갰다 · `False` 초록이다 · `None` 재지 못했다.

    왜 있나 — 「죽음」은 「명령이 빨갰다」일 뿐이고, 그 빨강이 변이의 **뜻** 때문인지
    파일을 **건드린 것** 때문인지 가르지 않는다. 2026-11-03 반복 805 실측: 활성 계획의
    「건드릴 파일」 칸 **밖** 파일에 docstring 산문 한 낱말을 더하고 전수를 돌리니
    `tests/test_docs.py` 의 `ScopeTest` 가 빨개져 「변이 죽음 rc=0」이 났다. 그 자가 읽는
    것은 `git diff --name-only` 의 **파일 집합**이라 무엇으로 바꿨는지와 무관하다.

    **심기 전 베이스라인으로는 못 잡는다** — 건드리기 전에는 초록이고 빨강은 건드린
    뒤에 생긴다(같은 실측). 즉 원인은 「이미 빨간 명령」이 아니라 **측정 행위가 측정
    대상을 흔드는 자기참조**다. 설계 `docs/design_mutant-baseline-red.md` 3-2절이
    그 탐침으로 선측정안을 버렸다. 이 자는 **이미 빨간 명령**(`PYTHONPATH` 누락 ·
    오타 난 명령 · 이미 빨간 전수)도 같은 `2` 로 떨어뜨린다 — 그쪽도 대조판에서 빨갛다.

    대조 편집은 **원본 끝에 개행 하나**다 — 뜻이 없는 가장 작은 바이트 변경이고,
    앵커 자리를 쓰지 않는다(치환 길이가 변이와 달라 「무해」를 보장하지 못한다).
    그 개행조차 무는 파일이면 대조판이 빨가므로 `2` 로 떨어진다 — **안전한 쪽이다.**

    ponytail: (파일·명령) 쌍마다 매번 다시 돈다 — 한 파일로 열아홉 판을 돌리는 밤이면
    대조판도 열아홉 번이다. 캐시는 상태를 들여오는 일이라 근거가 생기면 그때 둔다.
    """
    # `except OSError` 를 두지 않는다 — `main()` 의 바닥 그물이 어떤 예외든 **같은 `2`**
    # 로 돌리므로 여기서 받으면 분기만 늘고 재는 자가 0개가 된다(변이 M4 가 실제로
    # 살아남았다 · 2026-11-03 반복 808). `finally` 가 복원을 돌린 뒤 예외가 올라간다.
    try:
        target.write_bytes(original + b"\n")
        red = subprocess.run(cmd).returncode != 0
    finally:
        try:
            target.write_bytes(original)
        except OSError as err:
            print("!! %s 를 원본으로 되쓰지 못했다(%s) — 작업 트리가 더럽다"
                  % (target, err.strerror or err), file=sys.stderr)
            red = None
    return red


def apply_and_run(path, anchor, replacement, cmd):
    """유일한 앵커만 적용하고, 감싼 명령을 돌린 뒤 **반드시 되돌린다.**

    `git restore` 를 부르지 않는다 — 변이는 작업 중인 트리에서 돌고 그 명령은 남의
    미커밋 변경까지 날린다(`rules/plan.md` 3-1절). 원본 바이트를 들고 있다가 되쓴다.

    **복원 실패는 조용히 끝내지 않는다.** 더러운 트리를 0 으로 끝내면 다음 반복이
    변이가 남은 파일을 제 코드로 읽는다 — 데이터 안전이라 사다리로 타협하지 않는다.
    """
    if check(path, anchor) != 0:
        return 2                      # 거부면 명령을 돌리지 않는다 — 계약 3
    target = pathlib.Path(path)
    original = target.read_bytes()
    mutated = original.decode("utf-8").replace(anchor, replacement, 1)
    if mutated.encode("utf-8") == original:
        # **이 저장소가 손으로 쓰던 규약이 바로 이것이다** — `plan_history_037.md:151`
        # 「모든 변이는 심기 전에 `mutated != original` 로 실제로 심어진 것을 먼저
        # 단언한다」(`plan_history_035.md:145` 도 같다). 손버릇을 기제로 옮기면서
        # **그 단언만 빠뜨렸고** 백지 패스가 잡았다. 치환이 앵커와 같으면 아무것도
        # 안 심긴 채 명령이 돌아 「생존 … 이것은 판정이다」가 난다(실측).
        return verdict("변이가 심기지 않았다 — 치환이 앵커와 같은 글이다."
                       " 심기지 않은 변이의 초록은 판정이 아니다 — 재지 못했다", 2)
    died, broke, restore_err = None, None, None
    try:
        target.write_bytes(mutated.encode("utf-8"))
        died = subprocess.run(cmd).returncode != 0
    except (OSError, Stopped) as err:
        broke = getattr(err, "strerror", None) or err
    finally:
        try:
            target.write_bytes(original)
        except OSError as err:
            restore_err = err.strerror or err
    if restore_err is not None:
        print("!! %s 를 원본으로 되쓰지 못했다 — 작업 트리가 더럽다" % path,
              file=sys.stderr)
        return verdict("복원 실패(%s) — `git diff -- %s` 를 보고 손으로 되돌린다."
                       " 판정은 **내지 않는다** — 재지 못했다" % (restore_err, path), 2)
    if died is None:
        return verdict("변이를 적용하거나 명령을 돌리지 못했다(%s) — 재지 못했다"
                       % broke, 2)
    if died:
        # **「죽음」은 판정이 아니라 관찰이다** — 빨강의 원인을 가르고서야 판정이 된다.
        # 생존 쪽은 대조판을 돌리지 않는다: 변이를 심은 채로 초록이 났다는 것이 이미
        # 「이 파일을 건드리는 것은 빨강을 만들지 않는다」의 증명이다(설계 계약 2번).
        blind = control_red(target, original, cmd)
        if blind is None:
            # `control_red` 가 `None` 을 내는 길은 **복원 실패 하나**다. 그러니 판정
            # 줄이 더러운 트리를 말해야 한다 — 바로 위 형제 경로가 그렇게 적는데
            # 이쪽만 안 적고 있었다(백지 패스 · `| tail -1` 만 읽는 호출자가 못 본다).
            return verdict("대조판의 복원이 깨졌다 — `git diff -- %s` 를 보고 손으로"
                           " 되돌린다(원본 끝에 개행 하나가 남았다). 판정은"
                           " **내지 않는다** — 재지 못했다" % path, 2)
        if blind:
            # **원인을 단정하지 않는다.** 대조판 한 판은 「건드리면 빨강」과 「언제나
            # 빨강」을 **가르지 못한다** — 가르려면 원본 그대로 세 번째 판이 든다.
            # 단정하면 오타 난 명령·`PYTHONPATH` 누락에 **틀린 방향**을 알려주게 되고
            # 그것이 이 저장소 최다 재발(`[R131-2]`)이다. 백지 패스가 잡았다.
            return verdict("이 명령은 **변이의 뜻과 무관하게** 빨갛다 — 재지 못했다."
                           " ⓐ 그 명령이 원본에서 초록인지 먼저 본다"
                           " ⓑ 대상 모듈만 돌린다 ⓒ 칸에 그 파일을 적는다", 2)
        return verdict("변이 **죽음** — 이 자리를 무는 테스트가 있다", 0)
    return verdict("변이 **생존** — 이 자리를 무는 테스트가 없다."
                   " 앵커가 유일했으므로 이것은 판정이다", 1)


def main(argv):
    """**어떤 길로도 판정 줄 없이 끝나지 않는다.**

    `except OSError` 만 잡던 동안 UTF-8 아닌 대상 파일이 `UnicodeDecodeError` 로
    새어 **역추적 + `rc=1`** 로 끝났다(실측 · 백지 패스) — `1` 은 「변이 생존」이라
    **재지 못한 것이 판정 코드로 나간다.** 이 자가 닫으려는 병과 같은 것이라
    바닥에서 전부 받아 `2` 로 돌린다.
    """
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _stop)
    try:
        if len(argv) == 4 and argv[1] == "--check":
            return check(argv[2], argv[3])
        if len(argv) >= 6 and argv[4] == "--":
            return apply_and_run(argv[1], argv[2], argv[3], argv[5:])
        return verdict("인자가 맞지 않는다 — 재지 못했다. %s" % USAGE, 2)
    except Stopped as err:
        return verdict("%s 로 끊겼다 — 복원은 돌았다 — 재지 못했다" % err, 2)
    except Exception as err:                        # noqa: BLE001 — 바닥 그물
        print("!! %s: %s" % (type(err).__name__, err), file=sys.stderr)
        return verdict("%s 로 끝났다 — 재지 못했다" % type(err).__name__, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
