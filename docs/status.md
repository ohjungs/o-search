---
signal: GREEN
phase: 개발
step: 1/1
attempt: 0
iteration: 311
updated: 2026-09-04
ctx: 46
night_iterations: 134
night_red: 2
night_retries: 0
plan: passage-db-state # 계획 53 — 개발 1/1 완료 · 다음은 테스트
---

# 현재 상태

**계획 53 `passage-db-state` 개발 1/1 을 끝냈다.** 다음 phase 는 **테스트**다.
설계서는 `docs/design_passage-db-state.md`, 계획서는 `docs/plan_passage-db-state.md`,
브랜치는 `loop/passage-db-state`.

## 심은 것 — 설계서 3절 계약 그대로

① `indexer.passages()` 의 `_connect()` 직후 · `hits` 루프 **앞**에 `index_pages()` 와
같은 `sqlite_master` 가드. ② `serve.do_GET` JSON 사다리의 503 튜플에
`indexer.NoCrawlDataError`. ③ 화면 사다리는 **안 넓혔고** `# JSON 과 같은 값` 주석을
「왜 더 좁은가」로 다시 썼다. 헬퍼는 안 뽑았고 천장은 `ponytail:` 주석으로 코드에 있다.

제품 diff 는 `src/websearch/indexer.py` **+10** · `src/websearch/serve.py` **+8/-2**
두 파일뿐. 스키마·재색인·마이그레이션 **0** · 시그니처 무변.

## RED 를 눈으로 봤다

구현 전 `FAILED (failures=5, errors=1)` — 계획서 완료 기준 1·2·3 이 정확히 그 자리다.

| 관측 | RED 에서 본 값 | GREEN |
|---|---|---|
| `pages` 없는 DB · `q=김치찌개` | `OperationalError: no such table: pages` → HTTP **500** | **503** |
| 같은 DB · `q=zzzznope` | `NoCrawlDataError not raised` → **200 `[]`** | **503** |
| 같은 DB · `q=%01`(무토큰) | `NoCrawlDataError not raised` → **200 `[]`** | **503** |
| 같은 DB · `/search?q=김치찌개` | **200**(RED 때부터 초록 — 대조군) | **200 무변** |
| `README.md` 건수 단언 | `(593, 21) != (596, 21)` | 596 으로 맞춤 |

단위 **593 → 596 OK**(13.596초 · 맨몸·단독). 새 테스트 셋:
`test_indexer.TestPassages.test_db_without_pages_raises_for_every_query_shape`(`subTest` 3) ·
`test_serve.TestPassagesWithoutPagesTable`(503 3종 · `/search` 200) ·
`TestPassagesSchemaVersion` 표에 `NoCrawlDataError → 503` 행.

## 변이 둘이 다 죽었다 (완료 기준 10)

스크래치패드 사본에서 돌렸다(`.mutation-lock` 불필요 · `git checkout` **0회**).

- **① `passages()` 가드 삭제** → `failures=3, errors=1`(indexer 세 질의 + serve 503 3종).
- **② 503 튜플에서 `NoCrawlDataError` 제거** → `failures=2`
  (`TestPassagesWithoutPagesTable` · `TestPassagesSchemaVersion`).

**첫 판이 틀린 자리를 지웠다** — `t.index("if not db.execute(")` 가 `index_pages()` 의
같은 가드를 먼저 잡아 엉뚱한 변이가 됐다. 같은 문자열이 두 곳이라는 설계서의 천장이
변이 도구에서 먼저 나타난 것이다. `def passages` 뒤부터 찾도록 고쳐 다시 쟀다.

## 행동

다음은 **테스트** phase 다. 갭 탐색의 자리 후보:
`pages` 는 있는데 `html` 열이 없는 DB(설계서 4절이 「500 이 맞는 이름」으로 적어 둔
천장 — 그것을 붙드는 단언이 0개다) · 가드가 `search()` 뒤라는 **순서**를 붙드는 단언
(옛 색인 우선순위가 오늘 그대로인지) · 화면 사다리를 **안 넓힌 것**을 붙드는 단언.

## 설계

**끝났다.** `docs/design_passage-db-state.md` — 개발은 3절 계약을 한 글자도 안 벗어났다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` 가 그 뒤에 쌓여 있다.
   병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
