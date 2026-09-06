# e2e 결과 — 계획 63 `anchor-net-cover` (반복 370 · 2026-09-06)

**판정: 통과 — 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 8/8 → DONE.**

## 0. 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획 61·62 와 같은 자리다. 그때처럼 「해당 없음」으로 넘기지 않고 **없다는 것을 오늘 쟀다.**

`rules/e2e.md` 3절은 수단을 넷으로 적는다 — 웹 UI · HTTP API · CLI · 라이브러리.
이 계획의 산출물이 그 넷 중 **어디에도 안 닿는다는 근거 셋**:

1. **프로세스 밖에서 달라진 것이 0.** `git diff --stat 1752ecc HEAD -- src/ e2e/ docs/specs/ data/`
   가 **빈손**이다. 움직인 파일은 `tests/test_docs.py`(+25/-8)와 기록 문서들뿐이라
   HTTP 응답·CLI stdout·exit code·DB 스키마 중 무엇도 어제와 다르지 않다.
   `README.md` 는 이번엔 무접촉이다 — 건수가 620 그대로다(4절 6번).
2. **산출물이 제품 경로에서 도달 불가능하다.** 오늘 고친 것은 `tests/test_docs.py` 의
   모듈 상수 넷(`STEP_LINE`·`PLAN_SLUG`·`ITER_ROW`·`STEP_ROW`)이고 `src/` 에는
   `tests` 를 import 하는 줄이 **0건**이다(`grep -rn "test_docs\|tests\." src/` → 무출력, rc 1).
   「샘플에서 실제 import·호출」이라는 라이브러리 수단조차 걸 곳이 없다.
3. **전체 명령이 이미 집어간다.** 새 파일을 만들면 `PYTHONPATH=src python3 -m unittest
   discover -b -s tests` 와 겹쳐 「1회만」이 깨진다(`rules/e2e.md` 1절). 겹치는 것을
   또 만드는 것은 ponytail 사다리 1번이다.

**새 e2e 파일 0개** — `ls e2e/*.py` 는 어제와 같은 **21개**고 `README.md` 의
「e2e 시나리오 21종」이 그대로 맞다.

**대신 사용자 관점 검증이 하나 있고, 그것을 만들지 않고 실행했다**(3절). 이 가드들의
「사용자」는 **문서를 손으로 고치는 사람**이다.

## 1. e2e 21종 — 전부 `rc 0`

| # | 시나리오 | rc | 오늘 실측 |
|---|---|---|---|
| 1 | `crawl_e2e.py` | 0 | 수집 15 · 차단 요청 0 · 최소 간격 1.005s |
| 2 | `indexer_e2e.py` | 0 | 3문서 색인 · 증분 0문서 · 없는 상대경로 rc 1 |
| 3 | `noindex_e2e.py` | 0 | 4페이지 중 2문서 · 뒤늦은 noindex 제거 |
| 4 | `search_api_e2e.py` | 0 | 15문서 · 10+5건 겹침 0 · 400/404/501/503/500 · p95 **2.10ms** |
| 5 | `crawl_delay_e2e.py` | 0 | `Crawl-delay:2` 최소 2.00s · 하한 1.00s |
| 6 | `non_ascii_e2e.py` | 0 | 한글 경로 3행 · 서로게이트 시드 1건 건너뜀 |
| 7 | `hidden_passage_e2e.py` | 0 | 숨은 텍스트 **0/5** · 본문 문단 **5/5** · 오탐 대조군 4종 |
| 8 | `design_check.py` | 0 | 4축 통과 · JS **0 B** · 최저 대비 **4.87:1**(포커스 3.56:1) |
| 9 | `tokenizer_e2e.py` | 0 | 화면(HTML)에서 복합어·어순·굴절·AND · 503→재색인 복구 |
| 10 | `domain_key_e2e.py` | 0 | 같은 서버 간격 2.01×3 · robots 1회 · 대조군 1.01/1.00 |
| 11 | `deadline_e2e.py` | 0 | 대조군 16 / CLI 8페이지 2.2s · **버려진 응답 0건** |
| 12 | `interrupt_e2e.py` | 0 | SIGINT 10.0s rc 130 · DB 0행 · 두 번째 Ctrl-C rc -2 |
| 13 | `indexer_interrupt_e2e.py` | 0 | 재구축 중단이 옛 2,000행 보존 · 재실행 복구 |
| 14 | `crawl_politeness_e2e.py` | 0 | 예외 뒤 2.01s · 대조군 1.00s · 재시도 1.00s |
| 15 | `pagination_ui_e2e.py` | 0 | 다음을 따라가 doc00 · 마지막에 다음 없음 |
| 16 | `retry_interval_e2e.py` | 0 | https 재시도 5.01s · 대조군 1.01s |
| 17 | `url_normalize_e2e.py` | 0 | 표기 10개가 문서 6개로 |
| 18 | `perf_crawl.py` | 0 | [열림] **10.24/s** · [차단] **10.26/s** · [예외] 간격 1.002s |
| 19 | `perf_search.py` | 0 | p50 1.35ms · **p95 9.01ms** (예산 300ms 의 3.0%) |
| 20 | `quality_eval.py` | 0 | ko **20/20** · en **19/20** · 매치 평균 14.0 · 최소 11 · 최대 28 |
| 21 | `passage_eval.py` | 0 | 정확도 **100.0%** · 채택률 99.5% · p95 **1.52ms** |

