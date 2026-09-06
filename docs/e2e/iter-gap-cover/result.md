# e2e 결과 — 계획 61 `iter-gap-cover` (반복 360 · 2026-09-06)

**판정: 통과 — 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 6/6 → DONE.**

## 0. 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획 60 과 같은 자리다. 그때처럼 「해당 없음」으로 넘기지 않고 **없다는 것을 오늘 쟀다.**

`rules/e2e.md` 3절은 수단을 넷으로 적는다 — 웹 UI · HTTP API · CLI · 라이브러리.
이 계획의 산출물이 그 넷 중 **어디에도 안 닿는다는 근거 셋**:

1. **프로세스 밖에서 달라진 것이 0.** `git diff --stat a8a052a HEAD -- src/ e2e/ docs/specs/ data/`
   가 **빈손**이다. 움직인 파일은 `tests/test_docs.py`(+78/-…)와 `README.md`(±1) 둘뿐이라
   HTTP 응답·CLI stdout·exit code·DB 스키마 중 무엇도 어제와 다르지 않다.
2. **산출물이 제품 경로에서 도달 불가능하다.** `iter_gap` 은 `tests/test_docs.py` 안의
   모듈 수준 함수이고 `src/` 에는 `tests` 를 import 하는 줄이 **0건**이다
   (`grep -rn "test_docs\|tests\." src/` → 무출력). 「샘플에서 실제 import·호출」이라는
   라이브러리 수단조차 걸 곳이 없다 — 테스트 러너 밖에 이 함수의 호출자가 없다.
3. **전체 명령이 이미 집어간다.** 새 파일을 만들면 `PYTHONPATH=src python3 -m unittest
   discover -b -s tests` 와 겹쳐 「1회만」이 깨진다(`rules/e2e.md` 1절). 겹치는 것을
   또 만드는 것은 ponytail 사다리 1번이다.

**대신 사용자 관점 검증이 하나 있고, 그것을 만들지 않고 실행했다.** 이 가드들의
「사용자」는 **문서를 손으로 고치는 사람**이다. 실물 `docs/` 를 임시 디렉터리로 복사해
사람이 낼 법한 편집 넷을 넣고, 가드가 **소리를 내는지·어디가 어긋났는지 적는지**를 3절에서
쟀다. 저장소 파일은 한 바이트도 안 고쳤다.

## 1. e2e 21종 — 전부 `rc 0`

| # | 시나리오 | rc | 오늘 실측 |
|---|---|---|---|
| 1 | `crawl_e2e.py` | 0 | 수집 15 · 차단 0 · 최소 간격 1.006s |
| 2 | `indexer_e2e.py` | 0 | 3문서 색인 · 증분 0문서 · 없는 상대경로 rc 1 |
| 3 | `noindex_e2e.py` | 0 | 4페이지 중 2문서 · 뒤늦은 noindex 제거 |
| 4 | `search_api_e2e.py` | 0 | 15문서 · 10+5건 겹침 0 · 400/404/501/503/500 · p95 **2.08ms** |
| 5 | `crawl_delay_e2e.py` | 0 | `Crawl-delay:2` 최소 2.01s · 하한 1.00s |
| 6 | `non_ascii_e2e.py` | 0 | 한글 경로 3행 · 서로게이트 시드 1건 건너뜀 |
| 7 | `hidden_passage_e2e.py` | 0 | 숨은 텍스트 **0/5** · 본문 문단 **5/5** · 오탐 대조군 4종 |
| 8 | `design_check.py` | 0 | 4축 통과 · JS **0 B** · 최저 대비 **4.87:1**(포커스 3.56:1) |
| 9 | `tokenizer_e2e.py` | 0 | 화면(HTML)에서 복합어·어순·굴절·AND · 503→재색인 복구 |
| 10 | `domain_key_e2e.py` | 0 | 같은 서버 간격 2.01×3 · robots 1회 · 대조군 1.00 |
| 11 | `deadline_e2e.py` | 0 | 대조군 16 / CLI 8페이지 2.1s · **버려진 응답 0건** |
| 12 | `interrupt_e2e.py` | 0 | SIGINT 10.0s rc 130 · DB 0행 · 두 번째 Ctrl-C rc -2 |
| 13 | `indexer_interrupt_e2e.py` | 0 | 재구축 중단이 옛 2,000행 보존 · 재실행 복구 |
| 14 | `crawl_politeness_e2e.py` | 0 | 예외 뒤 2.01s · 대조군 1.00s · 재시도 1.01s |
| 15 | `pagination_ui_e2e.py` | 0 | 다음을 따라가 doc00 · 마지막에 다음 없음 |
| 16 | `retry_interval_e2e.py` | 0 | https 재시도 5.00s · 대조군 1.01s |
| 17 | `url_normalize_e2e.py` | 0 | 표기 10개가 문서 6개로 |
| 18 | `perf_crawl.py` | 0 | [열림] **10.23/s** · [차단] **10.26/s** · [예외] 간격 1.000s |
| 19 | `perf_search.py` | 0 | p50 1.31ms · **p95 8.69ms** (예산 300ms 의 2.9%) |
| 20 | `quality_eval.py` | 0 | ko **20/20** · en **19/20** · 매치 평균 14.0 · 최소 11 · 최대 28 |
| 21 | `passage_eval.py` | 0 | 정확도 **100.0%** · 채택률 99.5% · p95 **1.51ms** |

