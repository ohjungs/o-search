# 계획 62 — `head-anchor-cover`

`tests/test_docs.py` 의 **문서 가드 둘이 자기 판정을 못 잰다.** `ITER_LINE` 의 앵커
(`^`·`$`)를 지워도, `DocHeadTest` 의 판정 `^# \S` 를 `^` 로 넓혀도 전수 618건이
**죽은 단언 0** 으로 초록이다. 둘 다 실물 문서가 늘 「맞는 모양」이라 판정을
무력화해도 아무 데도 안 걸리는, 이 저장소가 이미 세 번 닫은 그 구멍이다.

- **근거**: `docs/digest.md` `## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 의 `[6]`
  「`iter_gap` 을 뺀 뒤에도 「판정이 실물 문서 위에서만 도는」 자리가 둘 남았다 —
  변이 둘이 전수 618건에서 살아남는다」(2026-09-06 계획 61 테스트 phase 가 등재하며
  **직교 편집이라 미뤘다**). 그 항목의 **여는 조건은 「그 검사를 손대는 날」**이고,
  이 계획이 곧 그날이다 — 계획 61 이 같은 파일의 같은 축(`ITER_LINE` 을 읽는
  `iter_gap`)을 반복 360 에서 DONE 으로 닫았으므로 미룬 이유가 오늘 없어졌다.
  계획 60 → 61 이 걸어온 것과 **글자 그대로 같은 계승**이다.
- **1~5순위 실측 0건** (2026-09-06 반복 361):
  전수 `Ran 618 tests in 15.892s` · `OK` · rc 0 **맨몸** ·
  린터/타입체커 설정 파일 0개(`project.md` 「린트/타입체크: 없음」) ·
  `TODO`/`FIXME`/`HACK` 이 `src/`·`tests/`·`e2e/`·`scripts/` 에 **1건**인데 그것은
  `tests/test_indexer.py:759` 의 **파서 입력 문자열 안**(`"<p>김치찌개 <!-- TODO: …"`)
  이라 코드 부채가 아니다 · `docs/candidates.md` 없음 · `docs/patches/` 없음 ·
  `digest ## 보류 (승인 대기)` **0건**(절이 비어 있다) · `gh issue list --state open`
  **0건 rc 0** · 활성 계획 0.
- **6순위의 더 높은 점수는 전부 「여는 조건 미도래」다** — `[9]` `/search` 몫 ·
  `[8]` 숨은 텍스트 뒷절반 · `[8]` 토크나이저는 실물 코퍼스/재색인이 필요하고,
  `[7]` macOS pycache 는 처방이 이미 들어갔고, `[7]` 재파싱 몫 배정과 `[7]` 키셋
  페이지네이션은 사람 결정이며, `[6]` 캡 하향 · `[6]` `_IMPLIED_END` 표 ·
  `[6]` `extract_blocks` 이름표는 각각 「캡을 내리는 날」·「표를 손으로 고치는 날」·
  「실물 코퍼스」다. **여는 조건이 실제로 온 항목은 `[6]` 하나다.**
- **기점**: `loop/passage-cost-band` 의 계획 61 마감 커밋(`d763317`, 원격 동일 —
  `git ls-remote origin loop/passage-cost-band` = `d763317c9d2f…`). 고칠 파일
  `tests/test_docs.py` 는 계획 60·61 이 세운 `step_gap`·`iter_gap` 관용구 위에 서 있고
  그것들이 `origin/main`(`d1fe3e9`)에는 0건이라 **`main` 에서 새로 따면 안 된다.**
  브랜치는 계획 57·58·59·60·61 과 같이 쌓아 둔 채로 간다.
- **원격**: `origin/main` 은 계획 56(`d1fe3e9`)까지고 열린 PR 은 0건이다. 병합은 사람 몫.

## 1. 문제 · 목표 · 기대 결과

**문제.** 두 자리다.

① **`ITER_LINE`(`tests/test_docs.py:48`)의 앵커를 붙드는 단언이 0개다.**
`IterationPatternTest.test_…`(`tests/test_docs.py:407`)의
`assertIsNone(ITER_LINE.search("night_iterations: 90"))` 은 앵커를 재는 줄처럼
보이지만 실제로 막는 것은 **복수형 `s`**(`iterations: ` ≠ `iteration: `)다 —
앵커를 지워도 그 단언은 그대로 초록이다. 앵커가 진짜 막는 것(줄 중간에 붙은 꼴 ·
꼬리가 붙은 꼴)을 밟는 단언은 **하나도 없다.**

