---
signal: GREEN
mode: night
plan: crawl-delay
phase: 설계
step: 0/4
attempt: 0
iteration: 38
night_iterations: 7
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 38)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 계획 수립 완료** → `docs/plan_crawl-delay.md` (스텝 4개).
다음 반복은 **설계 phase** 다 — 계획서 `## 설계` 절이 트리거 3개를 적어 두었고,
`docs/design_crawl-delay.md` 가 판정해야 할 갈림길이 계획서 안에 명시돼 있다.

## 설계가 정해야 할 것 (계획서에 실측과 함께 적혀 있다)

1. **stdlib 이 소수 Crawl-delay 를 버린다** — `Crawl-delay: 3.5` → `None`
   (`isdigit()` 검사, 3.9.6 실측). 그대로 두면 1초로 떨어져 **요청보다 3.5배 빠르게** 때린다
2. **간격 상한** — `Crawl-delay: 86400` 을 지킬 것인가, 그 도메인을 버릴 것인가
3. **배선 방향** — 크롤 루프가 `frontier.set_delay()` 로 밀어넣기 vs 프런티어가 콜백으로 당기기.
   robots.txt 는 그 도메인 첫 URL 을 **팝한 뒤에** 적재된다는 제약이 있다

## 진행 중인 스텝

없음 — 계획만 세웠다. 코드는 한 줄도 건드리지 않았다.
브랜치 `loop/crawl-delay` 를 `loop/search-api` 4f92e32 에서 땄다 (계획 브랜치는 직렬로 쌓인다).

## 직전 계획

`search-api` **DONE** (반복 32~37). 124/124, e2e 4개.
`GET /search?q=&page=` · 성능 기준선 p95 6.71ms(3000문서) · 아카이브 004.
**`loop/search-api` 는 머지 안 됐다** — 4개 계획 브랜치 전부 그 상태다.

## 정지 조건

이번 세션 반복 7건(32~38) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
