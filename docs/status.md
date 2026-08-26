---
signal: GREEN
mode: night
plan: non-ascii-url
phase: 설계
step: 0/4
attempt: 0
iteration: 56
night_iterations: 25
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 56)
ctx: 62% / 200k
rules: rules/design.md
---

# 현재 상태

**`quality-eval`(006) DONE. 새 계획 `non-ascii-url` 착수 — 다음은 설계 phase.**
브랜치 `loop/non-ascii-url` (`loop/quality-eval` 37fa3aa 에서 분기). 170/170 통과.

## 새 계획의 근거 — 재현했다

한글이 든 URL 을 크롤하면 **크롤 루프가 통째로 죽는다.** `fetcher.fetch()` 가
`FetchResult(0, ...)` 를 주는 게 아니라 `UnicodeEncodeError` 가 함수 밖으로 샌다
(`fetcher.py:20-23` 의 `try` 는 `Request` **생성만** 감싸고, `:40` 의
`except (URLError, OSError)` 는 `ValueError` 계열을 안 잡는다).
한국어가 1급인 저장소에서 한국어 위키백과 URL 이 대부분 비ASCII 다.

실측 표는 `docs/plan_non-ascii-url.md` `## 실측` 에 있다. 핵심 위험 하나:
`links.extract` 가 한글 URL 을 **날것 그대로** 프런티어·`pages` 에 넣어서,
같은 페이지가 `/가.html` 과 `/%EA%B0%80.html` **두 행**이 될 수 있다.

## 다음 (설계 phase — `rules/design.md`)

`docs/design_non-ascii-url.md` 에 답할 것 셋:

1. **정규화 지점** — `fetcher.fetch` 안인가, `links.extract`/`Frontier.add` 경계인가.
   저장 키(`pages.url`)가 갈린다
2. **함수의 집** — 새 `src/websearch/urls.py` 인가 기존 모듈인가
3. **인코딩 규칙** — `quote(safe=...)` 의 `safe` 에 `%` 를 넣을지.
   넣으면 멱등해지지만 경로에 든 **진짜 `%` 문자**는 못 고친다

## 직전 계획(006)이 남긴 것 — 다음에 토크나이저를 건드릴 때 읽을 것

`e2e/quality_eval.py` 로 잰 **ko 85% · en 90%** 가 기준선이다. 단 **이 자는 랭킹을
못 잰다**(`recall@1` == `recall@10`, 근거 `docs/e2e/quality-eval/result.md`).

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

`recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다.
`robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
