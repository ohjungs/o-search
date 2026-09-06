# 반복 기록 064 — 반복 356~365 (계획 61 `iter-gap-cover` · 계획 62 `head-anchor-cover`)

## 2026-09-06 05:00 | iter-gap-cover | 계획 0/1 | 시도1

- 한 일: 계획 60 `index-step-sync` 마감 + 계획 61 `iter-gap-cover` 등재. 만진 것은
  `docs/` 뿐 — `src/`·`tests/`·`e2e/`·`README.md`·`docs/specs/`·`data/crawl.db` 무접촉.
  **앞 에이전트가 같은 스텝에서 변경 0건으로 죽어 시도1**(3회에서 정지). 탐색·마감·등재를
  쪼개 커밋 둘로 냈다.
- 마감: `plan_index-step-sync.md`→`plan_history_046.md` · `design_…`→`design_history_046.md`
  (`git mv` · 내용 무변경) · `index.md` 60번 `진행`→`완료`(완료 기준 6/6 · 새 e2e 0 ·
  21종 rc 0 · 회귀 0 · `src/` 0줄) · `digest ## 완료` 한 줄.
- 마감: `digest ## 반복 실패` 의 「스텝 커밋에서 `index.md`·`metrics.md` 숫자를 안 올린다」
  (5회)에 취소선 — 규율이 아니라 `StepSyncTest` 가 붙든다.
- 집안일: `digest.md` 201줄 → `rules/docs.md` 3절대로 **완료 항목부터** 하나 삭제(계획 53,
  원본은 `index.md` 53번·`plan_history_040.md`·`docs/e2e/passage-db-state/result.md`).
  200줄 · 명부/보류/재발/관찰 무변. 이 파일은 249→279줄로 상한 300 미달이라 회전 없음
  (다음 회전 번호 `history_063.md`).
- 탐색: **1~5순위 0건** — 전수 `Ran 614 · OK · rc 0`(맨몸) · 린터 설정 0 ·
  `TODO`/`FIXME` 1건은 `tests/test_indexer.py:759` 파서 입력 문자열 안 · `candidates.md`
  없음 · `## 보류` 0 · 이슈 0. **6순위에서 여는 조건이 온 항목 하나** — `digest [6]`
  「`IterationSyncTest` 의 «판정» 도 실물 문서 위에서만 돈다」, 조건이 「반복 축을 손대는
  날」이었고 계획 60 이 닫히며 미룬 이유(직교 편집)가 사라졌다. 나머지 6순위는 그대로 막힘.
- 탐침: 기록된 답이 절반 틀렸다(`digest [7]` 12번째 적용). 메모리 변이로 재니 생존이
  하나가 아니라 **넷**(M1 자기비교 · M2·M3 가드 삭제 · M4 판정 통째 삭제, 전부
  `Ran 614 · 죽은 단언 0`). M5 `ITER_ROW` 넓힘은 `IterationPatternTest` 가 죽인다.
  점수 6→**7**. 양성 대조를 먼저 걸어 패치 대상이 `tests/test_docs.py` 임을 확인(`[8]`).
- 결정: **설계 생략 — `rules/design.md` 1절 트리거 0**(새 모듈 0 · 파일 1개 · revert 하나).
  대안 셋은 `design_history_046.md` 안 D 와 계획서 5·6절이 이미 갈라 놨다.
- 다음: **개발 1/1** — `step_gap` 옆에 `iter_gap(status_text, metrics_text)` 를 세우고
  `IterationSyncTest` 를 세 줄로 줄인 뒤 `IterGapTest` 로 갈래 넷을 밟는다. 완료 기준은
  `docs/plan_iter-gap-cover.md` 4절 여섯 개. 러너 규율 위반 **0회**(누적 38 유지).

## 2026-09-06 06:10 | iter-gap-cover | 개발 1/1 | 시도0

- 한 일: `tests/test_docs.py` 에 `iter_gap(status_text, metrics_text)` 를 `step_gap`
  **바로 위**에 세웠다(인자 순서·반환 계약·독스트링 모양 전부 `step_gap` 과 같은 꼴).
  `IterationSyncTest.test_metrics_and_status_agree` 는 두 파일을 읽어
  `assertIsNone(gap, gap)` 하는 **세 줄**로 줄었고, 갈래 넷을 합성 문자열로 밟는
  `IterGapTest` 4건을 `IterationPatternTest` 옆자리에 세웠다(초록 · 대조 불일치 ·
  `metrics` 행 없음 · `status` 줄 없음). 단언은 한 줄도 안 낮췄다.
