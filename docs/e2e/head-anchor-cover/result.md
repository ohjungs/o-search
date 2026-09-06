# e2e 결과 — 계획 62 `head-anchor-cover` (반복 365 · 2026-09-06)

**판정: 통과 — 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 7/7 → DONE.**
다만 **e2e 가 리뷰 세 프로세스가 놓친 사실 하나를 잡았다** — 3절 아래 「주석이 실물과
어긋난다」. 저심각도(주석 전용)라 계획 범위 안에서 그 자리만 고쳤다(6절).

## 0. 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획 60·61 과 같은 자리다. 그때처럼 「해당 없음」으로 넘기지 않고 **없다는 것을 오늘 쟀다.**

`rules/e2e.md` 3절은 수단을 넷으로 적는다 — 웹 UI · HTTP API · CLI · 라이브러리.
이 계획의 산출물이 그 넷 중 **어디에도 안 닿는다는 근거 셋**:

1. **프로세스 밖에서 달라진 것이 0.** `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/`
   가 **빈손**이다. 움직인 파일은 `tests/test_docs.py` 와 `README.md`(±1) 둘뿐이라
   HTTP 응답·CLI stdout·exit code·DB 스키마 중 무엇도 어제와 다르지 않다.
2. **산출물이 제품 경로에서 도달 불가능하다.** `DOC_HEAD` 는 `tests/test_docs.py` 안의
   모듈 상수이고 `src/` 에는 `tests` 를 import 하는 줄이 **0건**이다
   (`grep -rn "test_docs\|tests\." src/` → 무출력). 「샘플에서 실제 import·호출」이라는
   라이브러리 수단조차 걸 곳이 없다 — 테스트 러너 밖에 이 상수의 독자가 없다.
3. **전체 명령이 이미 집어간다.** 새 파일을 만들면 `PYTHONPATH=src python3 -m unittest
   discover -b -s tests` 와 겹쳐 「1회만」이 깨진다(`rules/e2e.md` 1절). 겹치는 것을
   또 만드는 것은 ponytail 사다리 1번이다.

**대신 사용자 관점 검증이 하나 있고, 그것을 만들지 않고 실행했다.** 이 가드의
「사용자」는 **문서를 손으로 고치는 사람**이다. 실물 `docs/` 를 임시 디렉터리로 복사해
사람이 낼 법한 **머리 편집 넷**을 넣고, 가드가 **소리를 내는지·어디가 어긋났다고 적는지**를
3절에서 쟀다. 저장소 문서는 한 바이트도 안 고쳤다.

## 1. e2e 21종 — 전부 `rc 0`

