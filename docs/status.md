---
signal: GREEN
phase: 설계
step: 0/1
attempt: 0
iteration: 310
updated: 2026-09-04
ctx: 46
night_iterations: 133
night_red: 2
night_retries: 0
plan: passage-db-state # 계획 53 — 설계 1/1 완료 · 다음은 개발
---

# 현재 상태

**계획 53 `passage-db-state` 설계 1/1 을 끝냈다.** 다음 phase 는 **개발**이다.
설계서는 `docs/design_passage-db-state.md`, 계획서는 `docs/plan_passage-db-state.md`,
브랜치는 `loop/passage-db-state`.

## 결정 — 편집 둘 + 주석 하나

① `indexer.passages()` 의 `_connect()` 직후·`hits` 루프 **앞**에 `index_pages()` 와
같은 `sqlite_master` 가드 네 줄을 인라인으로 둔다. ② `serve.do_GET` JSON 사다리의
503 튜플에 `indexer.NoCrawlDataError` 를 더한다. ③ 화면 사다리는 **안 넓히고**
`# JSON 과 같은 값` 주석을 비대칭 사유로 고친다. 헬퍼는 안 뽑는다(천장은 주석으로).

## 갈림길 셋을 무엇으로 갈랐나

1. **503 이냐 200 `[]` 이냐 → 503.** 같은 고장난 DB 의 `/search` 가 **200 · 결과 1건**
   이라, 200 `[]` 는 「제목만 매치된 문서」가 내는 **오늘의 정상 응답과 글자 그대로 같다**
   (`e2e/hidden_passage_e2e.py` 가 0/5 로 재는 값). 소비자가 두 상태를 못 가른다.
2. **가드 자리 → `passages()` 안(`search()` 뒤·루프 앞).** `_connect()` 에 두면
   `search()` 까지 걸려 `pages` 없는 DB 의 `/search` 가 200 → 503 으로 죽는다.
   헬퍼(C안)는 관측이 같은데 `index_pages()` 를 건드리는 직교 편집이라 버렸다.
3. **화면 사다리 → 안 넓힌다.** `pages` 없는 DB 의 `/?q=김치찌개` 는 **200 · 결과 1건**
   으로 실측됐다 — `search()` 는 `NoCrawlDataError` 를 못 낸다. 넣으면 **변이로 죽지
   않는 줄**(완료 기준 10 이 못 덮는 코드)이 생긴다. 대신 주석 한 줄을 고친다.

## 가정을 깼다 — 참이었다 (반복 310 실측)

「정상 경로에 `pages` 없는 DB 로 `passages()` 를 부르는 곳이 없다」를 **실제로 두 편집을
넣고 전수를 돌린 뒤 되돌렸다**(커밋 없음).

| 질의 | 오늘 | 가드만 | **가드+튜플** | 정상 DB 대조군 |
|---|---|---|---|---|
| `/passages?q=김치찌개` | 500 | 500 | **503** | 200 · 문단 1건 (무변) |
| `/passages?q=zzzznope` | 200 `[]` | 500 | **503** | 200 `[]` (무변) |
| `/passages?q=%01` | 200 `[]` | 500 | **503** | 200 `[]` (무변) |
| `/search?q=김치찌개` | 200 | 200 | **200** | 200 (무변) |
| `/?q=김치찌개`(화면) | 200 | 200 | **200** | 200 (무변) |

- 단위 **593 OK**(가드만·둘 다 — 두 번 다) · e2e **21종 전수 rc 0** ·
  `passage_eval` 정확도 **100.0%** · 채택률 **99.5%** · p95 **1.52ms** 세 숫자 무변.
- 덤 둘: **가드만으로는 여전히 500**(계획서의 «처방은 두 곳» 확인 — 완료 기준 10 변이 ②의
  기대값이다) · **«판정이 질의 내용에 안 달린다» 를 내는 것은 가드 하나**(가드만 넣어도
  세 질의가 500 하나로 모인다). 겹쳐 있던 두 고장을 서로 다른 편집이 고친다.

## 행동

다음은 **개발**이다(스텝 1/1). TDD 로 2절 표의 세 질의를 먼저 RED 로 세운다 —
`tests/test_indexer.py` 의 `test_missing_db_raises` 옆에 `subTest` 셋,
`tests/test_serve.py` 의 `test_every_passages_response_carries_version` 표에
`NoCrawlDataError → 503` 행과 실제 DB HTTP 503 하나(같은 DB 의 `/search` 200 을 옆에).
`README.md` 의 상태 코드 계약 줄과 `단위 593건` · `tests/test_readme.py` 건수 단언은
**같은 커밋**에서 움직인다.

## 설계

**끝났다.** `docs/design_passage-db-state.md` — 갈림길 셋의 표, 깬 가정, 계약, 천장,
역할 검토, 되돌리기까지. 개발이 새로 고를 것은 없다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` 가 그 뒤에 쌓여 있다.
   병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