전부 맨몸으로 돌렸다 — 파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율).

## 2. 기준선 대조 — 회귀 **0**

| 축 | 오늘 | 기준 | 직전(계획 62) |
|---|---|---|---|
| 근거 문단 정확도 | **100.0%** | ≥90% | 100.0% |
| `/passages` p95 | **1.52ms** | ≤500ms | 1.52ms |
| `/search` p95 | **9.01ms** | ≤300ms | 8.78ms |
| 품질 ko / en | **20/20 · 19/20** | ≥80% | 20/20 · 19/20 |
| 매치 수 평균/최소/최대 | **14.0 / 11 / 28** | 기록 | 14.0 / 11 / 28 |
| 크롤 [열림] / [차단] | **10.24 / 10.26** | 5.0 / 9.0 | 10.21 / 10.23 |
| 디자인 JS / 최저 대비 | **0 B / 4.87:1** | 50KB / 4.5:1 | 0 B / 4.87:1 |
| 숨은 텍스트 문단 | **0/5** | 0/5 | 0/5 |

`/search` p95 가 8.78 → 9.01ms 로 0.23ms 움직였지만 **예산 300ms 의 3.0%** 라 회귀가
아니라 잡음이다(계획 61 은 8.69, 60 은 9.01 이었다 — 같은 띠 안이다).
**움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도 안 갱신했다.** 계획이 제품
`src/` 를 0줄 고쳤으니 당연한 결과고, 이 표는 그 「당연함」이 실제로 그런지를 잰 것이다.

## 3. 사용자 관점 검증 — 실물 `docs/` 복사본에 사람이 낼 편집 여덟

`docs/` 와 `tests/test_docs.py` 를 `mktemp -d` 아래로 복사하고 그 **복사본만** 고쳤다
(`DOCS = Path(__file__).resolve().parent.parent / "docs"` 라 복사본이 자기 옆 문서를 읽는다).
이번 축은 **`status.md` 의 `step:`·`plan:` 줄과 `index.md`·`metrics.md` 의 표 행**이다.
저장소 워킹트리는 매 실행 뒤 `git status --porcelain` 빈손이다.

