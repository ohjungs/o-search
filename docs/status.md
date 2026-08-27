---
signal: GREEN
mode: night
plan: pagination-ui
phase: 개발
step: 2/5
attempt: 0
iteration: 97
night_iterations: 8
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 97 · 계획 015 착수)
ctx: 52% / 200k
rules: 1411a37
---

# 현재 상태

**계획 015 `pagination-ui` 를 열었다.** 계획 `docs/plan_pagination-ui.md`.
브랜치 `loop/pagination-ui` (기점 `716d245`).

**문제: 서버는 2페이지를 줄 수 있는데 화면에 가는 길이 없다.** `serve.py:217` 의 HTML
경로는 이미 `page` 를 받아 `offset` 을 건다 — `?q=X&page=2` 를 **손으로 치면 나온다**.
`_results()` 가 이동 링크를 안 그릴 뿐이라, 주소창을 편집할 줄 아는 사람만 11번째
결과를 본다. JSON 경로는 같은 문제를 이미 풀었다(`limit=PAGE_SIZE + 1` 로 11번째의
유무를 보고 `has_next`). **HTML 경로만 그 판정을 안 한다.**

**설계 phase 를 안 연다.** `design.md` 4절 트리거 넷(사용자 데이터 형태 / 공개 계약
파괴 / 의존성 / 보안 경계) 어디에도 안 걸린다 — 파일 하나, JSON API 불변,
`?q=&page=` 주소 계약은 이미 있는 것을 쓰는 쪽이다.

**미리 박아 둔 함정 둘** (계획 2절에 근거 있음):
- 새 `--fg-*` 토큰을 만들면 `design_check.PAIRS` 에도 적어야 하고 안 적으면 검사기가
  **종료 2(측정 불능)** 를 낸다 → 기존 토큰만 쓴다
- `PAGE_SIZE + 1` 로 받으면 "N건" 이 11 로 샌다 → 자른 뒤의 수를 쓴다

**하지 않을 것:** 총 건수 표시(COUNT 는 두 번째 전수 질의 — p95 에 얹힌다). 총 건수를
모르므로 **페이지 번호 목록도 안 만든다.** 이전/다음만이 지금 아는 정보로 정직하게
그릴 수 있는 것이다. `_parse()`·`PAGE_SIZE`·`MAX_PAGE`·JSON 응답도 안 건드린다.

다음 반복은 **스텝 2(개발)** — RED 를 먼저 본다.

## 직전 계획 (014 `crawl-politeness`) — DONE

예의 계약이 워커 경계를 못 넘어 새던 구멍 2건을 닫았다. A 워커 예외 뒤 간격
1.0 → **2.01초** · B 재시도 3회 0.0002 → **1.00초**. 단위 **296건** · e2e 4/4 ·
회귀 `perf_crawl` [차단] **10.30/s**. 기록은 `docs/e2e/crawl-politeness/result.md` ·
`plan_history_012.md` · `design_history_012.md` · `index.md` 14번.

**남긴 교훈 둘:** `**kw` 로 인자를 삼키는 가짜는 있을 수 없는 협력자를 흉내낸다
(거짓 초록 8건). 그리고 **"통과했다" 가 아니라 "무엇이 통과시켰나" 를 묻는다** —
첫 e2e 는 성공 가지가 미리 값을 걸어 둔 탓에 실패 가지를 재지도 않고 초록이었다.

## 다음 계획 (이번 계획이 DONE 되면)

`digest.md ## 판단 필요` 의 `[5]` — 재시도 간격이 **스킴별 robots** 만 본다.
`Frontier.interval(domain)` 공개 읽기를 내고 `_fetch_one` 이 둘의 `max` 를 쓰면 된다.
작다(계획 014 가 파일 목록 밖이라 미룬 것). 실측: `http` 만 `Crawl-delay: 5` 일 때
URL 사이는 5.000초인데 `https` 재시도는 1.000초.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