- TDD 0절: **RED 를 눈으로 먼저 봤다** — 함수 없이 테스트만 넣고 전수를 돌려
  `NameError: name 'iter_gap' is not defined` ×4 와 `(614, 21) != (618, 21)` 를 본 뒤 구현.
- 결과: 전수 `Ran 618 tests in 15.891s` · `OK` · rc 0(맨몸). 변이 재측 **M1~M4 4/4 사망**
  이고 **각 변이가 의도한 단언 하나만** 죽인다(M1 자기비교 → `test_iteration_mismatch_is_reported`
  · M2 → `test_missing_metrics_row_is_reported` · M3 → `test_missing_status_line_is_reported`).
  양성 대조 M4(판정 통째 삭제)는 **3건**을 죽여 계획서 기준 「셋 이상」을 넘긴다. 대조군은
  `죽은 단언 0`. 만진 파일은 `tests/test_docs.py`·`README.md` 둘뿐 —
  `src/`·`e2e/`·`docs/specs/`·`data/crawl.db` diff 빈손.
- 다음: **테스트 1/1** — 새 `iter_gap`·`IterGapTest` 위에서 갭을 탐색한다. 완료 기준 6개
  중 1~5 는 오늘 충족, 6(`status`↔`index` 스텝 축)은 이 커밋이 함께 `1/1` 로 올린다.
  러너 규율 위반 **0회**(누적 38 유지). 파일 **300줄로 상한에 닿았다** — 넘지는 않아
  이번엔 회전 없지만 **다음 append 가 넘긴다**(다음 회전 번호 `history_063.md`).

## 2026-09-06 10:00 | iter-gap-cover | 테스트 1/1 | 시도2

- 한 일: 전수와 변이 재측만 했다. 저장소 파일은 **한 줄도 안 고쳤고**(`src/`·`tests/`·
  `e2e/`·`README.md`·`docs/specs/`·`data/crawl.db` diff 빈손) 변이는 스크래치패드
  하네스가 `mock.patch` 로만 걸었다. 전수 `Ran 618 · OK · rc 0` · 대조군 죽은 단언 **0**.
- 결과: **M1~M5 사망** — M1 자기비교 1건(`IterGapTest.test_iteration_mismatch_is_reported`) ·
  M2 `metrics` 가드 삭제 1건 · M3 `status` 가드 삭제 1건 · M4 판정 통째 삭제(양성 대조)
  **3건** · M5 `ITER_ROW` 넓힘 **2건**(`IterGapTest` + `IterationPatternTest`). 계획 61 이
  세운 갈래가 실제로 갈렸다는 것을 각 변이가 **의도한 이름만** 죽이는 것으로 확인했다.
- 결과: **갭 둘이 살아남았다 — 둘 다 「판정이 실물 문서 위에서만 돈다」의 형제다.**
  ① **M6 `ITER_LINE` 의 `^`·`$` 제거 — 죽은 단언 0.** 앵커를 붙드는 줄로 보이던
  `IterationPatternTest` 의 `night_iterations` 단언은 사실 **복수형 `s` 가 막는 것**이라
  앵커가 없어도 초록이다. ② **M7 `DocHeadTest` 판정 넓힘(`^# \S` → `^`) — 죽은 단언 0**
  (두 번 재서 두 번 다 0). 실물 세 문서가 늘 H1 로 시작해 판정 무력화가 조용히 산다.
  둘 다 **8점 미만이라 이번 스텝에서 안 고치고** `digest` 의 테스트 phase 갭 절에 남겼다
  (`rules/test.md` 3절).
- 집안일: `history_current.md` 가 상한을 넘어 **`history_063.md` 로 회전**(반복 350~355 ·
  220줄 이관 · 남은 80줄 · 유실·중복 0). `digest` 아카이브 명부에 이름을 더하고 계획 60
  완료 줄에 회전 기록을 적었다. 200줄 상한을 지키려 **가장 오래된 완료 항목(계획 54)을
  지웠다**(`rules/docs.md` 3절 · 원본은 `plan_history_040.md`).