| # | 편집(사람이 낼 법한 것) | 결과 | 가드가 낸 말 |
|---|---|---|---|
| D0 | 손 안 댐 (대조군) | `Ran 26 · OK` | — |
| D1 | `status.md` `step: 1/1` → `1/2` | `StepSyncTest failures=1` | `스텝이 어긋났다 — index.md \`plan_anchor-net-cover\` 1/1 ≠ status.md \`step\` 1/2` |
| D2 | `index.md` 63번 행 스텝 칸 `1/1` → `2/2` | `StepSyncTest failures=1` | `… index.md … 2/2 ≠ status.md \`step\` 1/1` |
| D3 | `status.md` 의 `step:` 줄을 들여씀 | `StepSyncTest failures=1` | `status.md 에서 \`step: <N/M>\` 줄을 못 찾았다` |
| D4 | `status.md` `step: 1/1` 뒤에 `(리뷰까지 끝)` 메모를 붙임 | `StepSyncTest failures=1` | 같은 말 |
| D5 | `index.md` 63번 행 **앞에** 줄 중간에서 시작하는 메모 행(같은 슬러그·`9/9`) | `Ran 26 · OK` | — (오판 0) |
| D6 | `metrics.md` `\| 반복 \| 369 \|` **앞에** 메모 행(`999`) | `Ran 26 · OK` | — (오판 0) |
| D7 | `status.md` `plan:` 슬러그에 `-2` 접미 | `StepSyncTest failures=1` | `index.md 에서 \`\| plan_anchor-net-cover-2 \|\` 행의 스텝 칸을 못 읽었다 — 등재가 빠졌거나 표의 열 모양이 바뀌었다` |

**D1·D2 의 방향이 서로 반대라 한쪽만 재는 검사가 아니다**(계획 60·61 과 같은 확인).
**오늘 계획이 산 자리는 D5·D6 이다** — 사람이 표에 메모 행을 끼워도 가드가 **엉뚱한 수를
집지 않는다**. 이 계획 전이라면 판정은 같았겠지만 그 「같음」을 지키는 앵커가 무방비였고
(4절 1~4번), 오늘부터는 앵커가 죽으면 D5·D6 의 값(`9/9`·`999`)을 집어 **빨개진다**.
**D3·D4 는 같은 말을 낸다** — `^`·`$` 중 어느 쪽이 깨졌는지는 안 가른다. 실물 가드의
목적이 「읽었나 못 읽었나」라 그대로 뒀고, 앵커별 구분은 합성 리터럴 쪽(`StepPatternTest`)이
값→범인 대응으로 가른다.

## 4. 완료 기준 8/8 — 오늘 전부 다시 쟀다

메모리 전용 하네스(`mock.patch.object` 로 모듈 상수 교체, 저장소 밖)로 여덟 판을 돌렸다.

