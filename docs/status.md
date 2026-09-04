---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 317
updated: 2026-09-04
ctx: 55
night_iterations: 139
night_red: 2
night_retries: 0
plan: passage-html-column # 계획 54 — 개발 1/1 완료 · 다음은 테스트
---

# 현재 상태

**계획 54 `passage-html-column` 개발 1/1 을 끝냈다.** 다음 phase 는 **테스트**다.
설계서는 `docs/design_passage-html-column.md`, 계획서는 `docs/plan_passage-html-column.md`,
브랜치는 `loop/passage-html-column`.

## 심은 것 — 설계서 4절 계약 그대로 한 줄

`indexer.passages()` 안, 계획 53 이 심은 `sqlite_master` 가드 **직후** · `hits` 루프 **앞**:

```python
db.execute("SELECT html FROM pages LIMIT 0")
```

열이 없으면 sqlite 가 준비 단계에서 `OperationalError` 를 **질의와 무관하게** 내고,
`serve.do_GET` 의 `except Exception` 이 이미 그것을 500 으로 옮긴다. **`serve.py` 0줄 ·
새 예외 0개 · 스키마·마이그레이션·재색인 0 · 시그니처 무변.** 제품 diff 는
`src/websearch/indexer.py` **한 파일**이고, 그중 코드는 한 줄이다.

주석 두 자리를 고쳤다 — 계획서가 «오늘 살아 있는 손실은 거짓 주석» 이라 적은 자리다.
위 가드의 «`html` 열이 없거나 … 500 이 맞는 이름» 은 새 줄이 갈라내는 것으로 다시 썼고,
새 줄에는 `LIMIT 0` 을 고른 실측(0.0128 대 0.0016 ms)과 **루프 앞인 이유**를 적었다.
천장은 `ponytail:` 로 코드에 남겼다 — **`html` 열 하나만 본다**(다른 열·권한은 여전히
루프 안 500 이고 답이 같아 갈림이 없다. 셋째 열이 근거 경로에 생기면 `PRAGMA table_info`).

## RED 를 눈으로 봤다

구현 전 `FAILED (failures=6)` — 계획서 완료 기준 1·2·7 이 정확히 그 자리다.

| 관측 | RED 에서 본 값 | GREEN |
|---|---|---|
| `html` 열 없는 DB · `q=김치` | 500(오늘도 500 — 안 갈린 쪽) | **500 무변** |
| 같은 DB · `q=zzzznope` | `200 != 500` · `{"passages": []}` | **500** |
| 같은 DB · `q=%01`(무토큰) | `200 != 500` · `{"passages": []}` | **500** |
| 같은 DB **+ 색인 전** · `q=김치` | `200 != 500` | **500**(알고 바꾼 값) |
| `indexer.passages()` 세 질의(HTTP 밖) | `OperationalError not raised` × 2 | **셋 다 `OperationalError`** |
| 같은 DB · `/search?q=김치` | **200**(RED 때부터 초록 — 대조군) | **200 무변** |
| `README.md` 건수 단언 | `(599, 21) != (602, 21)` | 602 로 맞춤 |

단위 **599 → 602 OK**(13.441초 · 맨몸·단독). 새 단언 셋:
`test_serve.TestPassagesWithoutHtmlColumn.test_every_query_shape_is_500`(`subTest` 3 —
뒤집힌 것) · `test_search_still_answers_200`(대조군) ·
`TestPassagesWithoutHtmlColumnBeforeIndexing`(색인 전 500) ·
`test_indexer.TestPassages.test_db_without_html_column_raises_for_every_query_shape`.
클래스 docstring 의 «천장은 500 하나가 아니라 500/200 갈림이다» 는 이제 거짓이라 고쳤다.

## 변이 둘이 다 죽었다 — 붙들린 것은 「루프 앞」이다

스크래치패드 **전체 사본**에서 돌렸다(`git checkout` **0회** · 저장소 무접촉).

- **① 새 줄 삭제** → `failures=5`.
- **② 같은 줄을 `hits` 루프 **안으로** 이동** → `failures=5` — **①과 글자 그대로 같은 다섯**.

**②가 이 스텝의 진짜 변이다.** 줄이 있어도 자리가 틀리면 `hits` 가 빈 질의는 판정에 못
닿아 갈림이 그대로 돌아온다. 삭제 변이만 돌렸으면 「줄이 있다」만 재고 「앞에 있다」는
못 쟀다. 첫 판에서 `src`·`tests` 만 복사했더니 `e2e/`·`docs/` 가 없어 무관한 실패 24건이
섞였다 — 사본은 **저장소 전체**여야 판정 줄이 읽힌다.

## 재지 않은 것 · 그대로인 것

`passage_eval` 정확도 **100.0%**(398/398) · 채택률 **99.5%** · p95 **1.51ms**(예산의 0.3%)
— 손댄 경로를 직접 재는 도구라 이번에 돌렸고 셋 다 무변이다. **e2e 21종 전수는 안 돌렸다**
(e2e phase 의 몫이다). `data/crawl.db` sha256 `85c96744…5bda18` **무변**(전후 대조) ·
`docs/specs/` 무변 · `e2e/` 0줄 · 새 파일 0 · 새 의존성 0 · stdlib 만 · **PR #7 무접촉** ·
띄운 서버 0개(`pgrep -f websearch.serve` 0건 확인) · **러너 규율 위반 0회**(전부 맨몸).

## 행동

다음은 **테스트** phase 다. 갭 탐색의 자리 후보:
**판정 넷의 우선순위**(없는 DB → 옛 색인 → 창고 없음 → **열 없음 500**)를 붙드는 단언이
아직 0개다 — 설계서 3절이 표로만 쟀고 「`html` 열 없음 + 옛 색인 → `StaleIndexError`」가
코드에 못박혀 있지 않다. 그 밖에 `LIMIT 0` 이 **정상 DB 에서 오탐 0** 이라는 축(오늘은
602건 전체 통과가 대신 붙들고 있다)과, 화면(HTML) 사다리를 **안 넓힌 것**을 붙드는 단언.

## 설계

**끝났다.** `docs/design_passage-html-column.md` — 개발은 4절 계약을 한 글자도 안 벗어났다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` · `loop/passage-html-column` 이
   그 뒤에 쌓여 있다. 병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