전부 맨몸으로 돌렸다 — 파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율).

## 2. 기준선 대조 — 회귀 **0**

| 축 | 오늘 | 기준 | 직전(계획 60) |
|---|---|---|---|
| 근거 문단 정확도 | **100.0%** | ≥90% | 100.0% |
| `/passages` p95 | **1.51ms** | ≤500ms | 1.52ms |
| `/search` p95 | **8.69ms** | ≤300ms | 9.01ms |
| 품질 ko / en | **20/20 · 19/20** | ≥80% | 20/20 · 19/20 |
| 매치 수 평균/최소/최대 | **14.0 / 11 / 28** | 기록 | 14.0 / 11 / 28 |
| 크롤 [열림] / [차단] | **10.23 / 10.26** | 5.0 / 9.0 | 10.20 / 10.20 |
| 디자인 JS / 최저 대비 | **0 B / 4.87:1** | 50KB / 4.5:1 | 0 B / 4.87:1 |
| 숨은 텍스트 문단 | **0/5** | 0/5 | 0/5 |

**움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도 안 갱신했다.** 계획이 제품
`src/` 를 0줄 고쳤으니 당연한 결과고, 이 표는 그 「당연함」이 실제로 그런지를 잰 것이다.

## 3. 사용자 관점 검증 — 실물 `docs/` 복사본에 사람이 낼 편집 넷

`docs/` 와 `tests/test_docs.py` 를 `mktemp -d` 아래로 복사하고 그 **복사본만** 고쳤다
(`DOCS = Path(__file__).resolve().parent.parent / "docs"` 라 복사본이 자기 옆 문서를 읽는다).
저장소 워킹트리는 매 실행 뒤 `git status --short` 빈손이다.

| # | 편집(사람이 낼 법한 것) | 결과 | 가드가 낸 말 |
|---|---|---|---|
| D0 | 손 안 댐 (대조군) | `Ran 5 · OK` | — |
| D1 | `metrics.md` 의 `\| 반복 \| 359 \|` → `358` | `IterationSyncTest failures=1` | `반복 번호가 어긋났다 — metrics.md `반복` 358 ≠ status.md `iteration` 359` |
| D2 | `status.md` 의 `iteration: 359` → `358` | `IterationSyncTest failures=1` | `… metrics.md `반복` 359 ≠ status.md `iteration` 358` |
| D3 | `metrics.md` 의 행 이름을 `반복수` 로 | `IterationSyncTest failures=1` | `metrics.md 에서 `\| 반복 \| <수> \|` 행을 못 찾았다` |
| D4 | `status.md` 의 줄 이름을 `iterations:` 로 | `IterationSyncTest failures=1` | `status.md 에서 `iteration: <수>` 줄을 못 찾았다` |

