---
signal: GREEN
mode: night
plan: non-ascii-url
phase: 리뷰
step: 4/4
attempt: 0
iteration: 61
night_iterations: 30
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 61)
ctx: 76% / 200k
rules: rules/review.md
---

# 현재 상태

**`non-ascii-url` 테스트 phase 완료. 다음은 리뷰 phase.**
브랜치 `loop/non-ascii-url`. **196/196**(`expected failures=1`). e2e·성능 7개 전부 종료 0 —
`quality_eval` ko 85%·en 90%(기준선 동일), `perf_search` p95 **6.80ms**(기준선 7.06ms).

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

## 리뷰가 처리할 것 — 테스트 phase 가 넘긴 것

1. **[9] `fetch` 가 `http.client.InvalidURL` 을 흘린다 → 크롤 루프가 죽는다.**
   `HTTPException` 이라 `OSError` 그물에도 `UnicodeError` 에도 안 걸린다.
   도달 경로 3개가 전부 **평범한 HTML 에서 `links.extract` 가 만들어낸다**:
   `href="/a b"`(공백) · 제어문자 · `href="http://h:port/x"`(숫자 아닌 포트).
   **이 계획이 닫은 버그와 정확히 같은 부류다.** 고침은 한 줄이고 테스트 phase 가
   실제로 적용해 196/196 을 확인한 뒤 되돌렸다. `tests/test_fetcher.py` 에
   `@unittest.expectedFailure` 로 재현이 남아 있다
2. **[6] `to_ascii` 가 비ASCII URL 의 끝 `?`·`#` 를 삼킨다.** `http://h/가?` →
   `.../%EA%B0%80` 인데 `http://h/%EA%B0%80?` 는 그대로 → 계획 목표("두 표기가 1행")가
   이 조합에서만 샌다
3. **[7] `robots.allowed()` 도 비ASCII 호스트에서 예외를 흘린다** — `crawl` 경로에서는
   도달 불가(URL 이 태어나는 자리에서 이미 ASCII). 설계가 `robots.py` 를 범위 밖에 뒀고,
   순서가 밀리면 되살아나는 것은 새 계약 테스트가 막는다. **보류 후보**
4. [5] 호스트 대소문자 미정규화 · [4] 비ASCII userinfo 무테스트 — 계획 `## 안 할 것` 범위
5. 개발 중 나온 것: **정규화 못 하는 시드를 조용히 버린다**(`crawl.py:33` 에 stderr 선례 있음)

**뿌리가 하나다**: `fetcher`·`robots` 둘 다 "`OSError` 계열만 잡는다".

## 보류 (계획 밖 — 손대지 않는다)

- `recrawl` 정책 (`concept.md:31`) — 기존 `pages` 행 소급 정규화가 여기 걸린다
- `robots.py:_fetch_robots` 의 `resp.read()` 무제한 (`digest.md`)
- `search-ui` — 경량·디자인 축 측정 명령이 아직 `없음`
