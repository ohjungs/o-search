---
signal: GREEN
mode: night
plan: retry-interval
phase: e2e
step: 5/5
attempt: 0
iteration: 105
night_iterations: 16
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 105 · 리뷰 완료)
ctx: 50% / 200k
rules: 1411a37
---

# 현재 상태

**계획 016 `retry-interval` 을 열었다.** 계획 `docs/plan_retry-interval.md`.
브랜치 `loop/retry-interval` (기점 `5e7b525`).

**문제: 재시도만 스킴별 robots 를 보고, 프런티어가 아는 것을 모른다.** `_fetch_one`
(`crawl.py:37-38`)은 `robots.delay(url)` 로만 간격을 구하는데 그 값은 **그 스킴의
robots.txt** 것이다. 프런티어는 netloc 단위로 들고 단조 증가시키므로 `http://b.test`
가 선언한 5초를 `https://b.test` 에도 건다. 실측: URL 사이는 **5.000초**인데 `https`
재시도 3회는 **1.000초**. 절대 조건 위반은 아니지만(https robots 가 선언한 값이 없다)
**재시도 경로만 URL 사이 경로보다 덜 조심한다** — 재시도가 나가는 상황은 서버가 이미
아플 때다. 덜 조심할 자리로 최악이다.

**설계 phase 를 안 연다.** `design.md` 4절 트리거 넷 어디에도 안 걸린다 — `Frontier`
는 내부 계약이고, `_interval` 은 **이미 있는 메서드라 밑줄만 뗀다**. 간격을 올리는
방향뿐이라 절대 조건과 같은 쪽이다.

**함정 하나** (계획 2절에 근거 있음): 워커는 `Frontier` 를 만지면 안 된다(설계 계약 4).
바닥값은 **제출 시점에 메인 스레드가** 읽어 넘긴다 — `crawl.py:101` 은 이미 `domain`
을 손에 들고 있다.

**하지 않을 것:** `robots.delay` 를 스킴 무관으로 바꾸기 — `robots.txt` 는 스킴별로
다른 문서다. 없는 선언을 있는 것처럼 읽는 것은 사양을 어기는 쪽이고, 우리는
**더 기다리기만** 한다. `DOMAIN_INTERVAL`·`MAX_DELAY`·`RETRIES` 값도 안 건드린다.

## 이미 한 것

**스텝 2(개발) 완료.** RED 를 먼저 봤다 — `1.0 not greater than or equal to 5.0`,
digest `[5]` 가 적어 둔 실측과 **같은 숫자**다. `Frontier._interval` 의 밑줄을 떼고,
제출 시점에 메인 스레드가 읽어 `_fetch_one(url, robots, now, floor)` 로 넘긴다.
**311 → 315건 전부 통과** · 회귀 `perf_crawl` [차단] **10.25/s**(기준선 9.0) ·
`crawl_politeness` 0 · `crawl_delay` 0.

**가짜가 문제를 표현조차 못하고 있었다.** `FakeRobots._host` 가 **netloc** 으로 열쇠를
잡아 `http://b.test` 와 `https://b.test` 가 한 칸을 나눠 썼다 — 진짜 `RobotsCache` 는
`robots._base`, 즉 `스킴://netloc` 으로 캐시한다. **있을 수 없는 협력자**라 그 위에서는
이번 버그를 재현할 수조차 없었다(digest `[6]` 과 같은 부류). 진짜와 같은 열쇠로 고쳤고,
기존 호출 3곳의 키를 `"http://b.test"` 로 바꿨다 — 311건은 그대로 통과한다.

- 워커는 여전히 `Frontier` 를 안 만진다(계약 4). `crawl.py:101` 은 이미 `domain` 을
  손에 들고 있어 새로 계산할 것이 없다. **테스트로 못박았다** —
  `test_worker_never_touches_the_frontier` 가 스레드 이름을 모아 `{MainThread}` 인지 본다
- **올리기만 한다.** `floor` 는 이미 `DOMAIN_INTERVAL` 이상이고 `set_delay` 는 단조
  증가로만 쓴다. 대조군(`test_undeclared_domain_keeps_the_plain_floor`)이 선언 없는
  도메인은 **1.0 ≤ g < 2.0** 임을 잰다 — 없으면 "전부 5초로 재우기" 로도 통과한다
- `robots.delay` 를 스킴 무관으로 바꾸지 않았다. `robots.txt` 는 스킴별로 다른 문서다

**스텝 3(테스트 phase) 완료.** 갭 2건을 메웠다(315 → **322건**). ③격리·④flaky·⑤보안은
해당 없음(전역 없음·가짜 시계·입력 처리 변경 없음).

- 갭 ② (**9점**) **하한 보장의 자리가 호출부로 옮겨갈 뻔했다.** `floor` 를 도입하면서
  `max(DOMAIN_INTERVAL, ...)` 를 지웠는데, 오늘은 `frontier.interval()` 이 언제나 하한
  이상을 주지만 그 보장이 **한 곳에만** 있으면 더 작은 값을 넘기는 호출이 하나 생기는
  순간 조용히 사라진다. **하한은 컨셉의 절대 조건이다** — `max` 에 남기고 `floor=0.0`
  으로 직접 불러 1초가 지켜지는지 재는 테스트를 붙였다
