---
signal: GREEN
mode: night
plan: crawl-politeness
phase: 테스트
step: 4/6
attempt: 0
iteration: 93
night_iterations: 4
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 93 · 스텝 3 완료 — 문제 B 닫힘)
ctx: 71% / 200k
rules: 1411a37
---

# 현재 상태

**계획 013 `crawl-politeness` 를 열었다.** `docs/digest.md ## 판단 필요` 의 `[high]` 2건을
한 계획으로 묶었다 — 뿌리(예의 계약이 워커 경계를 못 넘는다)와 파일
(`src/websearch/crawl.py` 의 `_fetch_one`·`_store_result`)이 겹친다.

| 구멍 | 실측 | 목표 |
|---|---|---|
| A `Crawl-delay: 5` 도메인의 첫 요청이 예외 → 다음 간격 | **1.0초** (대조군 5.0) | ≥ 5.0초 |
| B 연결 거부 도메인 1 URL → TCP 연결 3회 간격 | **0.0002초** | 각각 ≥ 1.0초 |

계획 `docs/plan_crawl-politeness.md`. 브랜치 `loop/crawl-politeness` (기점 `cdbd842`).

**설계 완료** → `docs/design_crawl-politeness.md`. 고른 것:

- A: `RobotsCache.known_delay(url)` — **네트워크를 안 타는** 캐시 조회. 예외 가지가 이것으로
  이미 아는 간격을 건다. 성공·예외 두 가지가 같은 `_apply_delay()` 를 지난다.
  (버린 것: 워커가 안 죽게 만들기 = 스택을 잃는다 / 발신 전 선반영 = 동시화 계약 4 를 깬다)
- B: `fetcher.fetch(url, before_send=None, retries=RETRIES)` — 발신 훅. 간격을 알고 재우고
  **재는** 것은 전부 `crawl._fetch_one` 의 클로저다. `sent_at` 은 **마지막 발신**이 된다.
  (버린 것: fetcher 안 sleep = 마지막 발신을 **추정**하게 된다 / 재시도를 프런티어로
  승격 = 옳지만 크다 → `digest.md` 후보)
- 간격이 `MAX_DELAY` 를 넘으면 **재시도를 안 한다**(`retries=0`). 깎아서 때리지 않는다
- **새 주입 지점을 안 만든다** — 기존 `mock.patch("websearch.crawl.time.sleep")` 패턴을 쓴다.
  `crawl()`·`_fetch_one()` 시그니처 불변

## 이미 한 것

**스텝 2(문제 A) 완료** · 커밋은 아래. RED 를 먼저 봤다 — `1.0 not greater than or equal
to 5.0`, digest 가 적은 실측과 같은 값이다. 그 뒤 `RobotsCache.known_delay()`(네트워크
없는 캐시 조회)와 `crawl._apply_delay()`(성공·예외가 함께 지나는 자리)를 넣어 닫았다.
`_store_result` 가 `robots` 를 받도록 인자가 하나 늘었다(private, 호출부 1곳).
**269 → 276건 전부 통과.** 변이 3종이 전부 잡힌다(무변이 기준선 `OK` 를 먼저 잡고 셌다).

**스텝 3(문제 B) 완료.** `fetcher.fetch(url, before_send=None, retries=RETRIES)` 를 넣고
간격을 알고·재우고·**재는** 일은 전부 `_fetch_one` 의 클로저가 한다. `sent_at` 이
**마지막 발신**이 됐다. 상한 초과 도메인은 `retries=0`.
**276 → 289건 전부 통과.** 변이 4종 전부 잡힌다.

**시그니처가 바뀌어 가짜 fetch 를 전부 고쳤다** — `tests/test_crawl.py` 10곳(`**kw`)과
`e2e/perf_crawl.py` 의 `exploding_fetch`. `websearch.crawl.fetcher` 를 통째로 Mock 하는
곳에는 `mf.RETRIES` 도 심어야 한다(모듈이 Mock 이면 `fetcher.RETRIES` 도 Mock 이다).

다음 반복은 **스텝 4(테스트 phase)** — 새로 쓰는 곳이 아니라 **빠뜨린 것을 찾는** 곳이다.

## 다음 계획 (이번 계획이 DONE 되면)

`pagination-ui` — 검색 UI 에 페이지 이동을 붙인다. JSON API 는 이미 `page=` 를 받는다.
`e2e/design_check.py` 기준(JS 0B · 대비 4.5:1 · 360px)을 그대로 통과해야 한다.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
