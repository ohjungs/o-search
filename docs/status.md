---
signal: DONE
mode: night
plan: non-ascii-url
phase: e2e
step: 4/4
attempt: 0
iteration: 63
night_iterations: 32
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-26 (반복 63)
ctx: 76% / 200k
rules: rules/e2e.md
---

# 현재 상태

**`non-ascii-url`(007) DONE.** 브랜치 `loop/non-ascii-url`.
**199/199** · e2e 8개 + 성능 전부 종료 0 · 재시도 0 · RED 0.

지시받은 계획이 끝났다 (`/loop-harness night <할 일>` → **준 것만 하고 정지**).
새 계획을 탐색하지 않았다. 다음 세션은 `/loop-harness` 로 탐색부터 시작한다.

## 이 계획이 닫은 것

`https://ko.wikipedia.org/wiki/대한민국` 을 크롤하면 `UnicodeEncodeError` 가
`fetch()` 밖으로 새 나가 **크롤 루프가 통째로 죽던 것**. 시드도 링크도 이제 산다.

- `src/websearch/urls.py` 신규 — `to_ascii(url) -> str | None`.
  **ASCII URL 은 한 글자도 안 바꾼다**(멱등) · 호스트 IDNA · 비ASCII 문자만 퍼센트 인코딩 ·
  못 바꾸면 `None`. `urlsplit`/`urlunsplit` 재조립 없이 **원본 문자열 위에서 갈아끼운다**
- 정규화 경계 = **URL 이 태어나는 자리** 3곳: `links.extract`(중복 제거 앞) · 시드 · 리다이렉트 최종 URL
- `fetcher.fetch` 는 정규화하지 않는다 — **URL 오류는 즉시 status 0(재시도 없음),
  연결·응답 오류는 재시도**

## 덤으로 닫은 것 — 계획 이전부터 있던 크래시

`http.client.InvalidURL` 이 `OSError` 그물을 빠져나가 **크롤 루프를 죽이고 있었다.**
도달 경로 3개가 전부 평범한 HTML 이다: `href="/a b"`(공백) · 제어문자 ·
`href="http://h:port/x"`(숫자 아닌 포트). **뿌리는 `fetch` 가 `OSError` 계열만
잡는다는 것**이었고, `UnicodeError` 는 그 뿌리의 증상 하나였다.

## 다음 계획 후보 (이 계획이 남긴 것 — `digest.md`)

- **[7] `robots.allowed()`·`delay()` 도 같은 뿌리의 구멍** — 비ASCII 호스트에서 예외를 흘린다.
  지금은 도달 불가(URL 이 태어나는 자리에서 이미 ASCII)고
  `test_robots_and_store_never_see_non_ascii_url` 이 그 순서를 지킨다.
  같은 파일의 `resp.read()` 무상한 건과 **함께 열면 싸다**
- [5] 호스트 대소문자 미정규화 (`한국.COM` → `xn--3e0b707e.COM`) — 계획 `## 안 할 것` 범위였다
- e2e 가 **닿지 않는 경로 2개**: 비ASCII `Location:` 리다이렉트(302 를 서버에 추가해야 잰다) ·
  `fetch` 의 `InvalidURL`(앞에서 다 ASCII 가 돼 e2e 로는 도달 불가 — 단위 테스트가 담당)

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
