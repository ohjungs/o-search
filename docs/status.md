---
signal: GREEN
phase: 계획
step: 0/1
attempt: 0
iteration: 309
updated: 2026-09-04
ctx: 46
night_iterations: 133
night_red: 2
night_retries: 0
plan: passage-db-state # 계획 53 — 설계 필요
---

# 현재 상태

**계획 53 `passage-db-state` 착수 — 계획서를 썼다.** 다음 phase 는 **설계**다(트리거 셋).
계획서는 `docs/plan_passage-db-state.md`, 브랜치는 `loop/passage-db-state`(기점 `a4a4da1`).

## 무엇을 여는가

`/passages` 가 **DB 상태를 500 으로 내고, 그 판정이 질의 내용에 달려 있다.**
`pages` 테이블이 없는 DB(색인 `docs` 는 살아 있다)를 실서버로 띄워 오늘 직접 쟀다.

| 질의 | 정상 DB(대조군) | `pages` 없음 |
|---|---|---|
| `q=김치찌개`(매치 있음) | 200 · 문단 1건 | **500** `{"error":"검색 중 오류가 났다"}` |
| `q=zzzznope`(매치 없는 낱말) | 200 · `[]` | **200 · `[]`** |
| `q=%01`(무토큰) | 200 · `[]` | **200 · `[]`** |
| `GET /search?q=김치찌개` | 200 | **200**(색인은 멀쩡하다) |

`README.md:40` 이 «낫는 상태에는 503, 그 밖에는 500» 을 계약으로 적었는데 이 상태가
그 목록에 없고, 계획 47 `db-open-atomic` 이 `search()` **안**에서 닫은 «판정이 질의
내용에 달린다» 가 함수 하나 건너 `passages()` 에서 그대로 남아 있다.

## 계획 phase 가 한 것

- **탐색 1~5순위 0건 실측**: 단위 **593 OK**(맨몸·단독) · 타입/린트 설정 0개 ·
  코드의 `TODO`/`FIXME`/`HACK` 0건(유일한 1건은 `tests/test_indexer.py:758` 의 HTML
  fixture 문자열 안) · `docs/candidates.md` 없음 · `digest` 보류 절 0건. 6순위 `[5]` 채택.
- **중복 방지(discover 5절)**: `docs/index.md` 의 계획 표와 사양 분할 목록을 `digest` 후보와
  전수 대조 — 겹침 0 · 진행 중 계획 0 · `docs/patches/` 없음.
- **취소선 하나 그었다**: `digest` 후보 `[6] focus_rule 의 위치·극성` 은 네 갈래가
  계획 49 `focus-rule-scope`(`e2e/design_check.py` 조건 6·`INDIRECT_RE`/`FOCUS_RE`)로
  이미 닫혔는데 취소선만 없었다. 점수가 가장 높은 축이라 그대로 뒀으면 **완료된 것을
  다시 여는 반복**이 됐다.
- **후보의 처방을 다시 재서 절반인 것을 찾았다**: 후보는 «`passages()` 가
  `NoCrawlDataError` 를 쓰면 된다» 인데 `serve.py:281` 의 503 튜플이
  `(FileNotFoundError, StaleIndexError)` 뿐이라 **그것만으로는 여전히 500** 이다.
  `digest [7]`(기록된 답을 실행 전에 다시 재라)의 다섯 번째 적용(계획 41·44·51·52 에 이어).

## 행동

다음은 **설계**다. 갈림길 셋을 실측으로 가른다 —
① 503 이냐 200 `[]` 이냐(문서 단위 `continue` 규칙의 극한을 어디로 볼지),
② 가드를 `passages()` 안에 두나 `_connect()` 에 두나(후자면 `/search` 까지 죽는다),
③ 화면 사다리(`serve.py:323`)의 503 튜플도 넓히나(오늘은 닿을 수 없는 코드다).

## 설계

필요하다. 트리거 셋 — 공개 계약(`/passages` 상태 코드·`README.md:40`) 변경 ·
3개 이상 파일 · 갈림길 2개 이상.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` 가 그 뒤에 쌓여 있다.
   병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