- 다음: **리뷰 1/1.** 완료 기준 1~5 는 개발이, 6(`status`↔`index` 스텝 축)은 `index.md`
  61번 행이 이미 `1/1` 이라 `StepSyncTest` 가 전수 안에서 초록으로 확인한다.
  **앞 시도 둘이 600초 무진전으로 죽어 시도2** — 죽은 시도가 남긴 것은 회전 diff 뿐이라
  이 반복이 측정을 다시 재고 기록을 마감했다. 러너 규율 위반 **0회**(누적 38 유지).

## 2026-09-06 11:00 | iter-gap-cover | 리뷰 1/1 | 시도0

- 한 일: `git diff 6f911e3..HEAD -- tests/test_docs.py README.md` 를 백지 → 대조 두 패스로
  봤다. 후보 3건 중 **보고 1 · 자동 수정 1 · 승인 필요 0** 이라 개발 phase 로 반려하지 않는다.
  오늘 다시 잰 전수 `Ran 618 · OK · rc 0`(맨몸) · 제품 축 `src/`·`e2e/`·`docs/specs/`·`data/`
  diff **빈손** · `data/crawl.db` sha256 `85c96744…` 무변.
- 결과: 버린 둘은 ① `IterGapTest` 의 `assertIn("metrics.md"/"status.md", gap)` 이 「행 없음」과
  「불일치」를 못 가르는 것 — 두 메시지에 다 든 문자열이라 그렇지만 M2·M3 은 `AttributeError`
  로 죽어 **감지력 손실 0**(`severity.md` 4절 「충분히 덮는 단언을 더 조일 수 있다」) ②
  `night_iterations` 미끼가 이빨 없는 것(M6) — **기보류 중복**, 테스트 phase 가 `digest [6]①`
  로 이미 등재했다. 고친 하나는 **[R61-1] `status.md` 의 「`history_current.md` 는 80줄」이
  실제 105줄과 어긋난 것** — 회전 판단이 읽는 숫자라 이번 `status` 덮어쓰기에서 105 로 고쳤다.
- 결과: **`step_gap` 과 `iter_gap` 을 공통 헬퍼로 합치지 않는다.** 겹치는 몸통이 8줄뿐인 것보다
  큰 이유는 **합치면 변이 하나가 두 축의 테스트를 함께 죽여 갈래 귀속이 무너지는 것**이다 —
  두 함수를 뺀 목적 자체를 잃는다. 인자 순서 `(status, metrics)` 를 뒤집는 사고는 조용히
  통과가 아니라 「metrics.md 에서 행을 못 찾았다」로 시끄럽게 실패해 눈먼 자리가 아니다.
- 집안일: **반복 358 커밋 `22a2290` 이 원격에 없었다**(`ls-remote` 가 `9cf9b92`=357 을
  가리켰다). 이번 스텝 커밋과 함께 정상 푸시했다 — `--force`·`--amend`·`rebase` 없음.
- 다음: **e2e 1/1.** 제품 무변경이라 의존성 축은 빈손이고, 재는 것은 문서 가드 셋
  (`IterationSyncTest`·`StepSyncTest`·`IterGapTest`)이 실물 `docs/` 위에서 초록인가와
  완료 기준 6개의 최종 확인이다. 러너 규율 위반 **0회**(누적 38 유지) · 회전 없음(127줄).

## 2026-09-06 | plan_iter-gap-cover | e2e 1/1 | 시도0
- 한 일: e2e **21종 전수 rc 0**(맨몸)과 완료 기준 6개를 다시 쟀다. 메모리 변이 하네스로
  M1~M4 **4/4 사망**(각각 의도한 이름 하나 · 무변이 대조군 `Ran 618 · 죽은 것 0건`) · 양성
  대조 M4 가 `IterGapTest` **3건** · M5 는 `IterationPatternTest` 가 여전히 죽인다.
- 결과: **면제를 「해당 없음」으로 넘기지 않고 근거 셋으로 쟀다** — `src/`·`e2e/`·`specs/`·
  `data/` diff 빈손 · `iter_gap` 은 `tests/` 안이고 `src/` 에 `tests` import 0건이라
  `rules/e2e.md` 3절의 네 수단 어디에도 걸 곳이 없다 · 새로 만들면 전수와 겹쳐 「1회만」이
  깨진다. **대신 진짜 사용자 관점 검증을 하나 실행했다** — 이 가드의 사용자는 문서를 손으로
  고치는 사람이라 실물 `docs/` 를 `mktemp -d` 로 복사해 편집 넷(D1·D2 반복 번호 어긋내기 ·
  D3·D4 행·줄 이름 지우기)을 넣으니 **4/4 가 `IterationSyncTest` 를 빨갛게 만들고 어긋난
  자리를 문장으로 적었다**(D1·D2 는 방향이 반대). 그 넷 어디서도 `IterGapTest` 는 안
  흔들린다 — 합성 문자열 위에서 돌기 때문이고, 두 층을 가른 목적 그대로다.
