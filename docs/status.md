---
signal: DONE
phase: e2e
step: 2/2
attempt: 0
iteration: 446
updated: 2026-09-07
ctx: 51
night_iterations: 13
night_red: 0
night_retries: 0
plan: history-cap-guard
---

## 현재 상태

**계획 76 `history-cap-guard` e2e 통과 → DONE** (`docs/e2e/history-cap-guard/result.md`).
시나리오 4/4 를 **실물 문서를 진짜로 밀어서** 재현했다(백업 → 변이 → 전수 → 복원, 매번
복원 확인). 전수 **672 OK** · 품질 4축 회귀 0(p95 1.60ms · ko 20/20 · 디자인 4축).

**시나리오 4 가 이 계획 자신의 근거 문장을 고쳤다** — 반복 440 을 「상한 **둘을** 다
넘긴 채」라고 다섯 자리에 적어 왔는데, 회전 직전을 되살려 먹이니 문 것은 **줄 수 축
하나**(383 > 300)다. **항목 20 은 정확히 상한이라 조용한 것이 맞다** — 이 계획이 스스로
못박은 「경계는 초과가 아니다」가 자기 근거 문장에 적용된 것이다. 계획서·`status`·
`index`·`digest`·`HistoryCapTest` docstring 다섯 자리를 고쳤다. **근거는 안 흔들린다**:
넘긴 축이 하나여도 전수 664건이 여섯 반복 조용했고 이 못은 그 상태에서 빨개진다.

다음은 아카이브(`rules/docs.md` 4절) — `plan_history_062.md` 로 옮기고 명부·digest 갱신.

## 닫힌 판단

- **`digest.md` 는 201줄이다** — 반복 440 의 회전 기록 한 줄이 상한 200 을 1줄 넘겼다.
  무인 모드는 삭제를 안 하므로 **무엇을 버릴지는 아침에 사람이 정한다**(야간 보고서).
  아카이브가 한 줄을 더 쓰면 202줄이 된다 — 그것도 아침 몫으로 함께 적는다.
- **`.context-state.json` 이 낡았다**(반복 445 실측 32분) — statusLine 이 꺼진 것으로
  보고 `SKILL.md` 대로 **반복 상한에만 의존**한다. 마지막 값은 51/30/45 로 전부 여유.
