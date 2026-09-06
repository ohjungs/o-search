---
signal: GREEN
phase: plan
step: 0/1
attempt: 0
iteration: 399
updated: 2026-09-06
ctx: 55
night_iterations: 194
night_red: 2
night_retries: 4
plan: noindex-entity-prefilter 계획 69 (계획 phase 완료 · 개발 1/1 대기)
---

## 현재 상태

**계획 69 `noindex-entity-prefilter` 를 열었다 — 계획 phase 완료 · GREEN.**
브랜치 `loop/noindex-entity-prefilter`(기점 `7fcd669` = `origin/main`) ·
계획서 `docs/plan_noindex-entity-prefilter.md` · 스텝 **1개**(개발 1/1) · 설계 없음.
이번 반복은 **계획서와 기록 문서만** 만들었다 — `src/`·`tests/`·`e2e/`·`README.md`
**0줄**.

## 이번 phase 가 산 것

**아홉 계획 만에 제품에 착지하는 계획이다.** 계획 60~68 은 전부 문서·사양 인용·검사
가드였고 `src/` 를 0줄 고쳤다. 계획 69 가 고칠 자리는 `src/websearch/extract.py` 의
`is_noindex()` 사전 필터와 `src/websearch/indexer.py:176` 의 제거 질의 —
**제품 2줄**이다.

**착수 근거를 오늘 다시 쟀다.** `<meta name="&#114;obots" content="noindex">` 에서
`is_noindex()` 는 **False**(십육진 `&#x72;obots`·`content="none"` 도 False)인데
`_MetaRobotsParser` 단독은 같은 문서에서 `['noindex']`·`['none']` 을 본다 — 막는 것은
파서가 아니라 `extract.py:204` 의 `if "robots" not in html_text.lower()` 한 줄이다.
정상 문서(`name="robots"`)는 True 라 오탐이 아니라 **누락**이고, 색인 거부는 크롤
윤리 축이라 오탐보다 무겁다.

**처방을 갈아 끼웠다.** `digest [4]` 가 적어 둔 원래 처방은 「필터를 뺀다」인데,
그러면 모든 페이지를 색인마다 한 번 더 파싱한다. 판별자를 `'&#'` 로 잡으면 십진·
십육진 문자참조가 전부 걸리고(`r` 을 내는 이름 있는 엔티티는 없다) `&amp;` 만 든
문서에는 `&#` 이 없어 **빠른 길이 유지된다** — 실측으로 둘 다 확인했다.
「기록된 답을 실행 전에 다시 재라」의 여섯 번째 적용이다.

**구멍이 두 자리인 것을 계획에 못박았다.** 색인 진입(`extract.is_noindex()`)만
고치면 이미 색인된 문서는 `LIKE '%robots%'` 가 못 집어 그대로 남는다.

## 남긴 것 (막지 않음)

`http-equiv` 변형(`digest [5]`)과 head 제한 오탐(`digest [4]`)은 별도 축이라 5절
「하지 않을 것」에 넣었다. 후보 목록의 src 착지 항목 중 **`<nav>` 인라인 연접**
(`digest [8]`)은 오늘 탐침이 서술을 **뒤집었다** — 링크 2개짜리 예시에서 내비
블록은 점수 5, 본문 문단은 6 으로 **본문이 이긴다**. 그 항목이 「여전히 내비가
이긴다」고 적은 것은 링크 수에 달린 진술이라, 여는 날 링크 수 축으로 다시 재야 한다.

## 검증

전수 **`Ran 628 tests` · `OK` · rc 0**(맨몸 1회) ·
`git diff --stat 7fcd669 HEAD -- src/ tests/ e2e/ README.md docs/specs/ data/` **빈손** ·
`metrics.md` 「반복 399」 = 이 파일 `iteration: 399`.

## 다음

**개발 phase 1/1.** 계획서 3절의 완료 기준 다섯을 그대로 받는다.
