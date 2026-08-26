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
2. **호스트는 IDNA**(`encode("idna")`), **나머지는 비ASCII 문자만 퍼센트 인코딩**.
   ASCII 구분자(`?` `&` `=` `/` `#` `%`)는 손대지 않는다 — 계획이 걱정한 `safe=` 목록 문제가
   "비ASCII 문자 하나씩만 `quote` 한다"로 사라진다.
   **원본 문자열 위에서 갈아끼운다** — 분해 후 `urlunsplit` 재조립이 아니다. 재조립은
   빈 `?`·`#` 를 삼켜(`http://h/가?` → `.../%EA%B0%80`) 규칙 1 과 어긋난다.
   전제로 `urlsplit` 이 떼는 탭·개행을 먼저 뗀다 — 그래야 호스트가 원본의 부분문자열이다.
3. **못 바꾸면 `None`.** 서로게이트가 든 URL, IDNA 가 거부하는 호스트(빈 라벨·63자 초과).
   예외를 밖으로 내보내지 않는다 — 크롤 루프를 죽인 원인이 그것이다.

**호출처 3곳** (전부 "URL 이 태어나는 자리"):

| 자리 | 하는 일 |
|---|---|
| `links.extract` (`links.py:30` 스킴 검사 뒤, 중복 제거 **앞**) | `None` 이면 링크 아님으로 버린다. 뒤의 `seen` 이 두 표기를 1건으로 합친다 |
| `crawl.crawl` 시드 (`crawl.py:19`) | CLI 는 신뢰 경계. `None` 인 시드는 버리고 나머지는 크롤한다. **버릴 때 stderr 로 알린다** — 사용자가 직접 준 URL 이라 조용히 사라지면 안 된다 (`crawl.py:33` 간격 경고와 같은 선례) |
| `crawl.crawl` 리다이렉트 최종 URL (`crawl.py:44`) | `store` 키를 정규형으로 |

**`fetcher.fetch`** — 최후 방어선은 **URL 이 틀린 것**과 **연결·응답이 틀린 것**을 나눈다.
`HTTPError` 뒤에 둘을 순서대로 놓는다:

| 잡는 것 | 하는 일 | 왜 |
|---|---|---|
| `UnicodeError` · `http.client.InvalidURL` | `FetchResult(0, None, None)`, **재시도 없음** | URL 자체가 틀렸다(비ASCII·공백·제어문자·숫자 아닌 포트). 몇 번 보내도 같다 |
| `URLError` · `OSError` · `http.client.HTTPException` | 재시도 | 타임아웃·연결 실패·응답 파손. 다음 번엔 될 수 있다 |

`http.client` 예외는 `HTTPException` 이라 **`OSError` 그물에 걸리지 않는다** — 이것이
`UnicodeError` 를 흘리던 것과 같은 뿌리다. `InvalidURL` 로 가는 URL 은 셋 다
`links.extract` 가 평범한 HTML 에서 만들어낸다(`href="/a b"` · 제어문자 · `href="http://h:port/x"`).

→ `fetch` 를 직접 부르는 쪽에는 **틀린 URL 이 조용한 실패(status 0)** 로 보인다.
정규화를 `fetch` 안에 넣지 않는 이유는 위 표 ① 와 같다.

## 건드리지 않는 것

- **`robots.py`** — `allowed()`/`delay()` 는 프런티어를 통과한 ASCII URL 만 받는다.
  `_base()` 가 뽑는 `scheme://netloc` 도 따라서 ASCII 다. 계획의 위험 1 은 닫혔다.
- **`store.py` · 스키마 · 기존 행** — 소급 정규화 없음(계획 `## 안 할 것`).
- **일반 URL 정규화** — 끝 슬래시·기본 포트·질의 순서·**퍼센트 표기 대소문자**(`%ea` vs `%EA`).
  비ASCII 하나만 다룬다.

## 설계를 고친 곳 (리뷰 phase, 2026-08-26)

테스트 phase 가 계약의 구멍 둘을 찾아 넘겼다. 코드를 밀고 나가지 않고 계약을 고쳤다
(`rules/design.md` 6절).

1. **계약 2 — 재조립을 버렸다.** 원래 계약은 "호스트 IDNA + 나머지 퍼센트 인코딩"만
   말하고 *어떻게 다시 붙이는지*를 안 정했다. 구현이 고른 `urlunsplit` 은 빈 `?`·`#` 를
   삼켜 **계약 1(ASCII 는 안 바꾼다)과 비ASCII 쪽이 어긋났다** — `http://h/가?` 와
   `http://h/%EA%B0%80?` 가 다른 키가 돼 "두 표기가 1행" 목표가 이 조합에서만 샜다.
   원본 문자열 치환으로 바꾸니 재조립이 삼킬 것이 없어지고 함수도 한 줄 짧아졌다.
2. **`fetcher.fetch` — 잡는 그물이 좁았다.** 원래 계약은 `UnicodeError` 하나만 말했다.
   같은 자리에서 `http.client.InvalidURL` 이 그대로 새어 나가 크롤 루프를 죽인다.
   **뿌리는 "`OSError` 계열만 잡는다"** 였고 `UnicodeError` 는 그 뿌리의 증상 하나였다.
   그물을 뿌리에 맞춰 다시 그었다 — URL 이 틀린 것은 즉시 0, 연결·응답이 틀린 것은 재시도.

## 되돌리기

새 파일 1 + 짧은 편집 3 = **커밋 하나로 revert**. 플래그 불필요.

## 스텝 (계획의 4스텝 그대로, 경계만 확정)

1. `urls.to_ascii` + `tests/test_urls.py`
2. 호출처 3곳 연결 (`links.py` · `crawl.py`) + 기존 테스트
3. `fetcher` 최후 방어선 + `tests/test_fetcher.py`
4. `e2e/non_ascii_e2e.py` — 로컬 서버, 시나리오 3개
