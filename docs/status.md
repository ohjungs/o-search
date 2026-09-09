---
signal: DONE
phase: e2e
step: 0/0
attempt: 0
iteration: 530
updated: 2026-09-10
ctx: 65
night_iterations: 4
night_red: 0
night_retries: 0
plan: null
---

## 계획 85 `iter-third-witness` — 통과 · DONE

`docs/e2e/iter-third-witness/result.md`. 계획서는 `docs/plan_history_070.md` 로 아카이브했고
`index.md` 행은 `완료 · 통과`. 브랜치 `loop/iter-third-witness` 는 `main` 으로 병합했다.

## 이번 반복 — e2e · 트리는 그대로 두고 **자만 갈았다**

계획서 스텝 1 이 지정한 증거(`git show 9947049:docs/*.md`)를 **그날 아침 트리 통째로**
꺼냈다(`git archive`). 시드·명령·트리가 전부 같고 갈린 것은 `tests/test_docs.py` 하나뿐이다.

```
E0  2026-09-09 아침 트리 + 그날 자   Ran 70 · OK          ← 490·490·494 를 앞에 두고 조용
E1  2026-09-09 아침 트리 + 오늘 자   Ran 83 · failures=1  ← 「최대 494 ≠ iteration 490」
E2  오늘 트리(회전 흉내·최신 3항목)  Ran 83 · OK          ← 계획 2절의 「회전이 안 깬다」 참
E3  오늘 트리(항목 전부 삭제)        Ran 83 · failures=2  ← 하한 + 한 줄 신고(트레이스백 아님)
```

**E1 이 1건인 것도 값이다.** 오늘 자는 그날보다 13건 많은데(70 → 83) 그날 문서에 대해
나머지는 전부 조용했다 — 드리프트를 싸잡아 문 것이 아니라 **겨냥한 자리 하나만** 물었다.

**부분 복사를 안 했다.** 낮 검증에서 `src tests docs` 만 복사해 `SpecCitationTest` 3건이
거짓으로 빨갰던 장비 결함이 있었고, 계획 90 의 e2e 가 같은 자리에서 「대조군이 초록이
아니면 나머지를 못 읽는다」를 등재했다. `git archive` 로 추적 트리 통째를 꺼내 E0 이
`70 OK` 인 것을 먼저 보이고 나서 E1 을 읽었다.

새 e2e 파일은 **안 만들었다**(`rules/e2e.md` 3절) — `main..HEAD` 의 `src/`·`e2e/` diff 가
빈손이고 `e2e/*.py` 는 어제와 같은 22개다. 전수 **749 OK · rc 0**.

## 다음 반복 — 계획 탐색

밤의 첫 계획이 닫혔다(야간 3계획 상한 중 1). `discover.md` 1~5순위를 순서대로 돈다.
**5순위(보류)에 남은 것은 `userinfo-leak` 하나뿐이고 그것은 보안이라 밤이 못 댄다** —
1~4순위가 또 비면 짧은 경로 근거를 찾거나 정지한다.

## 한도

**statusLine 은 이 밤 내내 꺼져 있다** — 마지막 갱신이 31분 전이다(상한 10분).
**반복 상한에만 의존한다.** 마지막으로 읽힌 값 ctx 65 · 5h 9 · 7d 61.

`digest.md` 207줄(상한 200 — 무인은 회전하지 않는다, 계획 76 의 선).
`history_current.md` 267줄(상한 300).

## 아침 할 일 — 반복 527 이 남긴 넷 그대로

`perf_crawl` 기준선 · `deadline_e2e` 1초 하한 · `userinfo-leak` 패치 적용 판단 ·
`status.md` 본문 드리프트를 잴 것인가(digest 후보 등재). 이 반복은 아무것도 안 정했다.
