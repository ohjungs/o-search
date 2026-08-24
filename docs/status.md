---
signal: GREEN
mode: night
plan: noindex-respect
phase: 개발
step: 2/3
attempt: 0
iteration: 25
night_iterations: 4
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 25)
ctx: 71% / 200k
rules: null
---

# 현재 상태

**개발 2/3 완료 — 색인이 noindex 를 거르고 기색인 문서를 뺀다. 전체 84/84 통과.**
`src/websearch/indexer.py` 의 `index_pages()` 에 두 경로가 붙었다:
삽입 전 `extract.is_noindex(html)` 이면 건너뛰고(반환값에도 안 셈),
그 뒤 `docs ⋈ pages WHERE p.html LIKE '%robots%'` 후보 중 참인 url 을
`DELETE FROM docs`. `pages` 는 읽기만 한다 — 판정 규칙을 고쳤을 때 재판정할 근거다.
**개발 phase 는 여기서 끝난다.** 계획 스텝 3 은 e2e 다.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **테스트 phase (`rules/test.md` 3절 6카테고리 갭 탐색)**.
  개발 스텝 2개가 끝났으니 계획 스텝 3(e2e) 전에 테스트·리뷰 phase 를 거친다 —
  앞 두 계획(crawler-core, indexer)이 모두 이 순서로 돌았다
- 근거: 이번 변경의 갭 후보 — ① 제거 경로가 `html IS NULL` 행과 만날 때
  ② `docs` 에 있지만 `pages` 에서 사라진 url ③ 판정이 대용량 html 에서 느려지는지
  ④ CLI 출력이 "0 문서 색인" 과 "전부 거부됨" 을 구분해주는지
- 완료 기준: 8점 이상 갭은 테스트로 못박고, 미만은 `docs/digest.md` 로.
  전체 스위트 통과 유지
- 이미 한 것: 스텝 1·2 커밋 완료. 남은 코드 작업은 e2e 스크립트뿐

## 남은 스텝

- 계획 스텝 3/3 e2e `e2e/noindex_e2e.py` 신설 — 계획서 "e2e 시나리오" 5단계
  (리뷰 phase 통과 후)

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 테스트 phase 부터 이어진다.

## 정지 사유

(진행 중)