- 집안일: 기준선 회귀 **0**(정확도 100.0% · `/passages` p95 1.51ms · `perf_search` p95
  8.69ms · ko 20/20 · en 19/20 · 크롤 10.23/10.26 · JS 0 B · 4.87:1 · 숨은 텍스트 0/5)이라
  `project.md` 무갱신. `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 러너 규율 위반
  **0회**(누적 38 유지) · 변이는 전부 저장소 밖(코드는 메모리 · 문서는 임시 복사본).
- 다음: **계획 61 DONE.** 아카이브 `plan_history_047.md` · `index.md` 61번 완료 ·
  `digest` 완료 등재 + 닫힌 후보 항목 삭제. 다음 반복은 계획 phase 다.
## 2026-09-06 12:00 | head-anchor-cover | 계획 0/1 | 시도0
- 한 일: 계획 61 이 반복 360 에 DONE 으로 닫혀 활성 계획이 0 이라 **탐색 → 계획 62 등재**를
  돌았다. `discover.md` 1절 1~5순위를 실측으로 훑고(전수 `Ran 618 tests in 15.892s` `OK`
  rc 0 맨몸 · 린터/타입체커 설정 0개 · `TODO`/`FIXME`/`HACK` 이 `src`·`tests`·`e2e`·
  `scripts` 에 1건인데 `tests/test_indexer.py:759` 의 **파서 입력 문자열 안** ·
  `docs/candidates.md` 없음 · `docs/patches/` 없음 · `digest ## 보류` 절이 비어 0건 ·
  `gh issue list --state open` 0건 rc 0) **전부 0건**이라 6순위로 내려가
  `digest ## 다음 계획 후보 (테스트 phase 갭)` 의 `[6]` 을 열었다. 계획서
  `docs/plan_head-anchor-cover.md` · `index.md` 62번 행 등재.
- 결과: **착수 탐침이 기록된 답을 다시 쟀고 이번엔 항목이 맞았다**(`digest [7]` 열세 번째
  적용 · 저장소 파일 무변경 · 하네스는 저장소 밖 · `git status --short` 빈손).
  **M0** 무변이 `Ran 618 · 죽은 단언 0` · **M1** `ITER_LINE` 앵커 제거 → **생존**(죽은
  단언 0) · **M2** `DocHeadTest` 판정 `^# \S` → `^` → **생존**(죽은 단언 0) ·
  **M3 양성 대조** 같은 판정을 `^ZZZ` 로 → **실패 3**(subTest 셋)이라 패치가 그 메서드에
  실제로 꽂혔음이 증명됐다. `night_iterations: 90` 단언이 앵커를 재는 줄로 보이지만
  실제로 막는 것은 **복수형 `s`** 라는 항목의 진단도 정규식 단독 실행으로 확인했다 —
  `"x iteration: 1"`·`"iteration: 1x"` 는 앵커가 있으면 매치 없음, M1 이면 둘 다 매치다.
- 결과: **처방은 순수 함수가 아니라 상수+리터럴이다.** `step_gap`·`iter_gap` 관용구는
  «두 문서를 대조하는 판정» 을 뺄 때 쓴 것이고, 여기 판정은 문서 하나의 첫 줄에 정규식
  하나를 대는 것이라 뺄 몸통이 없다. 축이 정규식이면 저장소의 선례는 `CITATION` +
  `CitationPatternTest`(`CAUGHT`/`NOT_CAUGHT`) 쪽이다 — 그래서 **설계 생략(트리거 0)**,
  저울질할 대안이 남지 않았다.
