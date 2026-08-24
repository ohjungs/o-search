---
signal: GREEN
mode: night
plan: indexer
phase: 개발
step: 3/4
attempt: 0
iteration: 17
night_iterations: 15
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 17)
ctx: 68% / 200k
rules: null
---

# 현재 상태

indexer 개발 1/4(본문 추출)·2/4(FTS5 증분 색인) 완료. 스위트 전체 초록 48/48.
crawler-core DONE(아카이브 001). 다음은 개발 3/4 — 질의 함수 + CLI.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: indexer 개발 3/4 — `src/websearch/indexer.py` 에
  `search(db_path, query, limit=10) -> [(url, title, snippet)]` (bm25 순) 추가하고
  CLI `python3 -m websearch.indexer <db> [--query Q]` (질의 없으면 색인 실행)
- 근거: `docs/plan_indexer.md` 스텝 3, 계약은 `docs/design_indexer.md` 계약 절.
  **질의 재작성이 핵심** — 어절마다 `"어절"*` 로 접두 매치(unicode61 채택 이유),
  FTS5 특수문자는 큰따옴표로 감싸 무력화한다(주입 방지)
- 완료 기준: `PYTHONPATH=src python3 -m unittest discover tests` 전체 통과.
  `tests/test_indexer.py` 확장 — 한국어 2글자 질의 매치 / 영어 대소문자 /
  무결과 빈 리스트 / limit 준수 / FTS5 특수문자 질의가 예외를 안 냄
- 이미 한 것: 없음 (착수 전). TDD 1단계인 실패하는 테스트부터 쓴다

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 이어진다.
개발 3/4 질의+CLI → 테스트 → 리뷰 → e2e(스텝 4).

## 정지 사유

없음 (진행 중).
