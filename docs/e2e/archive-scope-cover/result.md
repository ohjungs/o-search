# e2e 결과 — 계획 64 `archive-scope-cover` (반복 375 · 2026-09-06)

**판정: 통과 — 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 9/9 → DONE.**

## 0. 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획 61·62·63 과 같은 자리다. 그때처럼 「해당 없음」으로 넘기지 않고 **없다는 것을 오늘 쟀다.**

`rules/e2e.md` 3절은 수단을 넷으로 적는다 — 웹 UI · HTTP API · CLI · 라이브러리.
이 계획의 산출물이 그 넷 중 **어디에도 안 닿는다는 근거 셋**:

1. **프로세스 밖에서 달라진 것이 0.** `git diff --stat ba53783 HEAD -- src/ e2e/ docs/specs/ data/`
   가 **빈손**(rc 0, 무출력)이다. 움직인 파일은 `tests/test_docs.py`(+39줄)와 `README.md`
   건수 한 줄, 그리고 기록 문서들뿐이라 HTTP 응답·CLI stdout·exit code·DB 스키마 중
   무엇도 어제와 다르지 않다.
2. **산출물이 제품 경로에서 도달 불가능하다.** 오늘 고친 것은 `tests/test_docs.py` 의
   모듈 상수 `ARCHIVE` 를 재는 새 클래스 하나(`ArchivePatternTest`)이고, `src/` 에는
   `tests` 를 import 하는 줄이 **0건**이다(`grep -rn "test_docs\|tests\." src/` → 무출력, rc 1).
   「샘플에서 실제 import·호출」이라는 라이브러리 수단조차 걸 곳이 없다.
3. **전체 명령이 이미 집어간다.** 새 파일을 만들면 `PYTHONPATH=src python3 -m unittest
   discover -b -s tests` 와 겹쳐 「1회만」이 깨진다(`rules/e2e.md` 1절). 겹치는 것을
   또 만드는 것은 ponytail 사다리 1번이다.

**새 e2e 파일 0개** — `ls e2e/*.py` 는 어제와 같은 **21개**고 `README.md` 의
「e2e 시나리오 21종」이 그대로 맞다.

**대신 사용자 관점 검증이 하나 있고, 그것을 만들지 않고 실행했다**(3절). 이 가드의
「사용자」는 **문서를 손으로 고치거나 회전을 돌리는 사람**이다.

## 1. e2e 21종 — 전부 `rc 0`

| # | 시나리오 | rc | 오늘 실측 |
|---|---|---|---|
| 1 | `crawl_e2e.py` | 0 | 수집 15 · 차단 요청 0 · 최소 간격 1.005s |
| 2 | `indexer_e2e.py` | 0 | 3문서 색인 · 증분 0문서 · 없는 상대경로 rc 1 |
| 3 | `noindex_e2e.py` | 0 | 4페이지 중 2문서 · 뒤늦은 noindex 제거 |
| 4 | `search_api_e2e.py` | 0 | 15문서 · 10+5건 겹침 0 · 400/404/501/503/500 · p95 **2.08ms** |
| 5 | `crawl_delay_e2e.py` | 0 | `Crawl-delay:2` 최소 2.01s · 하한 1.00s |
| 6 | `non_ascii_e2e.py` | 0 | 한글 경로 3행 · 서로게이트 시드 1건 건너뜀 |
| 7 | `hidden_passage_e2e.py` | 0 | 숨은 텍스트 **0/5** · 본문 문단 **5/5** · 오탐 대조군 4종 |
| 8 | `design_check.py` | 0 | 4축 통과 · JS **0 B** · 최저 대비 **4.87:1**(포커스 3.56:1) |
| 9 | `tokenizer_e2e.py` | 0 | 화면(HTML)에서 복합어·어순·굴절·AND · 503→재색인 복구 |
| 10 | `domain_key_e2e.py` | 0 | 같은 서버 간격 2.01×3 · robots 1회 · 대조군 1.01/1.00 |
| 11 | `deadline_e2e.py` | 0 | 대조군 16 / CLI 8페이지 2.1s · **버려진 응답 0건** |
| 12 | `interrupt_e2e.py` | 0 | SIGINT 10.0s rc 130 · DB 0행 · 두 번째 Ctrl-C rc -2 |
| 13 | `indexer_interrupt_e2e.py` | 0 | 재구축 중단이 옛 2,000행 보존 · 재실행 복구 |
| 14 | `crawl_politeness_e2e.py` | 0 | 예외 뒤 2.01s · 대조군 1.00s · 재시도 1.01s |
| 15 | `pagination_ui_e2e.py` | 0 | 다음을 따라가 doc00 · 마지막에 다음 없음 |
| 16 | `retry_interval_e2e.py` | 0 | https 재시도 5.01s · 대조군 1.00s |
| 17 | `url_normalize_e2e.py` | 0 | 표기 10개가 문서 6개로 |
| 18 | `perf_crawl.py` | 0 | [열림] **10.25/s** · [차단] **10.26/s** · [예외] 간격 1.001s |
| 19 | `perf_search.py` | 0 | p50 1.35ms · **p95 8.95ms** (예산 300ms 의 3.0%) |
| 20 | `quality_eval.py` | 0 | ko **20/20** · en **19/20** · 매치 평균 14.0 · 최소 11 · 최대 28 |
| 21 | `passage_eval.py` | 0 | 정확도 **100.0%** · 채택률 99.5% · p95 **1.51ms** |

