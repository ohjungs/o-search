---
signal: DONE
mode: night
plan: crawl-politeness
phase: e2e
step: 6/6
attempt: 0
iteration: 96
night_iterations: 7
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 96 · 계획 014 완료)
ctx: 62% / 200k
rules: 1411a37
---

# 현재 상태

**계획 014 `crawl-politeness` 완료 (DONE).** `docs/digest.md ## 판단 필요` 의 `[high]` 2건을
한 계획으로 묶어 닫았다 — 뿌리(예의 계약이 워커 경계를 못 넘는다)와 파일이 겹쳤다.

| 구멍 | 착수 전 실측 | 목표 | e2e 실측 |
|---|---|---|---|
| A `Crawl-delay` 도메인의 첫 요청이 예외 → 다음 간격 | 1.0초 | ≥ 선언값 | **2.01초** (선언 2초) |
| B 연결 거부 도메인 1 URL → TCP 연결 3회 간격 | 0.0002초 | 각 ≥ 1.0초 | **1.00초** |

계획 `docs/plan_history_012.md` · 설계 `docs/design_history_012.md` ·
e2e `docs/e2e/crawl-politeness/result.md`. 브랜치 `loop/crawl-politeness` (기점 `cdbd842`).

**고른 것:**

- A: `RobotsCache.known_delay(url)` — **네트워크를 안 타는** 캐시 조회. 예외 가지가 이것으로
  이미 아는 간격을 건다. 성공·예외 두 가지가 같은 `_apply_delay()` 를 지난다
- B: `fetcher.fetch(url, before_send=None, retries=RETRIES)` — 발신 훅. 간격을 알고·재우고
  **재는** 것은 전부 `crawl._fetch_one` 의 클로저다. `sent_at` 은 **마지막 발신**이다
- 간격이 `MAX_DELAY` 를 넘으면 재시도를 안 한다(`retries=0`). 깎아서 때리지 않는다
- 새 주입 지점을 안 만들었다 — `crawl()`·`_fetch_one()` 시그니처 불변

**검증:** 단위 **296건** 전부 통과(269 → 296) · e2e 4/4 · 회귀 `perf_crawl` [차단]
**10.30/s**(기준선 9.0) · `crawl_delay_e2e` 종료 0. 변이는 제품 10종 + e2e 2종을 전부
무변이 기준선 위에서 셌고 **전부 잡혔다**.

## 이 계획이 남긴 값진 것 둘

**리뷰가 내 테스트에서 거짓 초록 8건을 꺼냈다.** 시그니처가 바뀔 때 가짜 fetch 10곳에
`**kw` 를 붙였는데, 그 가짜들은 `before_send` 를 **받고 안 불렀다** — 진짜는 요청이 나가면
반드시 부른다. 그 위에서 잰 간격은 전부 크롤러가 "요청이 안 나갔다" 로 읽는 상태의
값이었다. 얇은 래퍼 `sending()` 이 훅 계약까지 흉내내게 고쳤다.

**첫 e2e 는 구멍 A 를 못 봤다 — 통과했는데 변이도 통과했다.** 느린 도메인을 시드로 준 탓에
**성공 가지**가 먼저 간격을 걸었고 예외 가지는 재지도 않은 채 초록이었다. 느린 도메인을
링크로만 물어오게 바꿔 그 도메인 요청이 전부 예외로 끝나게 하자 변이가 잡혔다.
**"통과했다" 가 아니라 "무엇이 통과시켰나" 를 묻는다.**

## 다음 계획

`pagination-ui` — 검색 UI 에 페이지 이동을 붙인다. JSON API 는 이미 `page=` 를 받는다.
`e2e/design_check.py` 기준(JS 0B · 대비 4.5:1 · 360px)을 그대로 통과해야 한다.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
