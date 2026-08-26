---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 개발
step: 1/3
attempt: 0
iteration: 65
night_iterations: 2
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-27 (반복 65)
ctx: 82% / 200k
rules: rules/dev.md
---

# 현재 상태

**`crawl-throughput`(008) 설계 완료.** 브랜치 `loop/crawl-throughput`.
계획서 `docs/plan_crawl-throughput.md` · 설계 `docs/design_crawl-throughput.md`.
**다음은 개발 스텝 1/3 — `e2e/perf_crawl.py`(처리량 측정 수단).**

## 문제 (사용자 실측)

크롤 처리량 **초당 0.5문서**. `concept.md:44` 기준은 **초당 5문서** — 10배 차이.
원인은 `src/websearch/crawl.py:26-51` 이 한 번에 한 페이지씩 순차로 받아
**네트워크 대기가 곧 총 소요시간**이라는 것. 같은 실측에서 1,700문서쯤
`store.upsert` 가 `sqlite3.OperationalError: database is locked` 로 크롤을 죽였다.

## 설계가 정한 것 (`docs/design_crawl-throughput.md`)

**A안 — 메인 스레드가 상태를 독점하고 네트워크만 스레드풀에 던진다.**
`Store`·`Frontier` 는 계속 한 스레드 전용이라 **락도 스레드별 커넥션도 없다.**
워커는 `robots.allowed()` → `robots.delay()` → `fetch()` 만 하고 튜플을 돌려준다.
`--workers`(기본 8) · **도메인당 in-flight 1개** · `--workers 1` 이 되돌리기 수단.

**깨본 가정은 참이었다** — `frontier.py:53-54` 의 자격 조건이 **팝 이후 경과 시간뿐**이라,
응답이 간격보다 길면 같은 도메인이 in-flight 인 채 다시 팝된다.
순차 루프에선 불가능했던 구멍을 동시화가 처음 연다 → 계약 3(도메인당 1개)이 이걸 막는다.
그래서 `Frontier.next(exclude=())` 가 필요하다.

## 스텝 (3개)

| # | 무엇 | 의존 | 건드릴 파일 |
|---|---|---|---|
| **1 (다음)** | 처리량 e2e 하니스 `e2e/perf_crawl.py` — 지금 코드로 **RED** 를 본다 | 없음 | e2e 신규 1 |
| 2 | 크롤 루프 동시 fetch (설계 계약 1~8) | 1 | crawl·frontier + 테스트 2 |
| 3 | `store` 가 잠긴 DB 에 안 죽는다 | 없음 | store + 테스트 1 |

임계경로 1 → 2. 스텝 3은 독립.

## 스텝 1을 시작하는 법

`e2e/perf_search.py` 가 검색 p95 에 하는 일을 크롤 처리량에 한다.
**포트가 곧 netloc** 이라(`frontier.py:44`) `127.0.0.1:PORT` 12개면 도메인 12개다.
`ThreadingHTTPServer` 12개 · 핸들러가 응답 전 `time.sleep(0.4)`(인위 지연이 핵심 —
없으면 순차와 동시가 같은 숫자를 낸다) · 도메인당 12페이지.
판정 3개: ① 초당 5문서 이상 ② 도메인별 요청 간격 전부 0.95초 이상 ③ 같은 URL 중복 요청 0.
**지금 코드로 돌리면 ①만 실패해야 한다**(순차 → 초당 2.5문서 근처).
자세한 것은 계획서 "스텝 1" 절.

- 이미 한 것: 계획서 + 설계서. **소스 0줄** — 코드는 아직 아무것도 안 건드렸다

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
- digest `[7]` `robots.allowed()` 비ASCII 예외 누수 — 이 계획 범위 밖
