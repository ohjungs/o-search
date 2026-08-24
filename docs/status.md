---
signal: GREEN
mode: night
plan: crawl-delay
phase: 개발
step: 3/4
attempt: 0
iteration: 41
night_iterations: 10
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 41)
ctx: 82% / 200k
rules: null
---

# 현재 상태

**`crawl-delay` 개발 2/4 완료.** 135/135 통과. 다음은 **개발 3/4 — 크롤 루프 배선**
(`docs/plan_crawl-delay.md` 스텝 3, 계약은 `docs/design_crawl-delay.md`).

## 다음 스텝이 할 일

`src/websearch/crawl.py` 의 `crawl()` 루프에서 `robots.allowed(url)` 이 참인 **직후**:

```python
frontier.set_delay(urllib.parse.urlsplit(url).netloc, robots.delay(url))
```

- `robots.delay()` 는 `allowed()` 가 이미 받아둔 캐시를 쓴다 — robots.txt 를 두 번 받지 않는다
- 테스트는 `tests/test_crawl.py` 에. 가짜 robots 를 주입하고 `now=` 로 시계를 밀어
  **`Crawl-delay: 5` 면 5초 전에는 두 번째 요청이 안 나간다**를 단언한다(실제로 자지 않는다)
- 30초 초과 도메인이 통째로 빠지는 것도 크롤 루프 수준에서 한 번 확인한다

## 스텝 1·2 가 남긴 것 (이미 참인 것)

- `RobotsCache.delay(url) -> float | None` — 소수는 `robots.py:_DELAY_LINE` 폴백으로 긁는다
- `Frontier.set_delay(domain, seconds|None)` — 하한 `DOMAIN_INTERVAL`,
  `MAX_DELAY = 30.0` 초과면 큐를 비우고 `add()` 도 거부. `next()`·`seconds_until_ready()`
  둘 다 `_interval(domain)` 을 본다
- 변이 검사 4건(하한 제거·폐기 대신 깎기·대기시간·재유입) 전부 잡힌다

## 함정 두 개 (이번 세션에서 실제로 밟았다)

1. **`git checkout <파일>` 로 변이를 되돌리지 마라** — 커밋 전이면 구현이 통째로 날아간다.
   사본을 떠 두고 `cp` 로 되돌린다 (반복 41 에서 스텝 2 구현을 한 번 잃었다)
2. 같은 길이 변이(`max`↔`min`)는 `__pycache__` 가 옛 .pyc 를 재사용한다 →
   `PYTHONDONTWRITEBYTECODE=1` (`docs/project.md` 명령 절)

## 정지 조건

이번 세션 반복 10건(32~41) 전부 GREEN. RED 0 · 재시도 0 · 보류 0 · 패치 0.
브랜치 `loop/crawl-delay`. **5개 계획 브랜치 전부 머지 안 됐다.**
