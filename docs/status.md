---
signal: GREEN
phase: 개발
step: 0/2
attempt: 0
iteration: 441
updated: 2026-09-07
ctx: 62
night_iterations: 8
night_red: 0
night_retries: 0
plan: history-cap-guard
---

## 현재 상태

**계획 76 `history-cap-guard` 수립 (야간 2번째 계획).** 근거는 digest 후보 `[7]` 이고
**그 여는 조건이 오늘 밤 열렸다** — 「상한 초과가 두 번째로 사고를 내는 날」. 반복 440
실측: `history_current.md` 가 **383줄·20회**로 상한 둘을 다 넘긴 채 여섯 반복을 지났고
전수 664건이 그동안 조용했다. 스텝 2개 · `tests/test_docs.py` 한 파일 · `src/` 0줄.
**`digest.md` 200 상한은 일부러 안 잰다** — 그쪽 처방은 삭제라 야간이 스스로 못 푸는
RED 가 된다(오늘 digest 는 실제로 201줄이다). 다음은 개발 1/2.

## 탐색 기록 (8순위 전수 · 반복 441)

1 실패 0(**664 OK**) · 2 린트·타입체커 없음 · 3 코드 `TODO` 0(유일한 히트
`tests/test_indexer.py:789` 는 fixture 문자열) · 4 `docs/candidates.md` 없음 ·
5 보류 0 · 8 이슈 트래커 없음 · `docs/patches/` 비어 있음(없음).
**6순위에서 났다** — 후보 `[7]` 이 스스로 적어 둔 여는 조건이 오늘 밤 열렸다.
중복 5곳 확인: `index.md` 의 계획 38(손 회전)·45(기록 대조 못)·72(digest 회전 못)는
**상한을 재지 않는다** · 활성 계획 0 · 보류 0 · 패치 0.

## 닫힌 판단

- **`digest.md` 는 201줄이다** — 반복 440 의 회전 기록 한 줄이 상한 200 을 1줄 넘겼다.
  무인 모드는 삭제를 안 하므로 **무엇을 버릴지는 아침에 사람이 정한다**(야간 보고서).
  2026-09-07 의 삭제 위임은 그 한 건 한정이었고 `rules/docs.md` 3절 문장은 그대로다.
