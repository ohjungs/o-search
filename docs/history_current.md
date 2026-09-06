# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

**회전 명부는 `digest.md` 의 `## 완료` 절 «아카이브 명부» 줄이 정본이다.**
여기 있던 스물한 회전의 서술(233줄)은 그 줄과 내용이 겹쳤고, 검사가 강제하는 명부도
그쪽 하나뿐이라(`tests/test_docs.py` 의 `ArchiveIndexTest`) **개발 9(반복 269)가 이
자리에서 지웠다** — 회전으로는 300줄 상한을 못 맞추던 세 반복(309 → 372 → 418줄)의
원인이 이 명부였다. **지운 것은 머리말이지 반복 기록이 아니다** — 항목은 여전히
append 전용이고 수정·삭제 금지다. 각 회전의 사유는 `digest.md` 의 같은 줄에, 원문은
`history_<NNN>.md` 에 그대로 있다.

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