| # | 실측 | 기준 | 판정 |
|---|---|---|---|
| 1 | M1a(`^` 만 제거)·M1b(`$` 만 제거) **각각 `Ran 620 · failures=1`** 이고 죽은 것은 둘 다 `StepPatternTest.test_status_lines_need_the_whole_line` | 두 변이 **따로** 걸어 둘 다 죽는다 | 충족 |
| 2 | M2(`PLAN_SLUG` `^` 제거) → 같은 시험 1건 사망 | 같은 시험이 죽는다 | 충족 |
| 3 | M3(`ITER_ROW` `^` 제거) → `IterationPatternTest.test_only_the_exact_row_matches` 1건 사망 | 그 이름이 죽는다 | 충족 |
| 4 | M4(`STEP_ROW` `^` 제거) → `StepPatternTest.test_row_is_picked_by_exact_slug` 1건 사망 | 그 이름이 죽는다 | 충족 |
| 5 | M0 무변이 대조군 `Ran 620 · OK · 죽은 것 0건`(오탐 0) · 계획 62 의 M5a(`ITER_LINE` `^`)·M5b(`$`)가 **각각 1건**씩 `IterationPatternTest.test_status_line_needs_the_whole_line` 을 그대로 죽인다 | 오탐 0 · 감지력 무회귀 | 충족 |
| 6 | 맨몸 전수 `Ran 620 tests in 15.874s` · `OK` · rc 0 · `README.md:104` 「단위 620건」 ↔ 실제 620 일치 · 「e2e 시나리오 21종」 ↔ `ls e2e/*.py` 21개 | 전수 초록 · README 일치 (**건수 증가 요구는 테스트 phase 가 무효화**) | 충족 |
| 7 | `git diff --stat 1752ecc HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변 | 제품 `src/` 0줄 · 스키마·재색인·새 의존성 0 | 충족 |
| 8 | `status.md` `step: 1/1` ↔ `index.md` 63번 행 스텝 칸 `1/1` · `StepSyncTest` 가 전수 안에서 초록이고 3절 D1·D2 에서 **양방향으로 문다** | 계획 60 의 `StepSyncTest` 가 이 계획 위에서 실제로 돈다 | 충족 |

**6번의 「정정」이 단언을 낮췄는지 e2e 도 다시 쟀다 — 안 낮췄다.** `test_readme.UNIT_COUNT`
를 「못 뽑는 꼴」(`단위 N개`)로 갈면 `test_verification_counts_match_reality` 1건 사망,
「다른 수를 뽑는 꼴」(`(\d+)`)로 갈아도 1건 사망, `E2E_COUNT` 를 같은 식으로 갈아도 1건
사망이다. 무변이 대조군은 `Ran 620 · OK`. 즉 README 대조는 **세 갈래 다 살아 있고**,
정정이 지운 것은 「메서드 수가 는다」는 예측 하나뿐이다.

## 5. 주석·리터럴을 실물과 대조했다 (계획 62 e2e 의 교훈)

계획 62 e2e 는 「실물을 좇는다고 읽히는 주석」이 실물과 어긋난 것을 잡았다. 오늘 diff 의
주장 다섯을 같은 방식으로 실측했다 — **어긋난 곳 0**.

| 주장(주석·실패 메시지) | 실측 |
|---|---|
| `StepPatternTest` ④ 「`^` 를 지운 변이는 이 행의 `8/8` 을 집는다」 | 실물 `1/1` · `^` 제거 **`8/8`** — 맞다 |
| 실패 메시지 「`9/9` 면 슬러그를 안 본다」 | 슬러그를 안 보는 정규식 → **`9/9`** |
| 실패 메시지 「`3/7` 이면 접두로 집었다」 | 이름 뒤 ` \| ` 를 뺀 정규식 → **`3/7`** |
| 「표의 수를 서로 다르게 두는 것이 조건」(리뷰가 넣은 주석) | 표의 넷이 `9/9`·`3/7`·`8/8`·`1/1` — 겹침 0 |
| `IterationPatternTest` 「네 번째 행이 잡음 행 · `^` 지우면 `999`」 | 표 5행 중 **네 번째**가 그 행 · 실물 `232` · `^` 제거 **`999`** |
| 「위 세 줄은 형식만 잰다 — 앵커를 지워도 초록」 | 옛 리터럴 `"step: 1/1"`·`"step: 1"` 은 앵커 없는 변이에서도 판정 동일 — 맞다 |

## 6. 한도 — 지킨 것

- **러너 규율 위반 0회(누적 38 유지).** 전수·e2e 21종·변이 12판(앵커 8 + README 4)·
  문서 편집 8판을 전부 맨몸으로 돌렸다. 리다이렉션·파이프·`grep`·`head` 를 안 붙였다.
- **변이는 저장소 밖에서 걸었다** — 코드 변이는 메모리(`mock.patch.object`), 문서 변이는
  `mktemp -d` 복사본. 워킹트리는 이 phase 내내 `git status --porcelain` 빈손이었다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0 · `docs/specs/` 읽기만.
- 원격 `loop/passage-cost-band` 위에 오늘 커밋을 쌓는다. `origin/main`(`d1fe3e9`) 무접촉 ·
  PR #7 무접촉(`gh pr` 호출 0) · `--force`·`--amend`·`rebase` 0회. 병합은 사람 몫이다.
- 도구 산출물 없음 — 브라우저 도구를 쓰지 않는 프로젝트라 `test-results/` 에 해당하는
  경로가 없다. 위 표의 숫자가 실행 출력 전부다.
