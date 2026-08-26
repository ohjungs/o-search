---
signal: GREEN
mode: night
plan: tokenizer
phase: 리뷰
step: 3/3
attempt: 0
iteration: 79
night_iterations: 3
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-27 (반복 79)
ctx: 30% / 200k
rules: rules/review.md
---

# 현재 상태

**`tokenizer`(010) 개발 3/3 완료.** 브랜치 `loop/tokenizer` (기점 `f8d921b`).
계획 `docs/plan_tokenizer.md` · 설계 `docs/design_tokenizer.md`.

## 이미 한 것

| 커밋 | 무엇 |
|---|---|
| `5241f93` | 계획 — 탐침으로 `trigram` 을 먼저 버렸다(한국어 질의 20개 중 10개가 2자) |
| `e807e97` | 설계 — 한글 2-gram 을 제목·본문 열로 **나눠** 넣는다 |
| `e07f5f2` | 개발 1/3 — 색인 스키마 드리프트 감지 → `docs` 재구축 |
| `9b06a32` | 개발 2/3 — `porter unicode61` + `title_ng`·`body_ng` 열 |
| `ec028dc` | 개발 3/3 — 오탐 요약 줄 + 성능 기준선 갱신 |

**실측**
- 검색 품질 **한국어 20/20 (100%) · 영어 19/20 (95%)** (옛 기준선 17/20 · 18/20)
- 테스트 **255/255** · 변이 **14종 전부 잡힘**(스텝1 3종 · 스텝2 8종 · 스텝3 3종)
- e2e 5종(`indexer`·`noindex`·`non_ascii`·`design_check`·`search_api`) 전부 종료 0
- 오탐 평균 매치 13.8 → **14.0** (최소 11 · 최대 28, 변동 없음)
- `perf_search` p95 6.71 → **9.11ms** (예산 300ms 의 3.0%) · `perf_crawl` **10.25/s** 유지
- 색인 크기 3000문서에서 1.3 → **3.1MB** (2.4배) — 설계 `## 범위 밖` 에 천장으로 적었다

## 다음

1. **리뷰** — 백지 서브에이전트가 돌고 있다(diff + 소스만, `docs/` 는 안 준다)
2. **e2e** — `docs/plan_tokenizer.md` `## e2e 시나리오` 6개.
   화면(`serve.py`)까지 HTTP 로 넘어가는지 봐야 한다. 수단은 아직 **미정** — e2e phase 에서 만든다
3. 끝나면 아카이브(010) → `docs/index.md` · `docs/reports/night_2026-08-27.md` 세션 4

## 이번 밤 사고 하나 (기록)

반복 78 에서 기준선 대조를 하겠다고 `git checkout <옛커밋> -- src/websearch/indexer.py`
를 `git stash` 와 섞어 돌렸다가 **스텝 2 구현을 통째로 되돌렸다.** 전체 테스트가
18건 빨개져서 즉시 발견했고 `git checkout HEAD -- ` 로 복구했다. 커밋은 안 됐다.
→ 교훈: 기준선 비교는 **작업 트리를 건드리지 말고** `git show <커밋>:<경로>` 로 읽거나
scratchpad 에서 따로 돌린다. digest 후보.

## digest 후보 (이번 밤)

1. **매치를 넓히는 변경에는 오탐을 재는 줄을 같은 커밋에 넣는다.** 포함률은 정답이
   들어왔는지만 세고 함께 딸려 온 것은 못 센다 — 없으면 무엇을 잃었는지 모른 채 닫는다
2. **`CREATE ... IF NOT EXISTS` 는 정의 변경에 눈이 멀다.** 스키마 문자열을 바꿔도
   옛 DB 는 옛 정의로 조용히 남는다. 정의를 `sqlite_master.sql` 과 대조하는 경로가 없으면
   "코드는 새것, 색인은 옛것" 이 조용히 성립한다
3. **작업 트리를 건드리는 기준선 비교 금지** (위 사고)
