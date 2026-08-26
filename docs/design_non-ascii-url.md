# 설계: 비ASCII URL

- **계획**: `docs/plan_non-ascii-url.md` · **슬러그** `non-ascii-url` · 2026-08-26
- **트리거**: 새 모듈(`urls.py`) · 대안이 2개 이상 갈림(정규화 경계) · 3개 파일

## 결정 한 줄

**URL 이 태어나는 경계에서 ASCII 로 바꾼다** — `links.extract` 와 시드.
`fetcher.fetch` 는 정규화하지 않고 **최후 방어선**으로 예외만 잡는다.

## 대안

출발점 셋에서 하나씩 냈다 (`design.md` 3-1절).

| | ① 최소 — `fetch` 안에서 정규화 | ② 정공법 — 태어나는 경계 | ③ 되돌리기 우선 — `Frontier.add` 한 곳 |
|---|---|---|---|
| 크롤이 사나 | 산다 | 산다 | 산다 |
| `pages` 저장 키 | **원본 그대로** — `/가.html` 과 `/%EA%B0%80.html` 이 **2행** | 정규형 1행 | 리다이렉트 최종 URL 이 안 지나감 → 2행 가능 |
| `links.extract` 계약 | 비ASCII 그대로 나감 | **ASCII 보장** | 비ASCII 그대로 나감 |
| 잊을 위험 | 없음(단일 관문) | 호출처 3곳 | 없음(단일 관문) |
| 줄 수 | 가장 적음 | +파일 1 +3줄 | +파일 1 +1줄 |

**②를 고른다.** ①은 계획의 목표("같은 페이지가 두 행이 되지 않는다")를 못 채운다 —
`fetch` 는 저장 키를 정하지 않기 때문이다. ③은 한 줄로 끝나 매력적이지만
`crawl.py:36` 의 `page_url = result.url or url`(리다이렉트 최종 URL)이 프런티어를
거치지 않고 바로 `store.upsert` 로 가서, 정규화 안 된 키가 DB 에 남는 구멍이 그대로다.
②는 그 자리도 함께 덮는다.

`Frontier` 는 큐로 남긴다 — URL 표기 규칙을 아는 것은 큐의 일이 아니다.

## 계약

```python
# src/websearch/urls.py
def to_ascii(url: str) -> str | None
```

1. **ASCII 만 든 URL 은 한 글자도 바꾸지 않고 그대로 돌려준다.** 회귀 위험이 전부 여기 있다.
   덕분에 **멱등**이다 — `to_ascii(to_ascii(u)) == to_ascii(u)`.
   이미 퍼센트 인코딩된 URL 을 다시 인코딩하는 사고(`%` → `%25`)도 이 규칙 하나로 막힌다.
2. **호스트는 IDNA**(`encode("idna")`), **경로·질의·프래그먼트는 비ASCII 문자만 퍼센트 인코딩**.
   ASCII 구분자(`?` `&` `=` `/` `#` `%`)는 손대지 않는다 — 계획이 걱정한 `safe=` 목록 문제가
   "비ASCII 문자 하나씩만 `quote` 한다"로 사라진다.
3. **못 바꾸면 `None`.** 서로게이트가 든 URL, IDNA 가 거부하는 호스트(빈 라벨·63자 초과).
   예외를 밖으로 내보내지 않는다 — 크롤 루프를 죽인 원인이 그것이다.

**호출처 3곳** (전부 "URL 이 태어나는 자리"):

| 자리 | 하는 일 |
|---|---|
| `links.extract` (`links.py:26` 스킴 검사 뒤, 중복 제거 **앞**) | `None` 이면 링크 아님으로 버린다. 뒤의 `seen` 이 두 표기를 1건으로 합친다 |
| `crawl.crawl` 시드 (`crawl.py:17`) | CLI 는 신뢰 경계. `None` 인 시드는 버리고 나머지는 크롤한다 |
| `crawl.crawl` 리다이렉트 최종 URL (`crawl.py:36`) | `store` 키를 정규형으로 |

**`fetcher.fetch`**: `UnicodeError` 를 잡아 `FetchResult(0, None, None)`.
재시도하지 않는다(같은 URL 은 몇 번 해도 같다). `HTTPError` 뒤, `URLError` 앞에 둔다.
→ `fetch` 를 직접 부르는 쪽에는 **비ASCII URL 이 조용한 실패(status 0)** 로 보인다.
정규화를 `fetch` 안에 넣지 않는 이유는 위 표 ① 와 같다.

## 건드리지 않는 것

- **`robots.py`** — `allowed()`/`delay()` 는 프런티어를 통과한 ASCII URL 만 받는다.
  `_base()` 가 뽑는 `scheme://netloc` 도 따라서 ASCII 다. 계획의 위험 1 은 닫혔다.
- **`store.py` · 스키마 · 기존 행** — 소급 정규화 없음(계획 `## 안 할 것`).
- **일반 URL 정규화** — 끝 슬래시·기본 포트·질의 순서·**퍼센트 표기 대소문자**(`%ea` vs `%EA`).
  비ASCII 하나만 다룬다.

## 되돌리기

새 파일 1 + 한 줄짜리 편집 3 = **커밋 하나로 revert**. 플래그 불필요.

## 스텝 (계획의 4스텝 그대로, 경계만 확정)

1. `urls.to_ascii` + `tests/test_urls.py`
2. 호출처 3곳 연결 (`links.py` · `crawl.py`) + 기존 테스트
3. `fetcher` 최후 방어선 + `tests/test_fetcher.py`
4. `e2e/non_ascii_e2e.py` — 로컬 서버, 시나리오 3개
