---
signal: GREEN
mode: night
plan: non-ascii-url
phase: 개발
step: 2/4
attempt: 0
iteration: 58
night_iterations: 27
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 58)
ctx: 72% / 200k
rules: rules/dev.md
---

# 현재 상태

**`non-ascii-url` 개발 step 1/4 완료. 다음은 step 2/4(호출처 연결).**
브랜치 `loop/non-ascii-url`. **185/185 통과**(기존 170 + `test_urls.py` 15).
`src/websearch/urls.py` 있음 — 다른 파일은 아직 안 건드렸다.

## 설계가 정한 것 — `docs/design_non-ascii-url.md`

**URL 이 태어나는 경계에서 ASCII 로 바꾼다.** 대안 셋 중 ②(정공법).

- 새 모듈 `src/websearch/urls.py` 의 `to_ascii(url) -> str | None`
  - **ASCII 만 든 URL 은 한 글자도 안 바꾼다** → 멱등, `%` 이중 인코딩 사고가 원천 차단
  - 호스트 IDNA · 그 외는 **비ASCII 문자 하나씩만** `quote` (구분자 `? & = / #` 무손상)
  - 못 바꾸면 `None` (서로게이트·IDNA 거부 호스트). 예외를 밖으로 흘리지 않는다
- 호출처 3곳: `links.extract`(중복 제거 앞) · `crawl` 시드 · `crawl` 리다이렉트 최종 URL
- `fetcher.fetch` 는 **정규화하지 않는다** — `UnicodeError` 를 잡아 `FetchResult(0, None, None)`
- `robots.py`·`store.py`·스키마는 건드리지 않는다

③(`Frontier.add` 한 곳)을 버린 이유가 이 설계의 핵심이다 — `crawl.py:36`
`page_url = result.url or url` 이 프런티어를 안 거치고 `store.upsert` 로 직행한다.

## 남은 스텝

1. ~~`urls.to_ascii` + `tests/test_urls.py`~~ **완료** (62cec7b, 변이 4종 확인)
2. **(다음)** 호출처 3곳 연결 (`links.py`·`crawl.py`)
3. `fetcher` 최후 방어선 + `tests/test_fetcher.py`
4. `e2e/non_ascii_e2e.py` — 로컬 서버, 시나리오 3개 (계획 `## e2e 시나리오`)

## 보류 (계획 밖 — 손대지 않는다)

- `recrawl` 정책 (`concept.md:31`) — 기존 `pages` 행 소급 정규화가 여기 걸린다
- `robots.py:_fetch_robots` 의 `resp.read()` 무제한 (`digest.md`)
- `search-ui` — 경량·디자인 축 측정 명령이 아직 `없음`
