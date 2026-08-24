---
signal: GREEN
mode: night
plan: search-api
phase: 개발
step: 2/5
attempt: 0
iteration: 32
night_iterations: 1
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 32)
ctx: 75% / 200k
rules: null
---

# 현재 상태

**스텝 2 완료 — `GET /search?page=N` 이 10건 단위로 나뉜다.** 105/105 통과.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **개발 스텝 3 — 신뢰 경계와 오류 경로** (`rules/dev.md`, TDD)
- 근거: `docs/plan_search-api.md` 스텝 3 + `docs/design_search-api.md` "진입점 방어를
  한 자리에 모은다". HTTP 핸들러가 CLI 두 개에 이은 **세 번째 진입점**이다
  (`docs/digest.md` 반복 실패 항목)
- 완료 기준: `_parse()` 한 곳에서 ① `page` 가 정수가 아니거나 1 미만 → 400
  ② `page` > 100 → 400 (성능이 아니라 자원 고갈 방어 — OFFSET 이 선형으로 자란다)
  ③ `q` 길이 200자 초과 → 400 ④ 없는 경로 404 ⑤ `POST /search` 501 (스텁 없이 stdlib)
  ⑥ FTS5 문법 문자·NUL·제어문자 질의가 500 이 아니라 200 — `indexer._fts_query()` 가
  이미 막는 것을 HTTP 로 **도달 가능해졌으니 다시 고정**. 어느 것도 트레이스백을 싣지 않는다
- 이미 한 것: 스텝 2 커밋 `872e911` 까지. `_parse()` 는 지금 `q` 빈값만 막고
  **`page` 는 `int()` 로 바로 변환한다** — 잘못된 값이면 `ValueError` 가 do_GET 의
  기존 400 경로를 타지만 본문 사유가 파이썬 영문 메시지다. 스텝 3 이 여기를 사람이 읽는
  한 줄로 바꾸고 범위 검사를 같은 함수에 넣는다
- 건드릴 파일: `src/websearch/serve.py`, `tests/test_serve.py`

## 남은 스텝

3 신뢰 경계 → 4 p95 측정 스크립트와 `project.md` 기준선 → 5 e2e

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 개발 스텝 3 부터 이어진다.
계획이 DONE 되면 다음은 **`crawl-delay` 존중**(`docs/digest.md` 크롤 윤리) — 사용자가
이미 정한 순서다.

## 정지 조건

이번 반복 시점 ctx 71% · 5h 66% · 7d 40% — 걸린 것 없음. 계속 진행 중.