- 집안일: `git ls-remote origin loop/passage-cost-band` = `d763317c9d2f…` 로 반복 360
  커밋이 원격에 정상 반영돼 있다. `origin/main` 은 계획 56(`d1fe3e9`)까지고 PR 0건 —
  만들지도 조회하지도 않았다. `docs/digest.md` 는 실측 **200줄**(상한 200 정각)이라
  후보 `[6]` 항목에 **줄을 더하지 않고 같은 줄 끝에** 연 사실만 이어 붙였다.
  러너 규율 위반 **0회**(누적 38 유지) · 회전 없음(146 → 이 항목 뒤 177줄, 상한 300).
- 다음: **개발 1/1.** `tests/test_docs.py` 에서 ① `IterationPatternTest` 에 리터럴 두 줄
  (`"x iteration: 1"`·`"iteration: 1x"`)을 더하고 ② `r"^# \S"` 를 모듈 상수 `DOC_HEAD` 로
  올려 `DocHeadPatternTest`(CAUGHT 3 · NOT_CAUGHT 6)를 세운다. `rules/dev.md` 0절대로
  **RED 를 눈으로 먼저 본다**. 건드릴 파일은 `tests/test_docs.py`·`README.md` 둘뿐이다.
## 2026-09-06 13:00 | head-anchor-cover | 개발 1/1 | 시도0
- 한 일: `tests/test_docs.py` 에 모듈 상수 `DOC_HEAD`(`ITER_LINE` 아래)와
  `DocHeadPatternTest`(CAUGHT 3 · NOT_CAUGHT 6)를 `CitationPatternTest` 관용구 그대로 세우고,
  `DocHeadTest` 는 `assertRegex(first, DOC_HEAD, …)` 로 바꿔 실물 셋을 재는 자리로 남겼다.
  `IterationPatternTest` 에는 앵커를 실제로 재는 리터럴 두 줄(`"x iteration: 1"`·
  `"iteration: 1x"`)과 「기존 단언이 막던 것은 앵커가 아니라 복수형 `s`」라는 주석을 더했다.
  만진 파일은 그 파일과 `README.md`(단위 건수 줄) **둘뿐** — 계획서 「건드릴 파일」과 같다.
- TDD 0절: **RED 를 눈으로 먼저 봤다** — 상수 없이 새 클래스와 `assertRegex(first, DOC_HEAD, …)`
  만 넣고 전수를 돌려 `NameError: name 'DOC_HEAD' is not defined` **×12**(새 클래스 9 ·
  `DocHeadTest` subTest 3)와 `test_readme` 의 `(618, 21) != (620, 21)` 을 본 뒤 구현했다.
- 결과: 전수 `Ran 620 tests in 15.792s` · `OK` · rc 0(맨몸) · 대조군 죽은 단언 **0**.
  변이 재측 **M1 사망 1**(`IterationPatternTest.test_status_line_needs_the_whole_line`) ·
  **M2(`DOC_HEAD`→`^`) 사망 6**(전부 `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` 의
  subTest) · **M3 양성 대조(`^ZZZ`) 사망 6**(`DocHeadTest` 실물 3 + 패턴 CAUGHT 3) ·
  **M5(`ITER_ROW` 넓힘) 여전히 사망 2**. **M2 와 M3 이 서로 다른 이름을 죽여** 두 층의 귀속이
  확인됐다 — 넓히는 변이는 합성 갈래가, 죽이는 변이는 실물 검사가 잡는다.
- 결과: 범위 무접촉 — `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
  `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 변이는 전부 저장소 밖(스크래치패드 하네스가
  `mock.patch.object` 로 모듈 속성만 갈았다) · 러너 규율 위반 **0회**(누적 38 유지).
- 다음: **테스트 1/1.** 완료 기준 7개를 오늘 전부 충족했다(7 은 `index.md` 62번 행을 `1/1` 로
  함께 올려 `StepSyncTest` 가 확인). 다음 갭 후보는 계획서 5절이 남긴
  `ITER_ROW`·`STEP_ROW`·`STEP_LINE`·`PLAN_SLUG` 의 앵커 — **오늘 재지 않았다.**
  `digest.md` 는 200줄 정각이라 한 줄도 안 더했다 · 회전 없음(201줄, 상한 300).
## 2026-09-06 14:00 | head-anchor-cover | 테스트 1/1 | 시도0
- 한 일: 새 테스트를 쓰는 자리가 아니라 **빠뜨린 것을 찾고 전체를 돌리는** 자리다
  (`rules/test.md` 1·3·6절). ① 완료 기준 1~4 의 변이를 개발 phase 와 **다른 프로세스에서**
  다시 걸었고 ② 계획서 5절이 남긴 네 정규식의 앵커를 처음으로 쟀다. 저장소는 한 바이트도
  안 고쳤다 — 스크래치패드 하네스가 `mock.patch.object` 로 모듈 속성만 갈았다.