② **`DocHeadTest.test_append_targets_start_with_h1`(`tests/test_docs.py:142`)의
판정 `^# \S` 를 `^` 로 넓혀도 죽는 것이 0건이다.** 실물 세 문서
(`APPEND_TARGETS` = `digest.md`·`index.md`·`history_current.md`)가 늘 H1 으로
시작해서, 판정을 통째로 무력화해도 조용히 산다. **이 파일이 존재하는 이유가
`digest.md` 의 H1 이 리스트 항목에 빨려 들어간 사고**(파일 머리 주석)인데,
그 사고를 잡는 판정이 지금 자기를 못 잰다.

**목표.** 두 판정을 **정규식 상수 + 리터럴 대조**로 못박는다. 이 저장소가
정규식 축에서 이미 두 번 쓴 관용구 그대로다 — `CITATION` + `CitationPatternTest`
(`CAUGHT`/`NOT_CAUGHT` 튜플, `tests/test_docs.py:155`) · `ITER_ROW` +
`IterationPatternTest.test_only_the_exact_row_matches`.

- ①은 `IterationPatternTest` 에 **리터럴 두 줄**을 더한다:
  `assertIsNone(ITER_LINE.search("x iteration: 1"))`(`^` 가 막는다) ·
  `assertIsNone(ITER_LINE.search("iteration: 1x"))`(`$` 가 막는다).
- ②는 `DocHeadTest` 의 본문에 박힌 `r"^# \S"` 를 **모듈 상수 `DOC_HEAD`** 로 올리고
  (`ITER_LINE` 옆), `CAUGHT`/`NOT_CAUGHT` 를 도는 `DocHeadPatternTest` 를 세운다.
  `DocHeadTest` 는 실물 세 문서를 `DOC_HEAD` 로 재는 자리로 남는다 — 두 층을 가른
  목적이 `step_gap`·`iter_gap` 과 같다(실물은 실물이, 갈래는 합성 리터럴이).

**왜 순수 함수(`head_gap`)가 아니라 상수인가.** `step_gap`·`iter_gap` 관용구는
**두 문서를 대조하는 판정**(가드 둘 + 비교 하나)을 뺄 때 쓴 것이다. 여기 판정은
문서 **하나의 첫 줄**에 정규식 하나를 대는 것이라 뺄 몸통이 없다 — 함수로 감싸면
`return None if DOC_HEAD.search(x) else "…"` 한 줄을 위한 껍데기가 늘 뿐이다
(ponytail 사다리 1번). 축이 정규식이면 관용구는 `CITATION` 쪽이다.

**기대 결과.** 제품 `src/` **0줄** · 고치는 파일 **`tests/test_docs.py` 하나**
(+ 단위 건수가 늘므로 `README.md` 의 「단위 618건」 한 줄) · 2절 변이 M1·M2 가
**2/2 사망**하고 각각 의도한 이름만 죽인다.

## 2. 착수 탐침 — 오늘 다시 쟀다 (2026-09-06 · 반복 361)

`digest [7]`「기록된 답을 실행 전에 다시 재라」의 **열세 번째 적용**. 저장소 파일은
한 바이트도 안 고치고 `tests/test_docs.py` 의 모듈 속성과 메서드를 **메모리에서**
갈아 끼워 전수를 돌렸다(하네스는 저장소 밖 `scratchpad`, `git status --short` 빈손).

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 618 · 실패 0 · 에러 0` — 죽은 단언 0 |
| **M1** `ITER_LINE` 을 `re.compile(r"iteration: ([0-9]+)", re.M)` 로(앵커 제거) | `Ran 618` — **죽은 단언 0 (생존)** |
| **M2** `DocHeadTest` 의 판정을 `^# \S` → `^` 로 | `Ran 618` — **죽은 단언 0 (생존)** |
| **M3** 양성 대조 — 같은 판정을 `^ZZZ` 로 | **실패 3**(`DocHeadTest.test_append_targets_start_with_h1` 의 subTest 셋) |