| # | 시나리오 | rc | 오늘 실측 |
|---|---|---|---|
| 1 | `crawl_e2e.py` | 0 | 수집 15 · 차단 0 · 최소 간격 1.002s |
| 2 | `indexer_e2e.py` | 0 | 3문서 색인 · 증분 0문서 · 없는 상대경로 rc 1 |
| 3 | `noindex_e2e.py` | 0 | 4페이지 중 2문서 · 뒤늦은 noindex 제거 |
| 4 | `search_api_e2e.py` | 0 | 15문서 · 10+5건 겹침 0 · 400/404/501/503/500 · p95 **2.06ms** |
| 5 | `crawl_delay_e2e.py` | 0 | `Crawl-delay:2` 최소 2.01s · 하한 1.00s |
| 6 | `non_ascii_e2e.py` | 0 | 한글 경로 3행 · 서로게이트 시드 1건 건너뜀 |
| 7 | `hidden_passage_e2e.py` | 0 | 숨은 텍스트 **0/5** · 본문 문단 **5/5** · 오탐 대조군 4종 |
| 8 | `design_check.py` | 0 | 4축 통과 · JS **0 B** · 최저 대비 **4.87:1**(포커스 3.56:1) |
| 9 | `tokenizer_e2e.py` | 0 | 화면(HTML)에서 복합어·어순·굴절·AND · 503→재색인 복구 |
| 10 | `domain_key_e2e.py` | 0 | 같은 서버 간격 2.01×3 · robots 1회 · 대조군 1.01/1.00 |
| 11 | `deadline_e2e.py` | 0 | 대조군 16 / CLI 8페이지 2.2s · **버려진 응답 0건** |
| 12 | `interrupt_e2e.py` | 0 | SIGINT 10.0s rc 130 · DB 0행 · 두 번째 Ctrl-C rc -2 |
| 13 | `indexer_interrupt_e2e.py` | 0 | 재구축 중단이 옛 2,000행 보존 · 재실행 복구 |
| 14 | `crawl_politeness_e2e.py` | 0 | 예외 뒤 2.01s · 대조군 1.00s · 재시도 1.01s |
| 15 | `pagination_ui_e2e.py` | 0 | 다음을 따라가 doc00 · 마지막에 다음 없음 |
| 16 | `retry_interval_e2e.py` | 0 | https 재시도 5.01s · 대조군 1.01s |
| 17 | `url_normalize_e2e.py` | 0 | 표기 10개가 문서 6개로 |
| 18 | `perf_crawl.py` | 0 | [열림] **10.21/s** · [차단] **10.23/s** · [예외] 간격 1.002s |
| 19 | `perf_search.py` | 0 | p50 1.31ms · **p95 8.78ms** (예산 300ms 의 2.9%) |
| 20 | `quality_eval.py` | 0 | ko **20/20** · en **19/20** · 매치 평균 14.0 · 최소 11 · 최대 28 |
| 21 | `passage_eval.py` | 0 | 정확도 **100.0%** · 채택률 99.5% · p95 **1.52ms** |

전부 맨몸으로 하나씩 돌렸다 — 파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율).

## 2. 기준선 대조 — 회귀 **0**

| 축 | 오늘 | 기준 | 직전(계획 61) |
|---|---|---|---|
| 근거 문단 정확도 | **100.0%** | ≥90% | 100.0% |
| `/passages` p95 | **1.52ms** | ≤500ms | 1.51ms |
| `/search` p95 | **8.78ms** | ≤300ms | 8.69ms |
| 품질 ko / en | **20/20 · 19/20** | ≥80% | 20/20 · 19/20 |
| 매치 수 평균/최소/최대 | **14.0 / 11 / 28** | 기록 | 14.0 / 11 / 28 |
| 크롤 [열림] / [차단] | **10.21 / 10.23** | 5.0 / 9.0 | 10.23 / 10.26 |
| 디자인 JS / 최저 대비 | **0 B / 4.87:1** | 50KB / 4.5:1 | 0 B / 4.87:1 |
| 숨은 텍스트 문단 | **0/5** | 0/5 | 0/5 |

**움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도 안 갱신했다.** 계획이 제품
`src/` 를 0줄 고쳤으니 당연한 결과고, 이 표는 그 「당연함」이 실제로 그런지를 잰 것이다.

## 3. 사용자 관점 검증 — 실물 `docs/` 복사본에 사람이 낼 머리 편집 넷

`docs/` 와 `tests/` 를 `mktemp -d` 아래로 복사하고 그 **복사본만** 고쳤다
(`DOCS = Path(__file__).resolve().parent.parent / "docs"` 라 복사본이 자기 옆 문서를 읽는다).
저장소 워킹트리는 매 실행 뒤 `git status --short` 빈손이다.

