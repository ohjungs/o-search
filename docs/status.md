---
signal: GREEN
mode: night
plan: crawl-delay
phase: 테스트
step: 4/4 (개발 끝)
attempt: 0
iteration: 43
night_iterations: 12
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 43)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 개발 4/4 완료 — 스텝 4개 전부 끝.** 138/138, e2e 5개 통과.
다음은 **테스트 phase** — 새로 쓰는 곳이 아니라 **빠뜨린 것을 찾고 전체를 돌리는** 곳이다
(`~/.claude/skills/loop-harness/rules/test.md`). 그다음 리뷰, 그다음 e2e 결과 기록.

## 완성된 동작

- robots 가 `Crawl-delay: N` 을 선언하면 그 도메인 요청 간격이 N 초가 된다 (실측 e2e)
- 1초 하한은 사이트가 풀 수 없다 (`Crawl-delay: 0` → 1초)
- 30초 초과 요청은 지킬 수 없다고 보고 **첫 접촉 뒤 그 도메인을 더 안 간다**
- stdlib 이 버리는 소수 값(`3.5`)도 지킨다 — `robots.py:_DELAY_LINE` 폴백

## 테스트 phase 가 볼 만한 곳 (미리 눈에 띈 것)

- `crawl.crawl()` 이 `robots.delay()` 를 **매 URL 팝마다** 부른다 — 캐시라 싸지만
  같은 값을 반복 대입한다. 계약이 아니라 낭비다
- `set_delay` 는 도메인 폐기를 되돌리는 경로가 없다(의도). 테스트로 못 박을지 판단
- `e2e/crawl_delay_e2e.py` 는 `127.0.0.1`/`localhost` 를 두 도메인으로 쓴다 —
  Host 헤더로 robots 를 가른다. 이 트릭이 깨지면 두 시나리오가 한 도메인이 된다

## 정지 조건

이번 세션 반복 12건(32~43) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
브랜치 `loop/crawl-delay`. **5개 계획 브랜치 전부 머지 안 됐다.**
