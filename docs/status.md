---
signal: GREEN
plan: null
mode: night
phase: null
step: -
attempt: 0
iteration: 111
night_iterations: 22
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 111 · 계획 017 DONE)
ctx: 62% / 200k
rules: 1411a37
---

# 현재 상태

**계획 017 `domain-key` DONE.** 브랜치 `loop/domain-key` (기점 `677ed3e`).
계획서는 `docs/plan_history_015.md`, e2e 기록은 `docs/e2e/domain-key/result.md`,
색인은 `docs/index.md` 17번.

**같은 서버인데 표기가 다르면 남남이었다.** 열쇠가 날 `netloc` 이라
`http://a.test` · `http://A.test` · `http://a.test:80` 이 큐도 `_last_fetch` 도
`_delays` 도 따로 가졌다 — 2초를 선언한 서버가 **2밀리초 안에** 요청 넷을 받았고
`robots.txt` 도 표기 수만큼 받았다. 절대 조건 위반이다.

답은 열쇠를 만드는 **한 곳짜리 헬퍼** `urls.domain_key(url)` — 호스트 소문자화 +
**스킴별** 기본 포트 제거. 호출부는 셋이었다(`frontier.add` · `crawl` 제출 직전 ·
`robots._base`) — digest 의 처방이 적어 둔 "두 호출부" 는 틀렸다.
**`urlsplit(...).port` 를 안 쓴다**: `:abc`·`:99999` 에 ValueError 를 던져
**열쇠를 만들다 크롤을 죽인다.** 문자열로만 가른다.

**백지 리뷰가 진짜 크래시 1건을 잡았다** — 가드가 `domain_key` 에만 들어갔고
`robots._base`·`can_fetch`·`links.extract` 는 여전히 날 파싱을 하고 있었다. 최악의
자리는 예외가 나는 곳이 아니라 **잡는 곳**이었다(`_store_result` 의 `except` 가
복구하려 부른 `known_delay` 가 두 번째로 던지면 아무도 안 잡는다). 파싱을 던지지 않는
`urls._split` 한 곳으로 모아 닫았다. 교훈은 `docs/digest.md [7]` 마지막 항목.

**e2e 5/5.** 서버 수신 간격 **2.01초**(고치기 전 0.002) · 같은 서버 `robots.txt`
**1회**(고치기 전 2~3) · 대조군(기본이 아닌 포트) **1.00초**로 안 묶인다 ·
측정 불능 **종료 2** · `perf_crawl` [차단] **10.24/s**.
**변이 3종이 서로를 못 대신한다** — 날 `netloc`·포트 통째 제거·`robots._base` 만
되돌리기. 단위 **354건 OK**, 회귀 e2e 다섯 전부 0.

**이 계획이 안 고친 것:** URL 정규화(digest `[5]`). `http://A.test/p` 와
`http://a.test/p` 는 지금도 **두 번 수집되고 두 행으로 저장된다** — 고쳐진 것은
**예의 계약이 세는 칸** 하나뿐이다.

## 다음 계획 (후보)

1. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기
2. `Ctrl-C` 최악 대기(digest `[4]`·`[6]`) — 진짜 답은 `--deadline` 이거나 워커가
   주기적으로 보는 중단 플래그다. 016 이 최악값을 키웠고 017 은 안 건드렸다
3. URL 정규화(digest `[5]`) — `store`·`_seen`·리다이렉트·끝 슬래시·퍼센트 표기가
   한꺼번에 걸린다. 크롤 **양**의 문제라 윤리 축보다 급하지 않다

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
