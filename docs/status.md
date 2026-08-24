---
signal: GREEN
mode: night
plan: noindex-respect
phase: 개발
step: 1/3
attempt: 0
iteration: 24
night_iterations: 3
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 24)
ctx: 71% / 200k
rules: null
---

# 현재 상태

**개발 1/3 완료 — `extract.is_noindex()` 구현. 전체 81/81 통과.**
`docs/design_noindex-respect.md` 계약대로 `src/websearch/extract.py` 에
`_MetaRobotsParser` + `is_noindex(html_text)` 를 넣었다. 사전 필터
(`"robots" not in html_text.lower()`) 덕에 대부분의 문서는 파싱조차 하지 않는다.
새 의존성 0. 색인 경로는 아직 이 함수를 부르지 않는다 — 스텝 2 가 붙인다.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **개발 스텝 2/3 — `src/websearch/indexer.py` 의 `index_pages()` 가
  noindex 를 거르고 이미 색인된 noindex 문서를 지운다**. TDD 로 간다:
  `tests/test_indexer.py` 에 케이스 3개를 먼저 쓰고 실패를 확인한 뒤 구현
- 근거: `docs/design_noindex-respect.md` "계약" 절이 질의 두 개를 확정했다 —
  삽입 경로는 기존 증분 select 결과에 `if extract.is_noindex(html): continue`,
  제거 경로는 `SELECT d.url, p.html FROM docs d JOIN pages p ON p.url = d.url
  WHERE p.html LIKE '%robots%'` 로 후보를 좁힌 뒤 참인 url 만
  `DELETE FROM docs WHERE url=?`. 반환값은 **실제로 넣은 수**(건너뛴 것은 안 셈)
- 완료 기준: `PYTHONPATH=src python3 -m unittest discover tests` 전체 통과.
  케이스는 `docs/plan_noindex-respect.md` 스텝 2 의 ①②③
- 이미 한 것: 스텝 1 커밋 완료(`extract.py`, `tests/test_extract.py`).
  `indexer.py` 는 아직 안 건드렸다

## 남은 스텝

- 3/3 e2e `e2e/noindex_e2e.py` 신설 — 계획서 "e2e 시나리오" 5단계

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 개발 스텝 2 부터 이어진다.

## 정지 사유

(진행 중)
