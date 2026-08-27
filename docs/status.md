---
signal: GREEN
plan: domain-key
mode: night
phase: 계획
step: 1/5
attempt: 0
iteration: 107
night_iterations: 18
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 107 · 계획 017 열었다)
ctx: 50% / 200k
rules: 1411a37
---

# 현재 상태

**계획 017 `domain-key` 를 열었다.** 계획 `docs/plan_domain-key.md`.
브랜치 `loop/domain-key` (기점 `677ed3e`).

**문제: 대소문자 하나로 예의 계약이 통째로 빠져나간다.** 도메인 열쇠를 날 `netloc`
으로 쓰는데(`frontier.py:57` · `crawl.py:108`) 호스트는 대소문자 무관이고 `:80`/`:443`
은 기본 포트다. **진짜 크롤 루프 실측**: `Crawl-delay: 3` 을 선언한 서버가 `LOCALHOST`
와 `localhost` 링크 탓에 **2밀리초 안에 요청 4개**를 받는다(같은 `robots.txt` 를 두 번
받는 것 포함). 대조군(`localhost` 두 번째 페이지)은 3.009초로 제대로 기다린다.
**절대 조건 위반이다** — 그리고 014·016 이 닫은 구멍들과 달리 **아무것도 잘못되지
않아도** 열린다. 사이트가 자기 링크에 호스트를 대문자로 쓰기만 하면 된다.

**설계 phase 를 안 연다.** `design.md` 4절 트리거 넷 어디에도 안 걸린다 — `Frontier`
와 `RobotsCache` 는 내부 계약이고, 방향은 **더 기다리는 쪽**이라 절대 조건과 같은 편이다.

**함정 하나** (계획 2절에 실측 근거 있음): `urlsplit(...).port` 는 `:abc`·`:99999` 에
**ValueError 를 던진다.** 지금 `netloc` 은 절대 안 던지므로 그것을 쓰면 **없던 크래시
경로**가 생긴다 — 문자열로만 가른다. 기대 6이 그것을 잰다.

**하지 않을 것:** URL 정규화(digest `[5]`). `http://A.com/` 과 `http://a.com/` 은 이
계획 뒤에도 두 번 수집되고 두 행으로 저장된다 — 여기서 고치는 것은 **예의 계약이 세는
단위** 하나뿐이다. URL 동일성은 크롤 **양**의 문제고 이것은 크롤 **윤리**의 문제다.

## 직전 계획 (016 `retry-interval`) — DONE

**계획 016 `retry-interval` DONE.** 브랜치 `loop/retry-interval` (기점 `5e7b525`).
계획서는 `docs/plan_history_014.md`, e2e 기록은 `docs/e2e/retry-interval/result.md`,
색인은 `docs/index.md` 16번.

**한 서버인데 두 경로가 다른 값을 쓰고 있었다.** `robots.txt` 는 스킴별 문서라
`_fetch_one` 이 `robots.delay(url)` 만 보면 `http` 가 선언한 5초를 모른 채 `https`
재시도를 **1초**로 냈다 — 프런티어는 netloc 단위로 모아 5초를 알고 있는데도. 그리고
재시도가 나가는 상황은 서버가 이미 아플 때다. 덜 조심할 자리로 최악이었다.

답은 **바닥값을 제출 시점에 메인 스레드가 읽어 넘기는 것**이다 —
`_fetch_one(url, robots, now, floor)`. `Frontier._interval` 은 이미 있던 메서드라
**밑줄만 뗐다**. 워커는 여전히 `Frontier` 를 안 만진다(동시화 계약 4).
e2e 실측 **5.01초**(고치기 전 1.0) · 대조군 **1.00초**로 남의 값이 안 샌다 ·
`perf_crawl` [차단] **10.27/s**(기준선 9.0) · 단위 **323건**.

`robots.delay` 를 스킴 무관으로 바꾸지 않았다 — 없는 선언을 있는 것처럼 읽는 쪽이
사양 위반이다. 우리는 **더 기다리기만** 한다.

**남긴 교훈 셋:**
- **가짜가 문제를 표현조차 못하고 있었다.** `FakeRobots` 가 **netloc** 으로 캐시해
  `http://b.test` 와 `https://b.test` 가 한 칸을 나눠 썼다 — 진짜는 `스킴://netloc`
  이다. 있을 수 없는 협력자 위에서는 이번 버그를 **재현할 수조차** 없었다 (digest `[6]`)
- **감시 대상을 상수로 바꿔치우면 재려던 시나리오가 사라진다.** 계약 4 테스트가
  `mock.patch.object` 로 `interval` 을 람다로 갈아 끼우고 있었다. 진짜 메서드를 감싸는
  방식으로 다시 쓰고, **감시한 5개가 실제로 다 불렸는지**까지 단언한다(공집합 방지)
- **재려는 상황이 안 만들어지는 배선이 있다.** 다른 e2e 는 전부 임시 포트를 URL 에
  달지만, 포트를 달면 `http://h:8001` 과 `https://h:8002` 는 **netloc 이 갈려** 이번
  상황 자체가 안 생긴다. 기본 포트라 netloc 에 안 실릴 때만 한 도메인이다

## 다음 계획 (후보)

1. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기
2. `Ctrl-C` 최악 대기(digest `[4]`·`[6]`) — 진짜 답은 `--deadline` 이거나 워커가
   주기적으로 보는 중단 플래그다. 016 이 최악값을 키웠다

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
