---
signal: GREEN
phase: e2e
step: 1/1
attempt: 0
iteration: 313
updated: 2026-09-04
ctx: 52
night_iterations: 136
night_red: 2
night_retries: 0
plan: passage-db-state # 계획 53 — 리뷰 1/1 완료(반려 0) · 다음은 e2e
---

# 현재 상태

**계획 53 `passage-db-state` 리뷰 1/1 을 끝냈다. 반려 0 — 다음 phase 는 e2e 다.**
설계서는 `docs/design_passage-db-state.md`, 계획서는 `docs/plan_passage-db-state.md`,
브랜치는 `loop/passage-db-state` — 테스트 커밋 `9e57f23` 위에 리뷰 커밋을 얹었다.

## 보고 1건 — 자동 수정 1 · 승인 필요 0 · 제품 `src/` 0줄

**[R53-1] 세 질의가 갈리는지 재는 단언이 `subTest` 밖에 있었다.**
`TestPassagesWithoutPagesTable.test_every_query_shape_is_503` 이 세 질의를 `subTest` 로
돌면서 단언 셋은 `with` 블록 **밖**에 뒀다 — 첫 질의에서 멈추고 어느 질의가 갈렸는지도
안 남는다. 설계서 3절이 「세 질의가 `subTest` 셋이어야 *판정이 질의 내용에 안 달린다* 가
하나의 축으로 잡힌다」고 적은 그 축이 **실제로는 안 잡혀 있었다**. 단언 셋을 `with` 안으로
넣고 사유를 주석으로 남겼다(`tests/test_serve.py` 한 파일).

**실측이 갈랐다** — 판정을 `hits` 에 매다는 변이에서 고치기 전에는 라벨 없는 실패 **1건**,
고친 뒤에는 `(q='zzzznope')`·`(q='%01')` **2건**. 같은 계약을 단위에서 재는
`test_db_without_pages_raises_for_every_query_shape` 는 처음부터 둘을 냈다.

## 변이 넷을 다시 돌렸다 — 「검증됨」을 그대로 안 믿는다

스크래치패드 사본에서 돌렸다(`git checkout` **0회** · 저장소 무변).

| 변이 | 결과 |
|---|---|
| ① 503 튜플에서 `NoCrawlDataError` 제거 | `failures=2` |
| ② `passages()` 가드 삭제 | `failures=3, errors=1` |
| ③ 가드를 `hits` 에 매단다(`if hits and not …`) | `failures=3` → 수정 후 **4** |
| ④ **화면 사다리를 `NoCrawlDataError` 로 넓힌다** | **`599 OK` · 죽는 것 0** |

④ 가 값이다 — 설계 갈림길 3 과 `serve.py` 주석이 근거로 삼은 「대칭으로 넓히면 어떤
테스트로도 RED 를 못 만드는 줄이 생긴다」를 **리뷰가 처음 직접 쟀다**.

## 버린 후보 5건 · 전수로 본 것

80점 미만 5건(두 벌 문자열 헬퍼 · 화면 테스트 중복 · docstring 예외 미기재 ·
`TestPassagesWithoutHtmlColumn` 의 오늘 값 고정 · `digest.md` 207줄).
**열거형 완전성은 diff 밖 전수로 봤다** — `passages()` 의 비테스트 호출자는 `serve`
한 곳뿐이라 새 예외가 CLI 트레이스백으로 새는 경로 **0**, 가드의 `raise` 는
`finally: db.close()` 안이라 연결도 안 샌다. `digest` 로 넘긴 6점 둘의 점수도 맞다.

## 전수

**단위 599 OK**(13.607초 · 맨몸·단독). `data/crawl.db` sha256 `85c967…5bda18` 무변 ·
`docs/specs/` 무변 · `src/`·`e2e/`·`README.md` **0줄** · 새 파일 0 · **PR #7 무접촉**.

## 행동

다음은 **e2e** phase 다. 완료 기준 8(21종 전수)은 테스트 phase 가 이미 rc 0 으로 닫았으니
e2e 의 몫은 **계약 표면을 실서버로 다시 재는 것**이다 — `pages` 를 치운 DB 에서
`/passages` **503**·`/search` **200**·화면 **200**, 그리고 본문이 DB 경로를 안 흘리는지.
집안일 하나: `docs/digest.md` 가 **207줄**로 상한 200 을 넘었다(기점에서 이미 205).
회전할 때 오래된 완료 항목부터 지운다 — 아카이브 명부 줄은 남긴다.

## 설계

**끝났다.** `docs/design_passage-db-state.md` — 리뷰는 3절 계약을 안 건드렸다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` 가 그 뒤에 쌓여 있다.
   병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
