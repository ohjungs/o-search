#!/bin/zsh
# 계획 브랜치를 main 에 병합한다 — **전수가 초록일 때만 푸시한다.**
#
# **왜 스크립트인가.** 이 절차를 매번 손으로 조립하다 2026-09-11 에 사고가 났다:
# `... && 전수 ; git push` 처럼 연쇄가 한 번 끊겨 **전수가 실패했는데 푸시가 됐다.**
# 그날은 실패 원인이 문서 상한이라 무해했지만, 구조는 「빨간 main 을 민다」였다.
# 손으로 조립하는 절차는 언젠가 반드시 한 번 틀린다 — 그래서 파일로 옮긴다.
#
# **`set -e` 를 안 쓴다.** 여기서는 실패를 **삼키지 않고 분기**해야 하는데
# (worktree 정리는 실패해도 반드시 돈다), `set -e` 는 그 분기 전에 죽는다.
# 대신 모든 갈래에서 `rc` 를 명시적으로 확인한다.
#
# 사용: scripts/merge-to-main.sh [브랜치]      기본값은 현재 브랜치
# 테스트 주입: MERGE_TEST_CMD 로 전수 명령을 바꿀 수 있다(테스트가 빨간 갈래를 밟는다)
set -u

BRANCH="${1:-$(git branch --show-current)}"
case "$BRANCH" in
  loop/*) ;;
  *) echo "병합 대상이 아니다: $BRANCH — 계획 브랜치는 loop/<슬러그> 다" >&2; exit 2 ;;
esac

TEST_CMD="${MERGE_TEST_CMD:-PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=\$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests}"

git push -q origin "$BRANCH" || { echo "브랜치 푸시 실패" >&2; exit 1; }
git fetch -q origin || { echo "fetch 실패" >&2; exit 1; }

WT=$(mktemp -d)/mm
git worktree add -q "$WT" main || { echo "worktree 실패" >&2; exit 1; }

rc=0
(
  cd "$WT" || exit 1
  git merge --no-ff "origin/$BRANCH" -m "병합: ${BRANCH#loop/} 마감분" -q || exit 1
  # **전수는 병합 «결과» 에서 돈다.** 브랜치에서만 돌면 병합이 만든 충돌을 못 본다.
  OUT=$(eval "$TEST_CMD" 2>&1); trc=$?
  echo "$OUT" | tail -3
  # 이 한 줄이 사고의 자리다 — 여기서 끊기면 빨간 main 이 나간다.
  [ $trc -eq 0 ] || { echo "전수 RED — 푸시 안 함" >&2; exit 1; }
  git push -q origin main || exit 1
  echo "main 병합·푸시 ok"
)
rc=$?

# 정리는 **실패해도 반드시** 돈다 — 안 지우면 다음 실행의 worktree add 가 막힌다.
git worktree remove --force "$WT" 2>/dev/null
git checkout -q main 2>/dev/null && git pull -q --ff-only origin main 2>/dev/null

exit $rc
