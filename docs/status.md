---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 개발
step: 2/3
attempt: 0
iteration: 66
night_iterations: 3
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 66)
ctx: 82% / 200k
rules: rules/dev.md
---

# 현재 상태

**`crawl-throughput`(008) 개발 스텝 1/3 완료.** 브랜치 `loop/crawl-throughput`.
계획서 `docs/plan_crawl-throughput.md` · 설계 `docs/design_crawl-throughput.md`.
**다음은 개발 스텝 2/3 — 크롤 루프 동시 fetch.**

## 스텝 1이 만든 것과 찾은 것

`e2e/perf_crawl.py` 신규 (로컬 서버 12개 = 포트가 곧 도메인 · 응답지연 0.4초 · 48문서).

- **RED 기준선: 초당 1.95문서** (`concept.md:44` 기준 5.0). 판정 ①이 실패하고 ②·③은 통과 —
  계획서가 예상한 그대로다
- **예상 못 한 것: 변이를 하나도 안 넣은 원본 코드가 도메인 간격을 깨고 있다.**
  도메인 2개로 좁히면 **0.819초** 간격이 나온다(`MIN_GAP` 0.95). 12도메인 본 실행에서는
  간격이 5초씩 벌어져 숨는다 — 기존 e2e 가 못 본 이유다
- 뿌리는 `digest.md [4]` — **간격 시계가 발신이 아니라 팝 시각에서 시작한다.**
  `frontier.py:62` 가 팝 순간 `_last_fetch` 를 찍는데 그 뒤 `crawl.py:31` 의
  `robots.allowed()` 가 robots.txt 를 받느라 0.4초를 쓴다. 다음 번엔 캐시라 바로 나가므로
  실제 간격 = `interval - robots왕복`
- **동시화는 이걸 반드시 악화시킨다** — 간격을 1초까지 좁히는 것이 동시화의 목적이라
  모든 도메인의 첫 간격이 0.6초가 된다. `concept.md:25` 에서 이건 리뷰 RED다
- → **설계 계약 9 신설**(`Frontier.mark_sent(domain, at)`). 계획서 `## 하지 않을 것` 도
  같이 고쳤다. **스텝 2는 이걸 고치지 않으면 판정 ②를 통과할 수 없다**
- 변이 검사: ②는 `DOMAIN_INTERVAL=0` 으로, ③은 중복 방어 두 겹(`_seen`·`store.has`)을
  동시에 끄고 발화 확인. ①은 실행 자체가 발화

## 스텝 2를 시작하는 법 — 설계 계약 1~9 를 그대로 구현한다

`docs/design_crawl-throughput.md` 의 **## 계약** 절이 전부다. 요약:
`concurrent.futures.ThreadPoolExecutor` 로 **네트워크만** 동시화하고
`Store`·`Frontier` 는 계속 메인 스레드 전용(락·스레드별 커넥션 없음).
워커는 `robots.allowed()` → `robots.delay()` → **발신 시각 기록** → `fetch()`.
`--workers`(기본 8) · **도메인당 in-flight 1개**(`Frontier.next(exclude=)`) ·
`Frontier.mark_sent()` · 실패는 `Future` 가 잡아 status 0 취급.

**`rules/dev.md` 0절대로 실패하는 테스트를 먼저 쓴다.** 계획서 스텝 2에 목록이 있다
(동시성 배리어 · 도메인당 in-flight 1 · 간격 유지 · `max_pages` 상한 · 워커 1 = 오늘).

- 이미 한 것: 계획서·설계서·`e2e/perf_crawl.py`. **`src/` 는 아직 0줄 수정**

## 스텝 (3개)

| # | 무엇 | 의존 | 상태 |
|---|---|---|---|
| 1 | 처리량 e2e 하니스 `e2e/perf_crawl.py` | 없음 | **완료** — RED 1.95/s 확인 |
| **2 (다음)** | 크롤 루프 동시 fetch (계약 1~9) | 1 | |
| 3 | `store` 가 잠긴 DB 에 안 죽는다 | 없음 | |

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
- digest `[7]` `robots.allowed()` 비ASCII 예외 누수 — 이 계획 범위 밖
- robots.txt 요청 **자체**를 간격 시계에 싣는 것 — 계약 9는 페이지 간격만 고친다
