---
signal: DONE
phase: 계획
step: 1/1
attempt: 0
iteration: 486
updated: 2026-09-09
ctx: 42
night_iterations: 9
night_red: 0
night_retries: 0
plan: seed-tier1
---

## 다음 반복이 읽을 것 — 밤은 **탐색 막힘**으로 끝났다. 아침 할 일은 둘

1. **패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch`
   (382줄 · 구현 + 단위 + e2e · `git apply --check` 통과). 계획 83 의 산출물이고
   야간이 적용하지 않은 이유는 「보안 관련 — 줄 수 무관 항상 보류」다.
   적용하면 바뀌는 계약: `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을
   준다(018 의 「보존」을 뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.
2. **다음 계획을 사람이 하나 열어 주는 것** — 8순위 전수를 다시 돌았고 근거가 0 이다.
   막힌 자리는 아래에 이름으로 적어 뒀다.

- **작업 트리는 `main` 과 같다** — `src`·`tests`·`e2e`·`README.md` 무변경, 전수
  **709 OK**(반복 493 재실행 · rc=0). 브랜치에 남는 것은 문서와 패치뿐이다.
- **반복 493 탐색 결과(8순위 전수)**: ① 실패 테스트 0(709 OK) ② 린트·타입 도구 없음
  ③ 코드 `TODO` 0(유일한 히트는 `tests/test_indexer.py` 의 HTML fixture 문자열)
  ④ `docs/candidates.md` 없음 ⑤ 보류 절은 오늘 밤 자기 것(`plan_userinfo-leak`)뿐
  ⑥ 후보 절 5점 이상은 **전부 「여는 조건」 미충족이거나 사람이 정할 갈림길**
  (`[7]` OFFSET 페이지네이션은 공개 API `?page=N` 을 커서로 바꾸는 건이라 루프 몫이 아니다)
  ⑦ 반복 실패 — 하나는 **오늘 닫힌 것으로 확인해 취소선**(아래), 나머지는 훅·규율이
  이미 선 자리 ⑧ `gh issue list` 0건.
- **`digest.md ## 반복 실패` 「회전을 돌리면서 digest 압축 줄을 안 남긴다」에 취소선.**
  그 항목이 처방으로 적은 검사가 이미 들어가 있다 —
  `tests/test_docs.py ArchiveIndexTest`, 오늘 재니 아카이브 **77개 전수가 `## 완료`
  명부에 있고 구멍 0**(단독 `Ran 1 · OK`). 같은 밤 두 번째 「본문은 닫혔는데 머리가
  열려 있어 탐색이 먼저 읽은」 줄이다(`[9]` 가 첫째).
- 야간 보고서: `docs/reports/night_2026-09-09.md`.