전부 맨몸으로 돌렸다 — 파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율).

## 2. 기준선 대조 — 회귀 **0**

| 축 | 오늘 | 기준 | 직전(계획 63) |
|---|---|---|---|
| 근거 문단 정확도 | **100.0%** | ≥90% | 100.0% |
| `/passages` p95 | **1.51ms** | ≤500ms | 1.52ms |
| `/search` p95 | **8.95ms** | ≤300ms | 9.01ms |
| 품질 ko / en | **20/20 · 19/20** | ≥80% | 20/20 · 19/20 |
| 매치 수 평균/최소/최대 | **14.0 / 11 / 28** | 기록 | 14.0 / 11 / 28 |
| 크롤 [열림] / [차단] | **10.25 / 10.26** | 5.0 / 9.0 | 10.24 / 10.26 |
| 디자인 JS / 최저 대비 | **0 B / 4.87:1** | 50KB / 4.5:1 | 0 B / 4.87:1 |
| 숨은 텍스트 문단 | **0/5** | 0/5 | 0/5 |

**여덟 축 전부 같은 띠 안이고 움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도
안 갱신했다.** `/search` p95 가 9.01 → 8.95ms 로, `/passages` p95 가 1.52 → 1.51ms 로
내렸지만 각각 예산의 3.0%·0.3% 라 잡음이다(계획 60~63 이 9.01·8.69·8.78·9.01 이었다).
계획이 제품 `src/` 를 0줄 고쳤으니 당연한 결과고, 이 표는 그 「당연함」이 실제로 그런지를 잰 것이다.

## 3. 사용자 관점 검증 — 실물 `docs/` 복사본에 사람이 낼 편집 일곱

`docs/` 와 `tests/test_docs.py` 를 `mktemp -d` 아래로 복사하고 그 **복사본만** 고쳤다
(`DOCS = Path(__file__).resolve().parent.parent / "docs"` 라 복사본이 자기 옆 문서를 읽는다).
이번 축은 **`ARCHIVE` 가 정하는 «검사 대상 밖» 의 경계**다. 넣은 편집은 전부 같은 한 줄
(``- 자세한 것은 `history_current.md` 12행 을 본다.``)이고 **어느 파일에 넣느냐만** 바꿨다 —
그것이 `ARCHIVE` 가 혼자 정하는 축이기 때문이다. 저장소 워킹트리는 매 실행 뒤
`git status --porcelain` 이 이번 회전 산출물(`docs/history_065.md` 등)뿐이었다.