| # | 편집(사람이 낼 법한 것) | 결과 | 가드가 낸 말 |
|---|---|---|---|
| H0 | 손 안 댐 (대조군) | `Ran 3 · OK` | — |
| H1 | `digest.md` 머리가 리스트 항목에 빨려 들어감 (`- [6] **아카이브 요약**`) | `DocHeadTest failures=1` | `digest.md 의 첫 줄이 H1 이 아니다 — 머리가 본문에 빨려 들어갔다: '- [6] **아카이브 요약**'` |
| H2 | `index.md` 머리가 H1 → H2 (`## 계획 목록`) | `DocHeadTest failures=1` | `index.md 의 첫 줄이 H1 이 아니다 …: '## 계획 목록'` |
| H3 | `history_current.md` 머리 앞에 빈 줄 하나 | `DocHeadTest failures=1` | `history_current.md 의 첫 줄이 H1 이 아니다 …: ''` |
| H4 | `digest.md` 의 `# ` 뒤 공백 누락 (`#아카이브 요약`) | `DocHeadTest failures=1` | `digest.md 의 첫 줄이 H1 이 아니다 …: '#아카이브 요약'` |

**H1 은 이 파일이 존재하게 만든 그 사고의 모양 그대로다** — 파일 머리 주석이 적은
「`digest.md` 의 H1 이 리스트 항목에 빨려 들어간 사고」를 실물 문서 위에서 재현했고,
가드가 **문서 이름과 실제 첫 줄을 함께** 찍었다.

**H0~H4 어디서도 `DocHeadPatternTest` 2건은 안 흔들린다** — 합성 리터럴 위에서 돌기
때문이고, 그것이 두 층을 가른 목적 그대로다. 실물이 흔들리면 `DocHeadTest` 만,
판정이 썩으면 `DocHeadPatternTest` 만 죽는다(4절 M2·M3 이 반대 방향에서 같은 것을 잰다).

### 주석이 실물과 어긋난다 — e2e 가 잡은 것 (severity: low · 주석 전용)

**M3(양성 대조)의 실패 메시지가 실물 세 문서의 첫 줄을 그대로 찍는다**:
`# 아카이브 요약` · **`# 계획 목록`** · **`# 최근 반복 기록`**.
그런데 `DocHeadPatternTest.CAUGHT` 위 주석은 「**실물 세 문서의 첫 줄 그대로**」라 적고
각 리터럴 옆에 `# index.md`·`# history_current.md` 를 달아 두었는데, 그 둘의 리터럴은
`# 계획 색인`·`# 기록 (현재)` 다 — **실물과 다르다**(`head -1` 로 대조 확인).

- **동작에는 영향이 0이다.** `CAUGHT` 는 합성 리터럴이고 판정(`^# \S`)을 재는 데
  제목 문구가 쓰이지 않는다 — H0~H4 다섯 판 전부에서 이 클래스는 안 움직였다.
- **그래도 거짓말이다.** 리뷰 phase 가 후보 ③으로 이 자리를 봤지만
  「제목이 바뀌면 고쳐야 한다로 읽힐 여지」로만 읽고 **이미 어긋나 있다는 사실**은
  못 봤다. 세 프로세스(개발·테스트·리뷰)가 놓친 것을 **실물을 읽는 e2e 가 잡았다** —
  이 phase 가 왜 마지막 관문인지의 실례다.
- **고친 것**: 그 주석을 「실물을 베끼지 않는 **합성 리터럴**이다 · 실물 제목이 바뀌어도
  이 셋은 안 움직인다 · 실물 첫 줄을 재는 것은 `DocHeadTest` 몫이다」로 바꾸고
  오해를 부르던 문서 이름 꼬리주석 셋을 지웠다. **리터럴은 안 건드렸다** — 실물을
  좇게 만들면 계획 61 리뷰가 세운 「두 층을 가른다」가 거꾸로 무너진다.
- 고친 뒤 전수 **맨몸** `Ran 620 tests in 15.767s` · `OK` · rc 0(건수 무변 — 주석뿐).

## 4. 완료 기준 7/7 — 오늘 전부 다시 쟀다

