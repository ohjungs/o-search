---
signal: GREEN
mode: night
plan: noindex-respect
phase: 개발
step: 0/3
attempt: 0
iteration: 23
night_iterations: 2
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 23)
ctx: 71% / 200k
rules: null
---

# 현재 상태

**설계 완료 — `docs/design_noindex-respect.md`. 개발 스텝 1 착수 가능.**
대안 A(색인 시점 판정) 채택. B(수집 시점 차단)는 스키마 변경이라 야간 금지 + 판정 시점이
굳어 재판정이 불가능해져서, C(검색 시점 필터)는 색인 자체가 남아 윤리 축을 못 채워서 버렸다.
위험 가정 4건은 탐침으로 전부 참 확인(커밋 안 함): html.parser 가 깨진 HTML·대문자·
따옴표 없는 속성에서도 meta 를 잡는다 / `'robots'` 사전 필터가 안전하다 /
FTS5 의 UNINDEXED url 로 DELETE 가 된다 / SQLite LIKE 는 대소문자 무시·NULL 미포함.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **개발 스텝 1/3 — `src/websearch/extract.py` 에 `is_noindex(html_text)` 추가**.
  TDD 다 (`rules/dev.md` 0절): `tests/test_extract.py` 에 케이스를 먼저 쓰고
  실패를 눈으로 확인한 뒤 구현한다. 케이스 7개는 `docs/plan_noindex-respect.md` 스텝 1 에 있다
- 근거: `docs/design_noindex-respect.md` 의 "계약" 절이 시그니처와 판정 규칙을 확정했다 —
  `name` 소문자화 후 `"robots"` 인 meta 만, `content` 를 쉼표로 쪼개 `noindex`/`none` 토큰,
  사전 필터 `"robots" not in html_text.lower()`, `_TextParser` 에 얹지 말고 새 서브클래스
- 완료 기준: `PYTHONPATH=src python3 -m unittest discover tests` 전체 통과
  (현재 기준선 71건 + 새 케이스). 새 의존성 0
- 이미 한 것: 계획서·설계서 작성과 탐침까지. **코드는 한 줄도 안 건드렸다**

## 남은 스텝

- 2/3 `indexer.index_pages` 가 noindex 를 거르고 기색인 문서를 지운다 (설계 "계약" 절의 질의 두 개)
- 3/3 e2e `e2e/noindex_e2e.py` 신설 — 계획서 "e2e 시나리오" 5단계

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 개발 스텝 1 부터 이어진다.

## 정지 사유

(진행 중)