| # | 편집(사람이 낼 법한 것) | 결과 | 가드가 낸 말 |
|---|---|---|---|
| D0 | 손 안 댐 (대조군) | `Ran 28 · OK` | — |
| D1 | `docs/index.md` 끝에 인용 한 줄 | `failures=1` | `append 전용 문서를 줄번호로 가리킨 인용 … index.md 599행:` |
| D2 | **아카이브** `docs/history_065.md` 에 같은 줄 | `Ran 28 · OK` | — (`ARCHIVE` 가 정확히 이걸 빼려고 있다) |
| D3 | `docs/history_001.md.bak.md` 를 새로 만들어 같은 줄 | `failures=2` | `DocCitationTest` + `ArchiveIndexTest` |
| D4 | `docs/history_.md`(숫자 0개) 를 새로 만들어 같은 줄 | `failures=1` | `… history_.md 2행:` |
| D5 | `docs/design_history_099.md` 를 새로 만들어 같은 줄 | `Ran 28 · OK` | — (아카이브다) |
| D6 | `docs/plan_history_099.md` 를 새로 만들어 같은 줄 | `Ran 28 · OK` | — (아카이브다) |

**D2·D5·D6 과 D3·D4 가 서로 반대 방향이라 한쪽만 재는 검사가 아니다** — 「빼야 할 것을
빼는가」와 「빼면 안 될 것을 안 빼는가」를 실물에서 각각 걸었다. **오늘 계획이 산 자리는
D3·D4 다**: 이 계획 전이라면 판정은 같았겠지만 `ARCHIVE` 가 `$` 나 수량자를 잃어도
아무도 안 울었으므로 D3·D4 가 **조용해지는 날을 막을 자가 없었다**. 오늘부터는
`ArchivePatternTest.test_pattern_leaves_live_docs` 가 그 세 이름을 리터럴로 붙든다.

**D0 이 처음엔 빨갰고 그것이 회전 절차를 잡았다.** 회전으로 `history_065.md` 를 만든 직후
아직 `digest.md` 명부에 이름을 안 넣은 상태에서 대조군을 돌리니 `ArchiveIndexTest` 가
「아카이브가 `digest.md` 의 `## 완료` 명부에 없다」로 울었다 — 계획 64 의 형제 가드가
**이번 회전 자체를 검사한** 셈이고, 명부를 채운 뒤 초록으로 돌아왔다.

## 4. 완료 기준 9/9 — 오늘 전부 다시 쟀다

메모리 전용 하네스(`mock.patch.object` 로 모듈 상수 교체, 저장소 밖 · 워킹트리 무접촉 ·
`PYTHONDONTWRITEBYTECODE=1` + `PYTHONPYCACHEPREFIX=$(mktemp -d)`)로 **열여덟 판**을 돌렸다.
`_SubTest` 가 이름을 삼키므로 실패를 `test_case` 로 되짚어 클래스·메서드까지 찍었다.

