---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 312
updated: 2026-09-04
ctx: 44
night_iterations: 135
night_red: 2
night_retries: 0
plan: passage-db-state # 계획 53 — 테스트 1/1 완료 · 다음은 리뷰
---

# 현재 상태

**계획 53 `passage-db-state` 테스트 1/1 을 끝냈다.** 다음 phase 는 **리뷰**다.
설계서는 `docs/design_passage-db-state.md`, 계획서는 `docs/plan_passage-db-state.md`,
브랜치는 `loop/passage-db-state` — 개발 커밋 `a4efdd9` 위에 테스트 커밋을 얹었다.

## 심은 것 — 테스트 **+3** · 제품 `src/` **0줄**

전부 `tests/test_serve.py` 한 파일이다.

| 새 단언 | 붙드는 것 |
|---|---|
| `TestPassagesWithoutHtmlColumn.test_matching_query_is_500` | 설계서 4절이 「500 이 맞는 이름」으로 적어 둔 천장 |
| 같은 클래스 `…_is_200_the_split_that_is_left` | **그 천장이 500 하나가 아니라 500/200 갈림**이라는 오늘의 답 |
| `TestPassagesWithoutPagesTable.test_html_screen_still_answers_200` | 화면 사다리를 **안 넓힌 것**(설계 갈림길 3) |

## 후보 ①이 후보가 적은 것보다 나빴다

`pages` 는 있는데 `html` 열이 없는 DB 는 **질의 내용으로 답이 갈린다** —
`q=김치찌개` 는 `no such column: html` 로 **500**, `q=zzzznope`·`q=%01` 은 루프에
못 닿아 **200 `[]`**. 계획 53 이 테이블 째로 없는 DB 에서 닫은 그 고장이 **열 하나
아래에 그대로** 있다. 설계서의 「500 이 맞는 이름」은 **답의 절반에만 참**이었다.
고치는 것은 제품 변경이라 범위 밖이다 — **오늘의 답을 못박고** `digest` 로 넘겼다(6점).

후보 ②(가드가 `search()` 뒤라는 순서)는 **안 열었다** — `pages` 없음 + 옛 색인은
`StaleIndexError` 가 이기는데 **셋 다 503 이라 HTTP 표면에서 구분이 없다**(6점 · `digest`).

## 변이 둘이 다 죽었다

스크래치패드 사본에서 돌렸다(`git checkout` **0회**).

- **① 가드가 열까지 본다**(`sql LIKE '%html%'` = 천장을 옮긴다) → `failures=3` —
  **새 테스트 둘만** 죽고 나머지 596 은 초록. 「천장을 옮기면 빨개진다」가 실물로 확인됐다.
- **② 가드를 `passages()` 에서 빼 `search()` 로 옮긴다**(설계가 버린 「대칭」안) →
  `failures=2` — 새 화면 테스트와 기존 `test_search_still_answers_200` 이 **함께** 죽었다.

**화면 테스트는 고유한 킬러 변이가 없다.** 변이 ②에서 기존 단언과 같이 죽고, 설계가
예고한 「화면 사다리를 대칭으로 넓히는」 변이는 어느 쪽도 못 죽인다. 남긴 이유는 **두
번째 표면**이라는 것 하나 — 화면이 근거 문단을 그리게 되는 날 그 줄만 빨개진다.

## 전수

**단위 599 OK**(13.342초 · 맨몸·단독) · **e2e 21종 전수 rc 0**(하나씩 눈으로 봤다) ·
`passage_eval` 정확도 **100.0%** · `quality_eval` 통과 · `hidden_passage_e2e` 0/5 무변.
계획서 8절의 최대 위험(「임시 DB 를 `pages` 없이 만드는 e2e 가 있으면 전수 RED」)은
**0건**으로 닫혔다. `README.md` 는 `단위 596 → 599건` 한 줄뿐이고 건수 단언과 같은 커밋이다.

## 행동

다음은 **리뷰** phase 다. 볼 자리: 새 세 단언이 계약을 **낮추지 않았는지**(특히
`…_is_200_the_split_that_is_left` 가 결함을 「바라는 답」으로 굳히는 것으로 읽히지 않는지) ·
`digest` 로 넘긴 6점 둘의 점수가 맞는지.

## 설계

**끝났다.** `docs/design_passage-db-state.md` — 테스트 phase 는 3절 계약을 안 건드렸다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` 가 그 뒤에 쌓여 있다.
   병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