**M3 이 붙든 것**: 패치가 실제로 그 메서드에 꽂혔다는 증거다. M2 가 안 죽는 것은
하네스 배선 탓이 아니라 **판정이 정말 안 재지고 있기 때문**이다(`digest [6]`
「탐침의 배선을 먼저 의심한다」).

**항목의 기록과 오늘 실측이 일치한다** — `[6]` 이 적어 둔 「변이 둘이 살아남는다 ·
`DocHeadTest` 는 두 번 재서 둘 다 0」이 그대로 재현됐다. 계획 61 때와 달리 이번엔
숫자를 올릴 일이 없어 점수 `[6]` 을 그대로 둔다.

**제안 리터럴이 실제로 갈래를 가르는지도 미리 쟀다**(같은 탐침, 정규식만 단독 실행):

- `"x iteration: 1"`·`"iteration: 1x"` → 앵커 있으면 **매치 없음**, M1(앵커 제거)이면
  **둘 다 매치**. 즉 이 두 줄이 M1 을 죽인다.
- `"# 아카이브 요약"`·`"# 계획 색인"`·`"# 기록 (현재)"` → `^# \S` 로 **매치**
- `"## 완료"`·`"#제목"`·`"# "`·`""`·`"- [6] **항목**"`·`"  # 들여쓴 머리"` →
  `^# \S` 로 **매치 없음**, M2(`^`)면 **여섯 다 매치**. 즉 이 여섯이 M2 를 죽인다.
  (`"- [6] **항목**"` 은 이 파일이 존재하게 만든 그 사고의 모양 그대로다)

## 3. 스텝 — 1개

**왜 1개인가**(`rules/plan.md` 3절이 요구하는 한 줄): 두 자리는 같은 파일의 같은
관용구를 같은 방식으로 세우는 편집이고, 둘을 가르면 `README.md` 의 건수 줄이 두 번
움직여 되돌리기만 어려워진다. 되돌리기는 커밋 하나 revert.

### 스텝 1/1 — 두 판정을 리터럴로 못박는다 · 의존: 없음

- **어디서 시작하나**: `tests/test_docs.py:48`(`ITER_LINE` 정의) ·
  `tests/test_docs.py:142`(`DocHeadTest`) · `tests/test_docs.py:407`
  (`IterationPatternTest` 의 `ITER_LINE` 단언들)
- **무엇이 이미 참인가**: 계획 61 이 `iter_gap` 을 뺐고 `IterGapTest` 4건이 산다.
  `CitationPatternTest`(`tests/test_docs.py:155`)가 `CAUGHT`/`NOT_CAUGHT` 관용구의
  본이다 — 새 클래스는 그것을 그대로 베낀다.
- **할 일**:
  1. `IterationPatternTest` 의 `ITER_LINE` 단언에 리터럴 **두 줄**을 더한다
     (`"x iteration: 1"` · `"iteration: 1x"`). 왜 `night_iterations` 줄만으로는
     앵커가 안 재지는지(복수형 `s` 가 막는다)를 주석 한 줄로 남긴다.
  2. `r"^# \S"` 를 모듈 상수 `DOC_HEAD` 로 올린다(`ITER_LINE` 아래).
     `DocHeadTest` 는 `assertRegex(first, DOC_HEAD, …)` 로 바꾼다 — 실물 판정은
     그대로 남는다.
  3. `DocHeadPatternTest` 를 `CitationPatternTest` 옆 관용구로 세운다:
     `CAUGHT` 3개 · `NOT_CAUGHT` 6개(2절 목록 그대로).
- **TDD**: `rules/dev.md` 0절대로 **RED 를 눈으로 먼저 본다** — 새 클래스를 먼저
  쓰고 `NameError: name 'DOC_HEAD' is not defined` 를 확인한 뒤 상수를 올린다.
- **완료 기준**: 4절.
- **건드릴 파일 (예상)**: `tests/test_docs.py` · `README.md`(단위 건수 줄).
  **여기 없는 파일을 고쳐야 하면 YELLOW.**

## 4. 완료 기준 — 전부 검증 가능

1. **M1 사망** — 메모리에서 `ITER_LINE` 을 앵커 없는 것으로 갈면
   `IterationPatternTest` 의 그 시험 **하나가** 죽는다(무변이 대조군은 죽은 것 0건).