| # | 실측 | 기준 | 판정 |
|---|---|---|---|
| 1 | M3(`ARCHIVE` `$` 제거) → `Ran 622 · 1건` · `ArchivePatternTest.test_pattern_leaves_live_docs` | 1건 이상 죽는다 | 충족 |
| 2 | M4(`re.I`) → `Ran 622 · 1건` · 같은 이름 | 1건 이상 | 충족 |
| 3 | M5(`[0-9]+`→`[0-9]*`) → `Ran 622 · 1건` · 같은 이름 | 1건 이상 | 충족 |
| 4 | M11(`design_history` 제거) → `Ran 622 · 1건` · `…test_pattern_catches_archive_names` | 1건 이상 | 충족 |
| 5 | M10(`_[0-9]+`→`.*`) **4건**(`test_pattern_leaves_live_docs` 셋 + `DocCitationTest`) · M1·M2·M8 이 **1·2·3건**(`CitationPatternTest` ×1, ×2, `CitationPatternTest`+`DocCitationTest`+`DocHeadTest`) · 앵커 변이 일곱(`STEP_LINE` `^`·`$` · `PLAN_SLUG` `^` · `ITER_ROW` `^` · `STEP_ROW` `^` · `ITER_LINE` `^`·`$`) 각 **1건** | 감지력 무회귀 | 충족 |
| 6 | M0 무변이 대조군 `Ran 622 · 죽은 단언 0건` · 실물 문서 한 글자도 안 고침 | 오탐 0 | 충족 |
| 7 | 맨몸 전수 `Ran 622 tests in 15.941s` · `OK` · **rc 0** · `README.md:104` 「단위 622건」 ↔ 실제 622 일치 · 「e2e 시나리오 21종」 ↔ `ls e2e/*.py` 21개 | 전수 초록 · README 일치 | 충족 |
| 8 | `git diff --stat ba53783 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변 | 제품 `src/` 0줄 · 스키마·재색인·새 의존성 0 | 충족 |
| 9 | `digest` 의 `[5]` 항목에 2절의 정정(① 은 하네스 인공물 · 값은 `ARCHIVE` 에 있고 M11 이 그 항목에 없던 것)이 적혀 있고, 오늘 그 문장이 가리키는 수(1·2·3 / 4 / 1)를 다시 재서 전부 재현했다 | 정정이 기록된다 | 충족 |

**5번의 「감지력 무회귀」를 계획 63 이 세운 앵커 다섯이 아니라 일곱으로 넓혀 쟀다** —
계획 62 의 `ITER_LINE` 둘까지 같은 판에 넣었다. 일곱 전부 오늘도 각 1건이고 죽는 이름도
그대로다(`StepPatternTest` 셋 · `IterationPatternTest` 넷 중 둘 + `test_only_the_exact_row_matches`).

## 5. 등가 주장을 한 번 더 실행으로 확인했다

계획서 5절이 「M6(`^` 제거)은 **완전 등가**라 안 잰다」로 남긴 것을 오늘 판으로 세워 다시 밟았다.

| 주장 | 실측 |
|---|---|
| M6(`ARCHIVE` 에서 `^` 제거) 는 등가 — 잴 값이 0 | `Ran 622 · 죽은 단언 0건` — **맞다** |
| 양성 대조 `^ZZZ_[0-9]+\.md$` 는 배선을 증명한다 | **4건** — `test_pattern_catches_archive_names` 셋 + `DocCitationTest` |
| `ARCHIVE` 의 제품 소비자는 `tests/test_docs.py` 의 `ARCHIVE.match()` 하나뿐 | `grep` 결과 그 한 곳 · `src/` 에서 `tests` 를 import 하는 줄 0건 |

**M6 이 0 이고 P 가 4 인 것이 같은 판에서 나온 것이 요점이다** — 하네스가 죽어서 0 이
아니라, 하네스가 살아 있는데도 0 이다. 등가라는 말이 「안 재도 된다」의 근거로 서려면
이 두 줄이 **함께** 있어야 한다.

## 6. 한도 — 지킨 것

- **러너 규율 위반 0회(누적 38 유지).** 전수·e2e 21종·변이 18판·문서 편집 7판을 전부
  맨몸으로 돌렸다. 판정 줄(`Ran … / OK / rc`)을 매번 눈으로 확인했다.
- **변이는 저장소 밖에서 걸었다** — 코드 변이는 메모리(`mock.patch.object`), 문서 변이는
  `mktemp -d` 복사본. 워킹트리에는 이 phase 의 문서 산출물 외에 아무것도 안 생겼다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0(stdlib) · `docs/specs/` 읽기만.
- 원격 `loop/passage-cost-band` 위에 오늘 커밋을 쌓는다. `origin/main`(`d1fe3e9`) 무접촉 ·
  PR #7 무접촉(`gh` 호출 0) · `--force`·`--amend`·`rebase` 0회. 병합은 사람 몫이다.
- 도구 산출물 없음 — 브라우저 도구를 쓰지 않는 프로젝트라 `test-results/` 에 해당하는
  경로가 없다. 위 표의 숫자가 실행 출력 전부다.
