---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 403
updated: 2026-09-07
ctx: 52
night_iterations: 198
night_red: 2
night_retries: 4
plan: noindex-entity-prefilter 계획 69 (e2e 1/1 통과 · DONE)
---

## 현재 상태

**계획 69 `noindex-entity-prefilter` e2e 1/1 끝냈다 · DONE.**
브랜치 `loop/noindex-entity-prefilter` · 계획서는 `docs/plan_history_055.md` 로 아카이브 ·
결과 문서 `docs/e2e/noindex-entity-prefilter/result.md` ·
전수 **632건 `OK`** · e2e 3종 rc 0 · 이번 phase 의 `src/` 변경 **0줄**.

## 이번 phase 산 것

**아홉 계획 만에 `src/` 를 고친 계획이라, 문서 검사가 아니라 일꾼 파이프라인을 물었다.**

`crawl` → `indexer` → `serve` 를 **임시 DB 하나로 관통**시켰다. 로컬 `http.server` 에
여섯 페이지를 띄우고(엔티티 인코딩 거부 · 평범한 거부 둘 · 명시 허용 · 오탐 대조군 ·
목차) 색인한 뒤, `python3 -m websearch.serve <db> --port 0` 을 진짜 서브프로세스로
띄워 `GET /?q=pyeongsan` 을 실제로 때렸다.

| 축 | 물은 것 | 실측 |
|---|---|---|
| 진입 | 엔티티 인코딩 `name` 이 색인에 안 들어가는가 | `3 문서 색인` (계획 전이면 4) |
| 화면 | 사용자가 보는 HTML 에 안 나오는가 | 200 · `/entity` 없음 · `/open`·`/follow` 있음 |
| 제거 | **이미 색인된 뒤** 선언이 붙으면 빠지는가 | `0 문서 색인` + **`1 문서 색인 제외`** |
| 회귀 | `&#` 만 든 문서 · `index, follow` 는 남는가 | 둘 다 색인·검색됨 (오탐 0) |

**새 e2e 파일은 0개다.** 기존 `e2e/noindex_e2e.py` 가 관통과 「뒤늦은 noindex」를 이미
덮고 있었고 **모자란 둘(엔티티 갈래 · 화면 HTTP)만** 그 파일에 더했다. 그래서
`README.md:105` 「e2e 21종」도 `:104` 「단위 632건」도 안 움직인다.

**변이 2판이 각각 다른 단언에서 죽었다** (저장소 밖 `mktemp -d` + `rsync` 사본):
`extract.py` 사전 필터의 `&#` 갈래를 빼면 `1회차 stdout: '4 문서 색인'` 에서,
`indexer.py` 제거 질의의 `OR` 절을 빼면 `엔티티 거부를 제거하지 않았다` 에서 각각
rc 1 이다. 단위(반복 401)가 산 판정을 **끝에서 끝까지에서 되샀다.** V0 성한 사본 rc 0.

## 안 산 것

- **e2e 21종 중 3종만 돌렸다** — 이번 diff 가 지나는 축(`noindex_e2e`·`indexer_e2e`·
  `crawl_e2e`)만. 나머지 18종은 `extract.is_noindex()`·제거 질의를 안 지난다.
- **`quality_eval.py`·`passage_eval.py` 는 못 돌린다** — `data/crawl.db` 를 요구하는데
  이번 phase 의 하드 제약이 **무개봉**이다. 안 돌린 것을 통과로 적지 않았다.
- 리뷰(반복 402)가 등재한 「`</head>` 컷」(`digest ## 다음 계획 후보`, 중요도 4)은
  계획 밖이라 안 건드렸다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
→ Ran 632 tests in 15.889s · OK · rc 0
PYTHONPATH=src python3 e2e/noindex_e2e.py   → rc 0
PYTHONPATH=src python3 e2e/indexer_e2e.py   → rc 0
PYTHONPATH=src python3 e2e/crawl_e2e.py     → rc 0
```

**바깥 네트워크 접속 0**(크롤 대상은 로컬 `http.server` 뿐) · 모든 파이프라인 실행은
`tempfile` 임시 DB · `data/crawl.db` sha256 `85c96744…5bda18` **무변·무개봉** ·
스키마·마이그레이션·재색인·새 의존성 **0** · `docs/specs/` 무접촉 ·
`main` 직접 커밋 0 · PR #7 무접촉(`gh` 0회).

## 다음

**계획 69 DONE.** 새 계획은 탐색하지 않는다 — 다음 루프가 `digest ## 다음 계획 후보`
에서 고른다.