2. **M2 사망** — `DocHeadTest` 의 판정 대신 `DOC_HEAD` 를 `re.compile(r"^")` 로 갈면
   `DocHeadPatternTest.test_pattern_leaves_non_h1_heads` 가 죽는다.
3. **M3(양성 대조) 는 여전히 실물 쪽을 죽인다** — 판정을 `^ZZZ` 로 갈면
   `DocHeadTest` 가 죽는다. 두 층이 각각 자기 것을 잡는다는 뜻이다.
4. **감지력이 낮아지지 않았다** — 계획 61 이 세운 M5(`ITER_ROW` 넓히기)를 다시 걸어
   `IterationPatternTest.test_only_the_exact_row_matches` 가 여전히 죽는 것을 확인한다.
5. **전수 초록 맨몸** — `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)
   PYTHONPATH=src python3 -m unittest discover -b -s tests` 가 `OK` rc 0 이고
   건수가 618 → **늘어난 수**로 바뀌며 `README.md` 의 「단위 N건」이 같은 수다.
6. **범위 무접촉** — `git diff --stat d763317 HEAD -- src/ e2e/ docs/specs/ data/` 가
   **빈손**이고 `data/crawl.db` sha256 이 `85c96744…5bda18` 그대로다.
7. **`status.md` 의 `step`·`plan` 이 `index.md` 62번 행과 매 커밋 함께 움직인다**
   (계획 60 이 세운 `StepSyncTest` 의 세 번째 시험대).

## 5. 하지 않을 것

- **`ITER_ROW`·`STEP_ROW`·`STEP_LINE`·`PLAN_SLUG` 의 앵커** — 오늘 재지 않았다.
  같은 유형의 구멍이 거기도 있는지는 이 계획의 변이 목록 밖이다. 있으면
  `digest` 후보로 남긴다.
- **`CITATION` 정규식** — 이미 `CitationPatternTest` 가 양쪽으로 붙들고 있다.
- **판정을 순수 함수(`head_gap`)로 빼는 일반화** — 1절이 거부했다(ponytail 1번).
- **`step_gap`·`iter_gap` 을 공통 헬퍼로 합치기** — 계획 61 리뷰가 이미 거부했다
  (합치면 변이 하나가 두 축을 함께 죽여 갈래 귀속이 무너진다).
- **`APPEND_TARGETS` 에 문서 더하기** — 대상 목록은 이 계획의 범위 밖이다.
- **제품 `src/` · `e2e/` · `docs/specs/` · `data/`** — 한 줄도 안 건드린다.
- **원격 조작** — `--force`·`--amend`·`rebase`·PR 생성 없음. 병합은 사람 몫.

## 6. 설계 생략 사유

**설계 생략 — 트리거 0.** 새 모듈·파일 0(기존 `tests/test_docs.py` 안) · 공개
인터페이스 무변(제품 `src/` 0줄) · 데이터 구조 무변 · 파일 2개(3 미만) · 되돌리기는
커밋 하나 revert. **대안이 갈리는 자리 하나**(상수+리터럴 vs 순수 함수)는 1절이
저장소의 **선례**로 닫았다 — 정규식 축은 `CITATION`·`ITER_ROW` 가, 대조 판정 축은
`step_gap`·`iter_gap` 이 이미 각각의 관용구를 정해 두었고 여기는 정규식 축이다.
저울질할 것이 남아 있지 않다.

## 7. 위험

- **`DocHeadPatternTest` 의 `NOT_CAUGHT` 가 과하면 오탐 방향이 뒤집힌다** —
  예컨대 `"# "`(제목 없는 H1)를 「막아야 하는 것」으로 두는 판단은 `\S` 를 요구하는
  현재 판정 그대로다. 여섯 줄 전부 **현재 판정이 이미 거절하는 것**만 담아 판정을
  바꾸지 않는다(2절에서 실측 확인).
- **건수 줄 어긋남** — `README.md` 의 「단위 618건」을 같은 커밋에서 안 고치면
  `test_readme.py` 가 빨개진다. 계획 61 이 같은 자리를 밟았으니 잊지 않는다.
- **`-b` 는 통과한 테스트의 경고를 삼킨다**(`digest [4]`) — 새 클래스가 경고를 내도
  안 보인다. 이 계획은 정규식만 다뤄 경고를 낼 경로가 없다.