- 결과: **완료 기준 재측 4/4 그대로다** — 대조군 `Ran 620` 죽은 단언 **0** ·
  M1(`ITER_LINE` 앵커 제거) **사망 1** `IterationPatternTest.test_status_line_needs_the_whole_line` ·
  M2(`DOC_HEAD`→`^`) **사망 1** `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` ·
  M3 양성 대조(`^ZZZ`) **사망 2** `DocHeadPatternTest.test_pattern_catches_document_heads`
  + `DocHeadTest.test_append_targets_start_with_h1` · M5(`ITER_ROW` 넓힘) **사망 2**.
  `\S` 를 지우는 변이 둘(`^# `·`^#`)도 새로 걸어 봤고 **둘 다 사망 1**(같은 이름)이라
  `NOT_CAUGHT` 의 `"#제목"`·`"# "` 이 실제로 그 글자를 붙들고 있다.
- 결과: **갭 하나 — 계획 62 가 닫은 구멍의 형제가 정규식 넷에 그대로 있다. 점수 [6].**
  `STEP_LINE`(`^`·`$`) · `PLAN_SLUG`(`^`) · `ITER_ROW`(`^`) · `STEP_ROW`(`^`) 를 지우는 변이가
  **4/4 전수 620건에서 생존**했다(`ARCHIVE` 의 `^…$` 도 생존하나 `.match()` 라 `^` 가 잉여).
  배선 의심을 먼저 껐다(`digest [6]`) — 같은 상수를 `^ZZZ` 로 죽이면 각각 **6·6·4·1건**이
  죽는다. `StepPatternTest` 의 `STEP_LINE.search("step: 1")` 이 막던 것도 앵커가 아니라
  **`N/M` 모양**이라 `ITER_LINE` 의 `night_iterations: 90` 과 같은 착시였다.
- 판정: **8 미만이라 이 스텝에서 닫지 않는다**(`rules/test.md` 4절). 앵커는 오늘 넷 다 참이고
  구멍은 「앞으로 넓히는 편집이 조용히 산다」는 잠복이며, 계획서 5절이 **미리 「있으면 digest
  후보로 남긴다」로 선언한 범위 밖**이다. 여는 조건은 「그 정규식 넷 중 하나를 손대는 날」.
