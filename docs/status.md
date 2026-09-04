---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 318
updated: 2026-09-04
ctx: 45
night_iterations: 140
night_red: 2
night_retries: 0
plan: passage-html-column # 계획 54 — 테스트 1/1 완료 · 다음은 리뷰
---

# 현재 상태

**계획 54 `passage-html-column` 테스트 phase 를 끝냈다.** 다음 phase 는 **리뷰**다.
설계서는 `docs/design_passage-html-column.md`, 계획서는 `docs/plan_passage-html-column.md`,
브랜치는 `loop/passage-html-column`.

## 갭을 하나 찾아 닫았다 — 「판정 넷의 우선순위」 (8점)

문서가 적어 둔 후보를 그대로 안 믿고 **직접 다시 쟀다.** 임시 DB 여덟 상태 × 세 질의를
`indexer.passages()` 에 직접 먹여 우선순위를 확인했다(저장소 `data/crawl.db` 는 안 읽었다):

| DB 상태 | 세 질의 전부 |
|---|---|
| 없는 DB | `FileNotFoundError`(503) |
| 옛 색인 · 옛 색인 + `html` 열 없음 · 옛 색인 + `pages` 없음 | **`StaleIndexError`**(503) |
| `pages` 없음 | `NoCrawlDataError`(503) |
| `html` 열 없음 · `html` 열 없음 + 색인 전 | `OperationalError`(500) |

설계서 3절의 표가 오늘도 참이다. **그런데 그 순서를 붙드는 단언이 0개였다.**
순서를 정하는 것은 `hits = search(...)` 가 두 가드보다 **앞줄**이라는 사실 하나인데,
그 한 줄을 가드 **뒤**로 내리는 변이를 스크래치패드 **전체 사본**에 심어 보니
**602건이 전부 초록**이었다. 그 변이는 「옛 색인 + `html` 열 없음」을 503 → **500**,
「옛 색인 + `pages` 없음」을 503 → 503(`NoCrawlDataError`)으로 바꾼다 —
**색인만 다시 돌리면 낫는 DB 를 «우리가 터졌다» 로 부르게 된다.**

단언 하나를 세웠다: `test_indexer.TestPassages.test_stale_index_wins_over_a_broken_pages_warehouse`
(`subTest` 둘 — 열 축·테이블 축). 같은 변이를 다시 심으니 **`errors=2`** 로 죽고,
어느 창고에서 갈렸는지가 실패 라벨에 적힌다(`warehouse='html 열 없음'`·`'창고 없음'`).
HTTP 표면은 안 더했다 — `StaleIndexError` → 503 은 `test_serve` 의 예외 표가 이미 붙들고
있어 그쪽에 줄을 더하면 룰 5절(이미 덮인 것)에 걸린다.

## 전수 — 맨몸·단독

- 단위 **602 → 603 OK**(13.439초). `README.md` 의 `단위 603건` 은 같은 커밋이다.
- `passage_eval` 정확도 **100.0%**(398/398) · 채택률 **99.5%** · p95 **1.51ms**(예산의 0.3%)
  — 손댄 경로를 직접 재는 도구라 다시 돌렸고 셋 다 무변이다.
- e2e 21종 전수는 **안 돌렸다**(e2e phase 의 몫이다). 제품 코드는 이번 스텝에서 **0줄**이다.
- `data/crawl.db` sha256 `85c96744…5bda18` **전후 대조 무변** · `docs/specs/` 무변 ·
  `e2e/` 0줄 · 새 파일 0 · 새 의존성 0 · stdlib 만 · **PR #7 무접촉** ·
  띄운 서버 0개(`pgrep -f websearch.serve` 0건) · **러너 규율 위반 0회**(전부 맨몸).

## 안 연 갭 (`digest` 에 남겼다)

- **[5] 「`html` 열 없음」 상태의 화면(HTML) 사다리를 붙드는 단언이 없다.** 형제 클래스
  `TestPassagesWithoutPagesTable` 에는 있고 이쪽에는 없다. 오늘 실측 **200 · 결과 보임**.
  화면은 `_page_hits` → `search()` 만 타 현실적인 변이가 안 서서 8점이 아니다.

## 행동

다음은 **리뷰** phase 다. 백지로 볼 자리: 새 제품 한 줄(`SELECT html FROM pages LIMIT 0`)의
**비용 축**(`LIMIT 0` 대 `LIMIT 1` 을 붙드는 단언은 여전히 0개다 — 값이 0.01ms 라 안 열었다)과,
설계·개발·테스트가 세 번 인용한 「602/603 전체 통과가 오탐 0 을 붙든다」가 정말 그런지.

## 설계

**끝났다.** `docs/design_passage-html-column.md` — 테스트 phase 는 4절 계약을 안 건드렸다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` · `loop/passage-html-column` 이
   그 뒤에 쌓여 있다. 병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
