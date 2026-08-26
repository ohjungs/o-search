---
signal: GREEN
mode: night
plan: non-ascii-url
phase: 개발
step: 3/4
attempt: 0
iteration: 59
night_iterations: 28
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 59)
ctx: 78% / 200k
rules: rules/dev.md
---

# 현재 상태

**`non-ascii-url` 개발 step 2/4 완료. 다음은 step 3/4(`fetcher` 최후 방어선).**
브랜치 `loop/non-ascii-url`. **192/192 통과**. `crawl_e2e.py` 회귀 없음(수집 15, 간격 1.004s).
`fetcher.py` 는 아직 안 건드렸다 — 비ASCII URL 을 직접 `fetch()` 하면 여전히 예외가 샌다.

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
2. ~~호출처 3곳 연결~~ **완료** (1f37fb2, 소스 4줄 · 테스트 7건)
3. **(다음)** `fetcher` 최후 방어선 + `tests/test_fetcher.py`
4. `e2e/non_ascii_e2e.py` — 로컬 서버, 시나리오 3개 (계획 `## e2e 시나리오`)

## 리뷰에서 볼 것 (개발 중 나온 것)

- **정규화 못 하는 시드를 조용히 버린다.** CLI 는 신뢰 경계고 `crawl.py:33` 에
  간격 초과 도메인을 stderr 로 알리는 선례가 있다. 계약 밖이라 step 2 에서 안 넣었다
- `crawl.py:36` 의 `or url` 폴백은 변이 검사를 **통과해버렸다**(테스트 0건) →
  step 2 에서 테스트를 하나 더 넣어 막았다. 같은 종류의 무검증 분기가 더 있는지 본다

## 보류 (계획 밖 — 손대지 않는다)

- `recrawl` 정책 (`concept.md:31`) — 기존 `pages` 행 소급 정규화가 여기 걸린다
- `robots.py:_fetch_robots` 의 `resp.read()` 무제한 (`digest.md`)
- `search-ui` — 경량·디자인 축 측정 명령이 아직 `없음`
