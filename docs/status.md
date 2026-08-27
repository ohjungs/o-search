---
signal: GREEN
mode: night
plan: crawl-politeness
phase: e2e
step: 6/6
attempt: 0
iteration: 95
night_iterations: 6
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 95 · 리뷰 phase 완료)
ctx: 50% / 200k
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

**스텝 4(테스트 phase) 완료.** 6개 카테고리로 훑어 갭 3건을 찾아 메웠다
(289 → **294건**, 전부 통과). `crawl_delay_e2e.py` 종료 코드 0 재확인.

- 갭 ⑥: **예외 가지가 `_apply_delay` 를 이번에 처음 지난다** — 상한 초과 도메인을
  버리는 분기에 테스트가 0이었다(`TestUnkeepableDelayFoundOnFailure`, 긍정 짝 포함)
- 갭 ②: `MAX_DELAY` **정확히 그 값**. `set_delay` 는 `>` 로 버리고 `_fetch_one` 은 `<=` 로
  재시도한다 — 부등호 둘이 어긋나면 갈라지는 자리다. 30.0 / 30.1 을 짝으로 고정
- 갭 ②: `Crawl-delay: 0` 이 하한 1초를 뚫는지 (재시도 경로에서도)
- 변이 3종 추가 확인: 예외 가지 `_apply_delay` 삭제→2 · `<=`→`<`→1 · 하한 제거→2

**스텝 5(리뷰) 완료.** `rules/review.md` 대로 **별도 백지 세션**(diff + 소스만, `docs/` 차단)에
넘겼다. 지적 4건, 자기 점수 86/100. 그 세션이 294건 통과와 `crawl_delay_e2e` 를 독립으로 재확인했다.

- **채택 ②** `_fetch_one` 이 훅을 한 번도 안 불렀는데 `now()` 를 발신 시각으로 지어냈다 —
  `Request()` 생성 실패(스킴 없는 시드)는 **요청이 안 나간 것**이라 쿨다운을 태우면 안 된다.
  `sends[-1] if sends else None` 로 고쳤다(`mark_sent` 는 None 을 무시한다).
  robots 차단 가지·`fetcher` docstring 과 같은 계약이 됐다
- **채택 ③** `crawl()` docstring 의 Ctrl-C 문단이 낡았다 — 재시도 사이 간격 대기가 붙어
  최악이 요청당 30 → **90초**다. 값을 치른 이유(윤리 > 성능)까지 적었다
- **보류 ①** → `digest.md`. 재시도 간격은 **스킴별 robots** 만 본다. 탐침: `http` 만
  `Crawl-delay: 5` 를 걸면 URL 사이는 5.000초로 맞는데 `https` URL 의 **재시도는 1.000초**
  간격이다. 절대 조건 위반은 아니다(https 쪽 선언이 없다). 고치려면 `Frontier.interval()`
  공개 읽기가 필요해 **이번 계획 파일 목록 밖** — 계획의 "하지 않을 것" 이라 미뤘다
- **버림 ④**(확신 60, 통과선 미달) — 다만 그 아래 관찰은 값이 있어 `digest.md` 에 적었다

**리뷰가 내 테스트에서 거짓 초록 8건을 꺼냈다.** ②를 고치자 7건이 깨졌는데 **제품이 아니라
가짜가 틀렸다** — 시그니처가 바뀔 때 가짜 10곳에 `**kw` 를 붙였고, 그 가짜들은 `before_send`
를 받고 **안 불렀다**. 진짜 fetcher 는 요청이 나가면 반드시 부른다. 즉 그 위에서 잰 간격은
전부 크롤러가 "요청이 안 나갔다" 로 읽는 상태에서 나온 값이었다. 얇은 래퍼 `sending()` 하나로
훅 계약까지 흉내내게 고쳤다. **294 → 296건 전부 통과**(새 테스트 `TestNoSendMeansNoClock`,
부정·긍정 짝). 변이 2종 확인: `now()` 로 되돌리기 → 1건, `sending()` 이 훅을 안 부르게 → 8건.

다음 반복은 **스텝 6(e2e)** — `docs/e2e/crawl-politeness/result.md` 시나리오 4개.

## 다음 계획 (이번 계획이 DONE 되면)

`pagination-ui` — 검색 UI 에 페이지 이동을 붙인다. JSON API 는 이미 `page=` 를 받는다.
`e2e/design_check.py` 기준(JS 0B · 대비 4.5:1 · 360px)을 그대로 통과해야 한다.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