- 결과: 전수 **맨몸** `Ran 620 tests in 15.889s` · `OK` · **rc 0** ·
  범위 무접촉(`git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
  `data/crawl.db` sha256 `85c96744…5bda18` 무변) · 러너 규율 위반 **0회**(누적 38 유지).
- 다음: **리뷰 1/1.** `digest.md` 는 200줄 정각이었으므로 후보 한 줄을 더하면서 룰대로
  **가장 오래된 완료 항목 하나**(계획 55 `db-state-invariant`)를 지워 200줄을 지켰다 —
  원본은 `plan_history_041.md` 와 아카이브 명부에 그대로 있다. `history_current.md`
  회전 없음(228줄, 상한 300).

## 2026-09-06 13:00 | head-anchor-cover | 리뷰 1/1 | 시도0

- 한 일: `git diff e774608..HEAD -- tests/test_docs.py README.md`(+51/−3)를 백지 → 대조
  두 패스로 봤다(짧은 경로라 세션을 안 나눴다). 후보 3건이 **전부 80점 미만**이라
  보고 0 · 자동 수정 0 · 승인 필요 0 — 개발 phase 로 반려하지 않는다.
- 재측: 계획서 7절의 위험(「`NOT_CAUGHT` 이 판정을 바꾼다」)을 세 번째 프로세스에서 다시
  쟀다 — `^# \S` 가 `NOT_CAUGHT` **6/6 거절** · `CAUGHT` **3/3 인정**이고, M2(`^`)면 여섯이
  **6/6 통과**해 죽는다. 새 앵커 리터럴 둘도 앵커 없는 `ITER_LINE` 에서 둘 다 매치돼 M1 을
  죽인다. 개발·테스트가 적은 수치가 그대로 재현됐다(`digest [7]` 열네 번째 적용).
- 버린 후보: ① `DOC_HEAD` 배치(각 주석이 자기 상수 위라 오해 없음) ② `re.M` 부재를 붙드는
  단언 없음 — **등가 변이**라 갭이 아니다(입력이 한 줄) ③ `CAUGHT` 옆 문서 이름 주석이
  「제목이 바뀌면 고쳐야 한다」로 읽힐 여지(합성 리터럴이라 실물 제목과 무관).
- 결과: 전수 **맨몸** `Ran 620 tests in 15.933s` · `OK` · **rc 0** · 범위 무접촉(`src/`·`e2e/`·
  `docs/specs/`·`data/` diff **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변) ·
  러너 규율 위반 **0회**(누적 38 유지).
- 다음: **e2e 1/1.** `digest` 는 등재할 후보가 없어 200줄 정각 무변 · `history_current.md`
  회전 없음(246줄, 상한 300).

## 2026-09-06 14:00 | head-anchor-cover | e2e 1/1 | 시도0

- 한 일: e2e 21종을 **하나씩 맨몸으로** 돌려 **rc 0 · 21/21**, 전수는 `Ran 620 tests in
  15.767s` · `OK` · rc 0. 결과는 `docs/e2e/head-anchor-cover/result.md`. 기준선 8축 전부
  회귀 0 이라 `docs/project.md` 는 한 줄도 안 갱신했다.
- 면제: 새 e2e 파일 0개를 「해당 없음」으로 안 넘기고 근거 셋으로 쟀다(`rules/e2e.md` 3절) —
  프로세스 밖 변화 0 · `DOC_HEAD` 가 `tests/` 안이라 네 수단에 걸 곳이 없다(`src/` 에
  `tests` import **0건**) · 새로 만들면 전수와 겹쳐 「1회만」이 깨진다.
- 대신 실물 `docs/` 를 `mktemp -d` 로 복사해 사람이 낼 **머리 편집 넷**을 넣으니 **4/4 가
  빨개졌다**(리스트 항목에 빨려 든 H1 · H1→H2 · 머리 앞 빈 줄 · `# ` 뒤 공백 누락).
  다섯 판 어디서도 `DocHeadPatternTest` 는 안 흔들린다 — 두 층을 가른 목적 그대로다.
- 완료 기준 **7/7** 재측: M0 대조군 620·0 · M1 → `test_status_line_needs_the_whole_line`
  하나만 · M2 → `test_pattern_leaves_non_h1_heads` 6/6 subTest · M3 → 실물 `DocHeadTest`
  3/3 · M5 → 계획 61 이 세운 `test_only_the_exact_row_matches` 여전히 사망.
- **e2e 가 세 프로세스가 놓친 것을 하나 잡았다** — M3 의 실패 메시지가 실물 첫 줄
  (`# 계획 목록`·`# 최근 반복 기록`)을 찍어서 `CAUGHT` 위 주석의 「실물 세 문서의 첫 줄
  그대로」가 **거짓**임이 드러났다(리터럴은 `# 계획 색인`·`# 기록 (현재)`). 동작 영향 0
  (합성 리터럴)이라 **주석만** 고치고 **리터럴은 안 건드렸다** — 실물을 좇게 만들면
  계획 61 리뷰가 세운 「두 층을 가른다」가 거꾸로 무너진다. 계획 범위 안이고 판정·건수가
  무변이라 개발 phase 로 안 돌렸다(`rules/e2e.md` 8절은 **실패** 때 되돌리라고 적는다).
  교훈: **양성 대조는 배선만 증명하는 게 아니라 실물을 화면에 찍어 준다 — 그 출력을 읽어라.**
- 결과: **계획 62 DONE** — `plan_history_048.md` 아카이브 · `index.md` 62번 행 완료 ·
  `digest` 완료 등재 + 이 계획이 닫은 후보 한 줄 삭제로 **200줄 정각** 유지 ·
  범위 무접촉(`data/crawl.db` sha256 `85c96744…5bda18` 무변) · 러너 규율 위반 **0회**(누적 38).
- 다음: **활성 계획 0 — 계획 phase.** `digest` 의 `[6]`「앵커 구멍의 형제가 정규식 넷에
  그대로 있다」가 계획 62 와 같은 여는 조건으로 남아 있다. `history_current.md` 회전
  없음(상한 300).
