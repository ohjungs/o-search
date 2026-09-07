---
signal: GREEN
phase: 계획
step: 0/0
attempt: 0
iteration: 447
updated: 2026-09-07
ctx: 51
night_iterations: 14
night_red: 0
night_retries: 0
plan: null
---

## 현재 상태

**계획 76 `history-cap-guard` 아카이브 완료 — `plan_history_062.md`.** 명부(`index.md`)에
다섯 phase 의 결론을 적었다. 야간 **두 번째** 계획이 닫혔다(첫째는 75 `project-const-drift`).

`history_current.md` 는 **회전 안 한다** — 오늘 255줄·14회로 두 축 모두 상한 안이고,
**그 판정을 오늘부터 사람이 아니라 `HistoryCapTest` 가 한다.** 넘기는 날 전수가 빨개진다.

## 닫힌 판단

- **`digest.md` 는 201줄이다** — 반복 440 의 회전 기록 한 줄이 상한 200 을 1줄 넘겼다.
  무인 모드는 삭제를 안 하므로 **무엇을 버릴지는 아침에 사람이 정한다**(야간 보고서).
  **이 계획이 그 상한은 일부러 안 쟀다** — 처방이 삭제라 야간이 스스로 못 푸는 RED 가
  되기 때문이고, 「무인이 digest 를 회전해도 되는가」는 사람이 정할 규약이다(digest `[7]`).
- **`.context-state.json` 이 낡았다**(반복 445 실측 32분) — statusLine 이 꺼진 것으로
  보고 `SKILL.md` 대로 **반복 상한에만 의존**한다. 마지막 값은 51/30/45 로 전부 여유.