- 갭 ⑥ (8점) **`Frontier.interval` 은 새 공개 읽기인데 직접 테스트가 0**이었다.
  `next`·`seconds_until_ready` 가 간접적으로 쓰지만 그 둘은 "언제 팝할까" 를 재는 쪽이라
  **값이 내려가지 않는다**는 성질은 아무도 단언하지 않았다 — `crawl` 이 이제 그 성질에
  기댄다. 단조성·0선언·상한초과·도메인 격리 6건
- **가드 위치를 먼저 확인했다**(digest `[7]`) — `tests/` 전체에 뒤에 코드가 오는 가드 없음
- 변이 5종 전부 잡힘: `floor` 미사용→1 · `DOMAIN_INTERVAL` 삭제→1 · `interval` 기본값
  0→23 · `set_delay` 단조성 삭제→16 · 제출 시 하한 고정→1
- 회귀: `perf_crawl` [차단] **10.30/s** · `crawl_politeness` 0 · 낮은 갭 1건 digest `[6]`

**스텝 4(리뷰) 완료.** 백지 세션(diff + 소스만, `docs/` 차단)에서 지적 4건. 3건은
고쳤고(322 → **323건 통과**), 1건은 **이 계획이 연 것이 아니라서** digest 로 넘겼다.

- **#1 [high] — 도메인 열쇠가 날 `netloc` 이다.** `http://b.test` · `http://B.test` ·
  `http://b.test:80` 이 서로 남남이라 탐침에서 셋이 **t=1000.000 에 동시 발신, 간격
  0.000초**. 선언한 `Crawl-delay: 5` 가 나머지 둘에는 아예 안 걸린다. 016 diff 밖이고
  착수 전 코드에서도 같은 값이 나온다. **열쇠를 바꾸면 도메인 동일성이 바뀌어 계약
  3(in-flight)·`_seen`·`store.has` 가 한꺼번에 움직인다** — 014 가 그랬듯 자기 RED 와
  자기 e2e 를 가진 별도 계획이 맞다. digest `[high]` 에 실측과 처방까지 적었다
- **#2 — 스킴 순서에 따라 안 막히는 경우가 있다.** `https` 를 먼저 치면 그때는
  프런티어가 `http` 의 선언을 아직 모른다. 닫으려면 추측성 robots.txt 왕복이 필요한데
  그쪽이 **덜 조심하는** 쪽이다. **보장되는 것만 못박았다** —
  `test_unseen_scheme_first_still_holds_the_floor`(어떤 순서든 1초 바닥은 산다)
- **#3 — `interval` 독스트링이 "안 내려간다" 를 무조건으로 읽히게 썼다.** 예외가 정확히
  하나 있다(상한 초과로 버려진 도메인은 `_delays` 에서 빠져 하한으로 읽힌다). 그 예외와
  "읽기 전에 살아 있는지 본다" 를 독스트링에 박았다
- **#4 — 계약 4 테스트가 감시 대상을 상수로 바꿔치우고 있었다.** `mock.patch.object` 로
  `interval` 을 람다로 갈아 끼워 **재려던 시나리오 자체를 바꿨다**. 진짜 메서드를
  감싸는 방식(`contextlib.ExitStack`, 5개 전부)으로 다시 썼고, 스레드 집합이
  `{MainThread}` 인지에 더해 **감시한 5개가 실제로 다 불렸는지**(공집합 방지)를 단언한다
- 변이 확인: 바닥값을 워커 안에서 읽게 바꾸면 #4 테스트가 **빨강**이 된다

다음 반복은 **스텝 5(e2e)** — 계획 5절의 시나리오 넷, 사이트 로그 쪽에서 잰다.

## 직전 계획 (015 `pagination-ui`) — DONE

**서버는 진작부터 2페이지를 줄 수 있었다.** `?q=X&page=2` 를 손으로 치면 나왔다 —
없던 것은 **화면에 그려진 길**이었다. JSON 경로가 이미 쓰던 탐침 한 줄
(`limit=PAGE_SIZE + 1`)을 `_page_hits`·`_has_next` **한 벌**로 뽑아 두 경로가 나눠 쓴다.
COUNT 를 안 더하므로 p95 에 얹히는 것이 없고(9.22ms), 총 건수를 모르니 **번호 목록도
안 그린다**. 단위 **311건** · e2e 4/4 · `design_check` 0(JS 0B 유지).
기록은 `docs/e2e/pagination-ui/result.md` · `plan_history_013.md` · `index.md` 15번.

**남긴 교훈 둘:**
- **`if __name__ == "__main__"` 뒤에 클래스를 붙이면 그 테스트는 존재하지 않는다.**
  직접 실행 55건 · `discover` 70건 — **양쪽 다 초록**이라 사라진 신호가 없었다.
  백지 리뷰가 아니었으면 못 봤다 (digest `[7]`)
- **측정 불능(2)과 빨강(1)을 안 가르면 회귀가 "못 쟀다" 로 보고된다.** e2e 첫 판은
  링크 개수를 가드에 넣어 **기능 삭제와 문서 부족이 같은 코드 2**로 나왔다. 갈 곳이
  있는지는 화면이 아니라 **독립된 계측기**(JSON API)로 먼저 묻는다

## 다음 계획 (후보)

1. **도메인 열쇠 정규화** (digest `[high]`, 이번 리뷰 #1) — 호스트 소문자화 + 기본 포트
   제거를 **한 곳짜리 헬퍼**로. 같은 서버를 동시에 때리는 것을 닫는다. 절대 조건 쪽이라
   1순위다
2. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
