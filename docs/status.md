---
signal: GREEN
phase: 개발
step: 0/3
attempt: 0
iteration: 499
updated: 2026-09-09
ctx: 55
night_iterations: 1
night_red: 0
night_retries: 0
plan: iter-third-witness
---

## 계획 85 `iter-third-witness` — 탐색이 세 밤 만에 근거를 찾았다

`docs/plan_iter-third-witness.md`. 브랜치 `loop/iter-third-witness`.

**근거는 지어낸 것이 아니라 이 저장소가 지금 들고 있는 상태다.** 어제 등재한
`digest ## 반복 실패` 39행(「`iteration` 은 status·metrics 가 «나란히» 틀리면 아무도
못 잡는다」)이 **오늘 실물에 그대로 있었다**:

```
status.iteration 490 · metrics.반복 490   ← 서로 같다 → IterationSyncTest 초록
history_current.md `### 반복` 최대   494
전수 719건 OK · rc 0                       ← 아무도 안 문다
```

`loop/backoff-429` 가 494 이전 지점에서 갈라져 두 숫자를 함께 싣고 494 마감 **뒤에**
병합됐다(`ad1f674` 16:22 vs `d05ea2a` 15:06). 등재된 것과 **같은 병합 모양**이다.

**처방을 실측이 뒤집었다.** digest 39행은 셋째 증인을 「마지막 `반복 NNN`」이라 적었는데
오늘 실물의 **마지막 항목은 490 이고 최댓값은 494** 다 — 적힌 대로 옮겼으면 틀린 자를
세울 뻔했다. 붙들 것은 **최댓값**이다.

## 이번 반복(계획 phase)이 한 것

- 계획서 작성. 스텝 3개(자 세우기 → 기록 정정 → 변이·등재). 설계 없음(트리거 대조는 6절).
- **반복 번호를 490 → 499 로 손으로 맞췄다.** 494 + `backoff-429` 의 네 반복(495~498)
  다음이 499 다. 자가 서는 순간 실물이 빨간 것과 **자에 이빨이 있는 것은 다른 명제**라,
  후자는 스텝 1 의 `git show 9947049:docs/*.md` 측정과 스텝 3 의 변이가 증명한다.
- **회전 1건** — `history_current.md` 299줄(상한 300)이 이번 append 를 못 받아 반복
  476~486 을 `history_078.md` 로 밀었다. 밀고 나서 180줄 · 항목 10. `digest` 명부에 한 줄.

## 다음 스텝 — 개발 1/3

`tests/test_docs.py` 의 `iter_gap` 에 `history_text` 인자를 더하고 `IterGapTest` 에
갈래(머리 없음 · 최댓값 불일치)를 붙인다. 호출자는 같은 파일 안 2곳뿐이다.

## 아침 할 일 — 어제와 같은 하나

**패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch` (382줄 ·
구현 + 단위 + e2e · `git apply --check` 통과). 밤이 안 댄 이유는 「보안 — 항상 보류」다.
적용하면 `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을 준다(018 의 「보존」을
뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.

## 한도

`digest.md` **215줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선).
