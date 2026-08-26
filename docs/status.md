---
signal: GREEN
mode: night
plan: non-ascii-url
phase: e2e
step: 4/4
attempt: 0
iteration: 62
night_iterations: 31
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 62)
ctx: 74% / 200k
rules: rules/e2e.md
---

# 현재 상태

**`non-ascii-url` 리뷰 phase 완료. 다음은 e2e phase — 마지막 스텝.**
브랜치 `loop/non-ascii-url`. **199/199**(`expectedFailure` 0). e2e·성능 7개 전부 종료 0 —
`quality_eval` ko 85%·en 90%, `perf_search` p95 **6.79ms**. 소스 누적 21줄 + 새 모듈.

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
3. ~~`fetcher` 최후 방어선~~ **완료** (359c5f4, 소스 2줄 · 테스트 2건)
4. `e2e/non_ascii_e2e.py` (e2e phase) — 로컬 서버, 시나리오 3개 (계획 `## e2e 시나리오`)

## 리뷰가 한 것 (0bdc98c) — 후보 7건 중 3건 적용

1. **[100] `fetch` 의 그물을 뿌리에 맞춰 다시 그었다.** `http.client` 예외는 전부
   `HTTPException` 이라 `OSError` 그물에 안 걸린다 — `UnicodeError` 는 그 뿌리의 증상
   하나였다. **URL 이 틀린 것**(`UnicodeError`·`InvalidURL`)은 즉시 0·재시도 없음,
   **연결·응답이 틀린 것**(`HTTPException` 포함)은 재시도로 나눴다
2. **[90] `to_ascii` 에서 `urlsplit`/`urlunsplit` 재조립을 버렸다** — 원본 문자열 위에서
   호스트와 비ASCII 문자만 갈아끼운다. 빈 `?`·`#` 를 삼키던 것이 사라지고 **코드가 줄었다**
3. **[85] 못 바꾸는 시드를 stderr 로 알린다** (`crawl.py:33` 간격 경고와 같은 형식).
   링크에서 나온 것은 조용히 버리는 그대로

**설계 문서를 먼저 고치고 코드를 밀었다**(`rules/design.md` 6절) —
`design_non-ascii-url.md` 에 `## 설계를 고친 곳 (리뷰 phase)` 절이 있다.

## 남은 것 — e2e phase

`e2e/non_ascii_e2e.py` 신규. 계획 `## e2e 시나리오` 3개:
① 한글 경로 링크를 따라가는 크롤이 **중단되지 않고** 저장된다
② 한글 표기와 퍼센트 표기 두 링크 → `pages` **1행**
③ 정규화 불가 URL 을 시드에 섞으면 그것만 건너뛰고 나머지는 전부 수집

## 보류 (계획 밖 — 손대지 않는다)

- `recrawl` 정책 (`concept.md:31`) — 기존 `pages` 행 소급 정규화가 여기 걸린다
- `robots.py:_fetch_robots` 의 `resp.read()` 무제한 (`digest.md`)
- `search-ui` — 경량·디자인 축 측정 명령이 아직 `없음`
