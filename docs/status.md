---
signal: GREEN
mode: night
plan: crawl-delay
phase: e2e
step: 4/4 (개발 끝)
attempt: 0
iteration: 45
night_iterations: 14
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 45)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 리뷰 phase 통과.** 백지 패스 지적 중 8점 이상 2건 + 값싼 것 4건을 고쳤다.
146/146, `e2e/crawl_delay_e2e.py` 통과. 다음은 **e2e phase** —
`docs/e2e/crawl-delay/result.md` 에 결과를 남기고 계획을 DONE 으로 닫는다.

## 리뷰가 잡은 것 (전부 실재. 확인하고 고쳤다)

1. **[7] 같은 netloc 의 http/https 가 서로의 간격을 덮어썼다** — robots 캐시는
   `scheme://netloc` 인데 프런티어 키는 `netloc` 이다. 20초를 요구한 사이트에
   지시 없는 https 링크 하나가 오면 1초로 떨어졌다. → `set_delay` 를 **늘어나는
   방향으로만** 움직이게 고쳤다(docstring 이 원래 그렇게 약속하고 있었다)
2. **[6] 폴백이 남의 UA 그룹 값을 집었다** — 다른 봇에게 건 `Crawl-delay: 86400` 을
   우리 값으로 읽으면 1.5초면 지킬 수 있는 사이트가 상한 초과로 통째로 버려진다.
   → `robots._applicable_delay()` 가 **우리 이름을 지목한 그룹 → 없으면 `*`** 만 본다
3. [5] 도메인 폐기가 조용했다 → `crawl()` 이 stderr 로 사유를 찍는다
4. [4] `Crawl-delay: 1e3` 을 1초로 읽었다 → `float()` 먼저 시도해 1000초로 읽는다
5. [3] docstring 이 코드와 달랐다 / [2] 폐기 도메인에 안 쓸 `_delays` 가 남았다 / [1] e2e 잡티

## 리뷰 지적 중 안 고친 것 (digest 에 있다)

- [5] `robots._fetch_robots` 에 응답 크기 상한 없음 — **무인 모드가 보안·자원은 안 만진다**
- [4] `MAX_DELAY` 는 요청당 대기만 막는다(총 크롤 시간 예산은 별도)
- [4] 간격 시계가 pop 시각 기준 — 프런티어 계약 변경이라 별도 판단

## 정지 조건

이번 세션 반복 14건(32~45) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
