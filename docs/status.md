---
signal: GREEN
mode: night
plan: retry-interval
phase: 개발
step: 2/5
attempt: 0
iteration: 102
night_iterations: 13
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 102 · 계획 016 착수)
ctx: 68% / 200k
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

**스텝 1(계획) 완료.** 다음 반복은 **스텝 2(개발)** — RED 를 먼저 본다(기대 1이
지금 코드에서 **1.0초**로 실패하는 것).

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

1. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