| # | 실측 | 기준 | 판정 |
|---|---|---|---|
| 1 | **M1**(`ITER_LINE` → `re.compile(r"iteration: ([0-9]+)", re.M)`) → `IterationPatternTest.test_status_line_needs_the_whole_line` **하나만** 사망(「줄 중간에 붙은 꼴을 물었다 — `^` 가 죽었다」). 무변이 대조군 **M0** `Ran 620 · 실패 0 · 에러 0` | M1 사망 · 대조군 0건 | 충족 |
| 2 | **M2**(`DOC_HEAD` → `re.compile(r"^")`) → `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` 가 `NOT_CAUGHT` **6/6 subTest 전부** 사망 | M2 가 그 시험을 죽인다 | 충족 |
| 3 | **M3**(`DOC_HEAD` → `^ZZZ`) → `DocHeadTest.test_append_targets_start_with_h1` **실물 3문서 3/3** 사망 (+ `DocHeadPatternTest.test_pattern_catches_document_heads` 3건). 두 층이 각각 자기 것을 잡는다 | M3 가 실물 쪽을 죽인다 | 충족 |
| 4 | **M5**(`ITER_ROW` 를 `^\| 반복[^\|]*\| ([0-9]+) \|` 로 넓힘) → `IterationPatternTest.test_only_the_exact_row_matches` **사망**(`'232' != '0'`, 이웃 행을 물었다) + `IterGapTest.test_missing_metrics_row_is_reported` 사망 | 계획 61 이 세운 감지력이 낮아지지 않았다 | 충족 |
| 5 | `Ran 620 tests in 15.767s` · `OK` · rc 0 (맨몸) · 618 → **620** · `README.md` 러너 줄이 `단위 620건`·`e2e 시나리오 21종` 이고 `ls e2e/*.py` 가 **21개** | 전수 `OK` rc 0 · README 숫자 일치 | 충족 |
| 6 | `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변 | 제품 `src/` 0줄 · 스키마·재색인·새 의존성 0 | 충족 |
| 7 | `status.md` `step` ↔ `index.md` 62번 행이 계획 62 의 매 커밋에서 함께 움직였다 · `StepSyncTest` 가 전수 안에서 초록(세 번째 시험대) | 계획 60 이 세운 `StepSyncTest` 가 이 계획 위에서 실제로 돈다 | 충족 |

**변이 하네스는 메모리 전용이다** — `test_docs` 를 import 한 뒤 모듈 속성
`ITER_LINE`·`DOC_HEAD`·`ITER_ROW` 를 갈아 끼우고 전수를 돌린다. 계획 58 의
`mock.patch.object` 관용구와 같은 자리고, 저장소 파일은 5회 실행 내내 무변경이다.

## 5. 한도 — 지킨 것

- **러너 규율 위반 0회(누적 38 유지).** 전수 2회·e2e 21종·변이 5판·문서 편집 5판을
  전부 맨몸으로 돌렸다. 리다이렉션·파이프·`grep`·`head` 를 러너에 안 붙였다.
- **변이는 저장소 밖에서 걸었다** — 코드 변이는 메모리, 문서 편집은 `mktemp -d` 복사본.
  워킹트리는 이 phase 내내 `git status --short` 빈손이었다(6절의 주석 수정 전까지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0 · `docs/specs/` 읽기만.
- 원격 `loop/passage-cost-band` 위에 오늘 커밋을 쌓는다. `origin/main`(`d1fe3e9`) 무접촉 ·
  PR 0(만들지도 조회하지도 않았다) · `--force`·`--amend`·`rebase` 0회. 병합은 사람 몫이다.
- 도구 산출물 없음 — Playwright 같은 브라우저 도구를 쓰지 않는 프로젝트라
  `test-results/` 에 해당하는 경로가 없다. 위 표의 숫자가 실행 출력 전부다.

## 6. 이 phase 가 고친 것

`tests/test_docs.py` 의 `DocHeadPatternTest.CAUGHT` **주석 3줄**(+ 꼬리주석 3개 삭제).
계획의 「건드릴 파일」 안이고 **판정·리터럴·건수 무변**이라 개발 phase 로 돌려보내지
않았다(`rules/e2e.md` 8절은 **실패**했을 때 스텝으로 되돌리라고 적는다 — 21종·전수
어디도 안 빨개졌다). 근거와 대안 기각 사유는 3절 아래 절에 있다.