**D1·D2 의 방향이 서로 반대라 한쪽만 재는 검사가 아니다**(계획 60 의 M2·M3 과 같은 확인).
**D0~D4 어디서도 `IterGapTest` 4건은 안 흔들린다** — 합성 문자열 위에서 돌기 때문이고,
그것이 두 층을 가른 목적 그대로다. 실물이 흔들리면 `IterationSyncTest` 만, 함수가
썩으면 `IterGapTest` 만 죽는다.

## 4. 완료 기준 6/6 — 오늘 전부 다시 쟀다

| # | 실측 | 기준 | 판정 |
|---|---|---|---|
| 1 | M1 → `test_iteration_mismatch_is_reported` · M2 → `test_missing_metrics_row_is_reported` · M3 → `test_missing_status_line_is_reported` · M4 → 그 셋. 무변이 대조군 `Ran 618 · 죽은 것 0건` | M1~M4 가 **4/4 사망**하고 각각 의도한 이름을 죽인다 | 충족 |
| 2 | M4(`iter_gap` 이 늘 `None`) 에서 `IterGapTest` **3건 사망** | 양성 대조에서 **3건 이상** | 충족 |
| 3 | M5(`ITER_ROW` 를 `^\| 반복[^\|]*\| ([0-9]+) \|` 로 넓힘)에서 `IterationPatternTest.test_only_the_exact_row_matches` **사망** (덤으로 `test_missing_metrics_row_is_reported` 도 죽어 **감지력이 낮아지지 않았다**) | 정규식 축의 감지력이 유지된다 | 충족 |
| 4 | `Ran 618 tests in 15.835s` · `OK` · rc 0 (맨몸) · `README.md` 러너 줄이 `단위 618건`·`e2e 시나리오 21종` 이고 `tests/test_readme.py` 가 전수 안에서 초록 | 전수 `OK` · rc 0 · README 숫자 일치 | 충족 |
| 5 | `git diff --stat a8a052a HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변 | 제품 `src/` 0줄 · 스키마·재색인·새 의존성 0 | 충족 |
| 6 | `status.md` `step: 1/1` ↔ `index.md` 61번 행 스텝 칸 `1/1` · `StepSyncTest` 가 전수 안에서 초록 (이 계획의 매 커밋에서) | 계획 60 이 세운 `StepSyncTest` 가 이 계획 위에서 실제로 돈다 | 충족 |

**변이 하네스는 메모리 전용이다** — `tests.test_docs` 를 import 한 뒤 모듈 속성
`iter_gap`·`ITER_ROW` 를 갈아 끼우고 전수를 돌린다. 계획 58 의 `mock.patch.object`
관용구와 같은 자리고, 저장소 파일은 6회 실행 내내 무변경이다(누적 38 유지).

## 5. 한도 — 지킨 것

- **러너 규율 위반 0회(누적 38 유지).** 전수·e2e 21종·변이 6판·문서 변이 5판을 전부
  맨몸으로 돌렸다. 리다이렉션·파이프·`grep`·`head` 를 붙이지 않았다.
- **변이는 저장소 밖에서 걸었다** — 코드 변이는 메모리, 문서 변이는 `mktemp -d` 복사본.
  워킹트리는 이 phase 내내 `git status --short` 빈손이었다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0 · `docs/specs/` 읽기만.
- 원격 `loop/passage-cost-band` 위에 오늘 커밋을 쌓는다. `origin/main`(`d1fe3e9`) 무접촉 ·
  PR 0(만들지도 조회하지도 않았다) · `--force`·`--amend`·`rebase` 0회. 병합은 사람 몫이다.
- 도구 산출물 없음 — Playwright 같은 브라우저 도구를 쓰지 않는 프로젝트라
  `test-results/` 에 해당하는 경로가 없다. 위 표의 숫자가 실행 출력 전부다.
