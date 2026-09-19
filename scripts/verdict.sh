#!/bin/zsh
# 아무 명령이나 감싸서 **판정과 종료 코드를 stdout 의 마지막 한 줄**로 다시 찍는다.
#
# 사용: PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests
#       PYTHONPATH=src scripts/verdict.sh python3 e2e/crawl_e2e.py
#
# **환경 변수는 래퍼 «앞»에 둔다.** `scripts/verdict.sh PYTHONPATH=src python3 …` 는
# 안 된다 — `"$@"` 로 넘어온 `VAR=val` 은 배정이 아니라 **명령 이름**으로 읽힌다.
# 앞에 두면 쉘이 래퍼의 환경에 넣고 자식이 그대로 물려받는다(실측). 틀리게 쓰면
# `command not found: PYTHONPATH=src` 와 `rc=127` 이 **마지막 줄에** 찍힌다 —
# 조용히 틀리지 않으므로 낱말을 파싱해 주는 코드를 넣지 않는다.
#
# **왜 이것이 존재하나.** `digest ## 반복 실패` 최다 재발 항목(「러너의 판정 줄을
# 가린다」, 37회)을 막으려던 시도 셋이 전부 **문장**이었고 셋 다 뚫렸다. 고치는 것은
# 손버릇이 아니라 **출력의 순서**다 — 판정이 마지막 줄에 있으면 가장 자주 붙는
# 손(`tail`)이 오히려 판정만 남긴다. 방아쇠를 없애는 대신 **무해하게** 만든다.
#
# 사라지는 것이 셋이고 원인이 다르다(`docs/design_verdict-last.md`):
#   ① `Ran/OK` 줄 — 판정은 stderr(무버퍼)인데 테스트 stdout 은 파이프 아래 블록
#      버퍼라 끝에 한꺼번에 밀려 나온다. **순서 역전**이고, `-b` 는 초록 절반만 덮는다
#   ② 판정 전부 — `2>/dev/null`. 판정이 stderr 라 재지향이 통째로 버린다
#   ③ `rc` — 파이프 오른쪽의 종료 코드가 `$?` 가 된다. **출력 길이와 무관**하다
#
# **출력을 줄이지 않는다.** 방아쇠 「출력이 길다」의 나머지 절반은 「빨간 쪽이 길다」이고
# 그건 줄이면 안 되는 쪽이다. 여기가 바꾸는 것은 길이가 아니라 **순서**다.
#
# **판정은 stdout 으로 찍는다** — `print` 의 기본이 stdout 이라는 것이 ②를 덮는
# 유일한 이유다. stderr 로 찍으면 래퍼가 원래 버그를 그대로 물려받는다.
#
# ponytail: zsh 전용이다(`pipestatus`). 이 저장소의 유일한 다른 쉘 스크립트가 이미
# zsh 고, `bash` 분기를 두면 아무 테스트에도 안 걸리는 코드가 된다.
# ponytail: 판정 낱말이 `unittest` 표기에 묶여 있다. e2e 스크립트는 그 낱말을 안 쓰므로
# 판정 칸이 비고 `rc=N` 만 남는다 — 거기서 재는 값이 `rc` 라 족하다.
set -u

[[ $# -ge 1 ]] || { print -u2 -- "감쌀 명령이 없다: scripts/verdict.sh <명령...>"; exit 2 }

log=$(mktemp)
trap 'rm -f "$log"' EXIT INT TERM

# 흐르는 쪽을 골랐다 — `>log` 후 `cat` 판과 판정 축에서 동률이고, 갈린 것은 실행 중
# 화면뿐이다. 분 단위 e2e 에서 「멈춘 건가」를 구별할 수 있어야 한다.
"$@" 2>&1 | tee "$log"
rc=${pipestatus[1]}   # 1 번은 감싼 명령이다. `tee` 의 것(늘 0)을 실으면 실패가 통과로 보인다

print -r -- "── $(grep -E '^(Ran |OK|FAILED)' "$log" | tr '\n' ' ')rc=$rc"
exit $rc
