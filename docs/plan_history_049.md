# 계획 63 — `anchor-net-cover`

`tests/test_docs.py` 의 **문서 가드 정규식 넷이 자기 앵커를 못 잰다.** `STEP_LINE` 의
`^`·`$` 를 지워도, `PLAN_SLUG`·`ITER_ROW`·`STEP_ROW` 의 `^` 를 지워도 전수 620건이
**죽은 단언 0** 으로 초록이다. 계획 62 가 `ITER_LINE` 에서 닫은 그 구멍의 형제이고,
실물 문서가 늘 「맞는 모양」이라 앵커를 무력화해도 아무 데도 안 걸리는,
이 저장소가 이미 네 번 닫은 그 자리다.

- **근거**: `docs/digest.md` `## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 의 `[6]`
  「계획 62 가 `ITER_LINE` 에서 닫은 앵커 구멍의 형제가 정규식 넷에 그대로 있다 —
  앵커를 지우는 변이 4/4 가 전수 620건에서 생존한다」(2026-09-06 계획 62 테스트
  phase 가 등재하며 **직교 편집이라 미뤘다**). 그 항목의 **여는 조건은 「그 정규식
  넷 중 하나를 손대는 날」**이고, 이 계획이 곧 그날이다 — 계획 62 의 5절
  「하지 않을 것」이 이 넷을 이름으로 적어 미뤘고, 그 계획이 반복 365 에 DONE 으로
  닫혔으므로 미룬 이유가 오늘 없어졌다. 계획 60 → 61 → 62 가 걸어온 것과 **글자
  그대로 같은 계승**이다(`step_gap` → `iter_gap` → `ITER_LINE`·`DOC_HEAD` → 앵커 넷).
- **1~5순위 실측 0건** (2026-09-06 반복 366):
  전수 `Ran 620 tests in 15.930s` · `OK` · rc 0 **맨몸** ·
  린터/타입체커 설정 파일 0개(`docs/project.md` 「린트/타입체크: 없음」 · 저장소
  최상위에 `pyproject.toml`·`setup.cfg`·`.ruff.toml`·`mypy.ini` 가 하나도 없다 —
  `ls -a` 로 확인, 설정은 `.gitignore` 하나뿐) ·
  `TODO`/`FIXME`/`HACK` 이 `src/`·`tests/`·`e2e/` 에 **1건**인데 그것은
  `tests/test_indexer.py:759` 의 **파서 입력 문자열 안**(`"<p>김치찌개 <!-- TODO: …"`)
  이라 코드 부채가 아니다 · `docs/candidates.md` 없음 · `docs/patches/` 없음 ·
  `digest ## 보류 (승인 대기)` **0건**(절 본문이 주석 한 줄뿐이다) ·
  `gh issue list --state open` **0건 rc 0** · 활성 계획 0.
- **6순위의 더 높은 점수는 전부 「여는 조건 미도래」다** — `[9]` `/search` 몫 ·
  `[8]` 숨은 텍스트 뒷절반 · `[8]` 토크나이저는 실물 코퍼스/재색인이 필요하고,
  `[7]` macOS pycache 는 처방이 이미 들어갔고, `[7]` 재파싱 몫 배정과 `[7]` 키셋
  페이지네이션은 사람 결정이며, `[6]` 캡 하향 · `[6]` `_IMPLIED_END` 표 ·
  `[6]` `extract_blocks` 이름표는 각각 「캡을 내리는 날」·「표를 손으로 고치는 날」·
  「실물 코퍼스」다. **여는 조건이 실제로 온 항목은 `[6]` 하나다.**
- **기점**: `loop/passage-cost-band` 의 계획 62 마감 커밋(`1752ecc`, 원격 동일 —
  `git ls-remote origin loop/passage-cost-band` = `1752ecc7b210…`). 고칠 파일
  `tests/test_docs.py` 는 계획 60·61·62 가 세운 `step_gap`·`iter_gap`·`DOC_HEAD`
  관용구 위에 서 있고 그것들이 `origin/main`(`d1fe3e9`)에는 0건이라
  **`main` 에서 새로 따면 안 된다.** 브랜치는 계획 57~62 와 같이 쌓아 둔 채로 간다.
- **원격**: `origin/main` 은 계획 56(`d1fe3e9`)까지고 열린 PR 은 0건이다. 병합은 사람 몫.

## 1. 문제 · 목표 · 기대 결과

**문제.** 정규식 넷이다. 넷 다 오늘 **앵커가 붙어 있고 판정도 옳지만**, 그 앵커를
지우는 편집을 아무도 못 본다 — 전수 620건에서 죽는 단언이 0이다.

| 상수 | 자리 | 앵커를 지워도 죽는 단언 |
|---|---|---|
| `STEP_LINE` | `tests/test_docs.py:58` | **0** (`^`·`$` 둘 다 제거) |
| `PLAN_SLUG` | `tests/test_docs.py:59` | **0** (`^` 제거) |
| `ITER_ROW` | `tests/test_docs.py:47` | **0** (`^` 제거) |
| `STEP_ROW` | `tests/test_docs.py:60` | **0** (`^` 제거) |

지금 앵커를 재는 줄처럼 보이는 것은 둘인데 **둘 다 다른 것을 재고 있다**:

① `StepPatternTest.test_status_lines_need_the_whole_line`
(`tests/test_docs.py:331`)의 `assertIsNone(STEP_LINE.search("step: 1"))` 이 막는 것은
앵커가 아니라 **`N/M` 모양**이다 — `^`·`$` 를 지워도 `"step: 1"` 은 여전히 안 물린다.
② `IterationPatternTest` 의 `assertIsNone(ITER_ROW…)` 계열은 표의 **이웃 행**을
가르지 앵커를 안 잰다 — 넓힌 정규식이 첫 매치를 그대로 집으면 초록이다.

**계획 62 가 `ITER_LINE` 의 `night_iterations: 90` 에서 본 착시와 글자 그대로
같은 모양이다** — 「앵커를 재는 줄처럼 보이는데 실은 다른 축을 재는 줄」.

**목표.** 넷의 앵커를 **합성 리터럴**로 못박는다. 계획 62 가 `ITER_LINE` 에 쓴 관용구
그대로이고(`assertIsNone(ITER_LINE.search("x iteration: 1"))` ·
`assertIsNone(ITER_LINE.search("iteration: 1x"))`), 표 축은 `IterationPatternTest`·
`StepPatternTest` 가 이미 쓰는 **「이웃을 일부러 앞에 두는 합성 표」** 그대로다 —
넓힌 정규식이 엉뚱한 수를 집게 만들어 죽인다.

- 줄 축(`STEP_LINE`·`PLAN_SLUG`)은 `StepPatternTest` 에 **리터럴 세 줄**을 더한다:
  `"x step: 1/1"`(`^`) · `"step: 1/1x"`(`$`) · `"x plan: a"`(`^`).
- 표 축(`ITER_ROW`·`STEP_ROW`)은 두 합성 표에 **줄 중간에서 시작하는 잡음 행**을
  하나씩 더한다. 앵커가 있으면 안 물리고, 없으면 그 행의 수를 집어 기존 단언이 죽는다.

**왜 `PLAN_SLUG` 에는 꼬리 리터럴이 없나.** `PLAN_SLUG` 는 `$` 가 **일부러** 없다 —
`plan: index-step-sync 계획 60 (설계 완료)` 처럼 슬러그 뒤에 설명이 붙는 것이 계약이고
`tests/test_docs.py:333` 이 그것을 이미 잰다. 그래서 이 축의 앵커는 `^` 하나뿐이다.

**기대 결과.** 제품 `src/` **0줄** · 고치는 파일 **`tests/test_docs.py` 하나**
(+ 단위 건수가 늘므로 `README.md` 의 「단위 620건」 한 줄) · 2절 변이 M1~M4 가
**4/4 사망**하고 각각 의도한 이름만 죽인다.

## 2. 착수 탐침 — 오늘 다시 쟀다 (2026-09-06 · 반복 366)

`digest [7]`「기록된 답을 실행 전에 다시 재라」의 **열네 번째 적용**. 저장소 파일은
한 바이트도 안 고치고 `tests/test_docs.py` 의 모듈 상수를 `mock.patch.object` 로
**메모리에서** 갈아 끼워 전수를 돌렸다(하네스는 저장소 밖 `scratchpad`,
`git status --porcelain` 빈손).

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 620 tests in 15.930s · OK · rc 0` — 죽은 단언 0 |
| **M1** `STEP_LINE` 앵커 `^`·`$` 제거 | `Ran 620` — **죽은 단언 0 (생존)** |
| **M2** `PLAN_SLUG` 앵커 `^` 제거 | `Ran 620` — **죽은 단언 0 (생존)** |
| **M3** `ITER_ROW` 앵커 `^` 제거 | `Ran 620` — **죽은 단언 0 (생존)** |
| **M4** `STEP_ROW` 앵커 `^` 제거 | `Ran 620` — **죽은 단언 0 (생존)** |
| **M5** 양성 대조 — 같은 넷을 각각 `^ZZZ` 꼴로 | **실패 6 · 6 · 5 · 3** |

**M5 가 붙든 것**: 패치가 실제로 그 상수에 꽂혔다는 증거다. M1~M4 가 안 죽는 것은
하네스 배선 탓이 아니라 **앵커가 정말 안 재지고 있기 때문**이다(`digest [6]`
「탐침의 배선을 먼저 의심한다」). 죽은 이름도 축별로 갈렸다 — `STEP_LINE`·`PLAN_SLUG`
는 `StepGapTest` 4 + `StepPatternTest` 1 + `StepSyncTest` 1, `ITER_ROW` 는
`IterGapTest` 3 + `IterationPatternTest` 1 + `IterationSyncTest` 1, `STEP_ROW` 는
`StepGapTest` 2 + `StepPatternTest` 1 이다.

**항목의 기록과 오늘 실측이 일치한다** — `[6]` 이 적어 둔 「넷 다 죽은 단언 0」이
그대로 재현됐다. **다른 것은 양성 대조의 건수 하나뿐이다** — 항목은 `6·6·4·1` 로
적었고 오늘은 `6·6·5·3` 이다. 대조 리터럴의 **모양이 달라서**(오늘 `ITER_ROW` 는
`^ZZZ([0-9]+) \|`, `STEP_ROW` 는 `^ZZZ%s \| …` 로 갈았다) 함께 죽는 이름이 늘어난
것이고, 대조가 증명하는 것(배선이 꽂혔다)은 어느 쪽이든 같다. 점수 `[6]` 을 그대로 둔다.

**제안 리터럴이 실제로 갈래를 가르는지도 미리 쟀다**(같은 탐침, 정규식만 단독 실행 —
왼쪽이 오늘의 실물 정규식, 오른쪽이 앵커를 지운 변이):

- `"x step: 1/1"` → 실물 **매치 없음** · `^` 를 지운 변이는 **매치**
- `"step: 1/1x"` → 실물 **매치 없음** · `$` 를 지운 변이는 **매치**
- `"x plan: a"` → 실물 **매치 없음** · `^` 를 지운 변이는 **매치**
- `IterationPatternTest.TABLE` 의 정확한 행 **앞에** 잡음 행
  (`앞 계획은` 칸 다음에 `반복`·`999` 칸이 오는 줄)을 끼우면 → 실물은 그대로 `232`,
  `^` 를 지운 변이는 **`999`** 를 집는다
- `StepPatternTest.TABLE` 의 정확한 행 **앞에** 잡음 행
  (`메모 — 아래는 옛 행` 칸 다음에 `plan_index-step-sync`·`완료`·`loop/x`·`9/9` 칸이
  오는 줄)을 끼우면 → 실물은 그대로 `1/1`, `^` 를 지운 변이는 **`9/9`** 를 집는다

즉 **다섯 줄이 M1~M4 를 전부 죽인다.** 실물 정규식에서는 다섯 다 오늘 값이 그대로라
**오탐 0** 이다(위 목록의 「실물」 쪽이 그 실측이다).

## 3. 스텝 — 1개

**왜 1개인가**(`rules/plan.md` 3절이 요구하는 한 줄): 넷은 같은 파일의 같은 관용구를
같은 방식으로 세우는 편집이고, 가르면 `README.md` 의 건수 줄이 여러 번 움직여
되돌리기만 어려워진다. 되돌리기는 커밋 하나 revert.

### 스텝 1/1 — 앵커 넷을 합성 리터럴로 못박는다 · 의존: 없음

- **어디서 시작하나**: `tests/test_docs.py:296`(`StepPatternTest`) ·
  `tests/test_docs.py:422`(`IterationPatternTest`)
- **무엇이 이미 참인가**: 계획 62 가 `IterationPatternTest` 에 앵커 리터럴 두 줄
  (`"x iteration: 1"`·`"iteration: 1x"`, `tests/test_docs.py:454`)을 세웠다 —
  **새 리터럴은 그 줄을 그대로 베낀다.** `StepPatternTest.TABLE`
  (`tests/test_docs.py:308`)과 `IterationPatternTest.TABLE`
  (`tests/test_docs.py:433`)은 이미 「이웃을 일부러 앞에 두는」 합성 표다 — 새 잡음
  행은 그 표에 한 줄씩 끼운다.
- **할 일**:
  1. `StepPatternTest.test_status_lines_need_the_whole_line` 에 리터럴 **세 줄**을
     더한다(`"x step: 1/1"` · `"step: 1/1x"` · `"x plan: a"`). 지금 있는
     `STEP_LINE.search("step: 1")` 줄이 막는 것은 앵커가 아니라 `N/M` 모양이라는
     것을 주석 한 줄로 남긴다 — 계획 62 가 `night_iterations` 줄에 남긴 것과 같다.
  2. `IterationPatternTest.TABLE` 에 **줄 중간에서 시작하는 잡음 행**을 정확한 행
     앞에 끼운다 — 첫 칸이 `앞 계획은` 이고 그 다음이 `반복`·`999` 칸인 줄이다.
     `test_only_the_exact_row_matches` 의 실패 메시지에 「줄 중간에서 시작하는 행」을
     더한다(단언 자체는 그대로 `232` 를 요구한다).
  3. `StepPatternTest.TABLE` 에 같은 모양의 잡음 행을 정확한 행 앞에 끼운다 —
     첫 칸이 `메모 — 아래는 옛 행` 이고 그 다음이 `plan_index-step-sync`·`완료`·
     `loop/x`·`9/9` 칸인 줄이다. `test_row_is_picked_by_exact_slug` 의 실패 메시지에
     같은 한마디를 더한다(단언은 그대로 `1/1`).
- **TDD**: `rules/dev.md` 0절대로 **RED 를 눈으로 먼저 본다** — 잡음 행 둘을 먼저
  끼워 `999`·`9/9` 로 빨개지는 것을 본 뒤 앵커가 그것을 막는 것을 확인한다.
  (앵커는 이미 붙어 있으므로 RED 는 「잡음 행이 실제로 함정이다」를 확인하는 쪽이다 —
  잡음 행을 넣고 앵커를 지운 상태에서 빨강, 앵커를 되돌리면 초록.)
- **완료 기준**: 4절.
- **건드릴 파일 (예상)**: `tests/test_docs.py` · `README.md`(단위 건수 줄).
  **여기 없는 파일을 고쳐야 하면 YELLOW.**

## 4. 완료 기준 — 전부 검증 가능

1. **M1 사망** — 메모리에서 `STEP_LINE` 을 앵커 없는 것으로 갈면
   `StepPatternTest.test_status_lines_need_the_whole_line` 이 죽는다.
   `^` 만 지운 변이와 `$` 만 지운 변이를 **따로** 걸어 **둘 다** 죽는 것을 본다.
2. **M2 사망** — `PLAN_SLUG` 의 `^` 를 지우면 같은 시험이 죽는다.
3. **M3 사망** — `ITER_ROW` 의 `^` 를 지우면
   `IterationPatternTest.test_only_the_exact_row_matches` 가 죽는다.
4. **M4 사망** — `STEP_ROW` 의 `^` 를 지우면
   `StepPatternTest.test_row_is_picked_by_exact_slug` 가 죽는다.
5. **오탐 0 · 감지력 무회귀** — 무변이 대조군이 `OK`(죽은 것 0건)이고, 계획 62 가
   세운 `ITER_LINE` 앵커 변이가 여전히 `IterationPatternTest` 를 죽인다.
6. **전수 초록 맨몸** — `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)
   PYTHONPATH=src python3 -m unittest discover -b -s tests` 가 `OK` rc 0 이고
   건수가 620 → **늘어난 수**로 바뀌며 `README.md` 의 「단위 N건」이 같은 수다.
   **정정 — 2026-09-06 테스트 phase(반복 368).** 「늘어난 수」는 3절의 처방과
   어긋난 예측이었다: 처방이 **기존 시험 메서드에 단언을 더하고 합성 표에 행을
   끼우는 것**이라 메서드 수가 안 는다. 실제는 **620 무변**이고 `README.md` 의
   「단위 620건」이 이미 같은 수다. **기준의 뜻(전수 초록 + README 일치)은 그대로
   요구하고 건수 증가 요구만 무효**로 한다 — 수를 맞추려 시험을 쪼개는 것은
   계수기를 위한 편집이다. README 대조가 살아 있는 것은 이 phase 가 쟀다:
   `test_readme.UNIT_COUNT` 를 「못 뽑는 꼴」과 「다른 수를 뽑는 꼴」로 각각 갈면
   `test_verification_counts_match_reality` 가 **각각 1건씩 죽는다**.
7. **범위 무접촉** — `git diff --stat 1752ecc HEAD -- src/ e2e/ docs/specs/ data/` 가
   **빈손**이고 `data/crawl.db` sha256 이 `85c96744…5bda18` 그대로다.
8. **`status.md` 의 `step`·`plan` 이 `index.md` 63번 행과 매 커밋 함께 움직인다**
   (계획 60 이 세운 `StepSyncTest` 의 네 번째 시험대).

**e2e 실측 — 2026-09-06 · 반복 370 · 8/8 충족** (`docs/e2e/anchor-net-cover/result.md`).
하나씩 다시 쟀다: 1 M1a·M1b 가 각각 `Ran 620 · failures=1` 로 `test_status_lines_
need_the_whole_line` 을 죽인다 · 2 M2 도 같은 시험 1건 · 3 M3 → `test_only_the_exact_
row_matches` 1건 · 4 M4 → `test_row_is_picked_by_exact_slug` 1건 · 5 M0 대조군 `OK`
(오탐 0)이고 계획 62 의 `ITER_LINE` 변이 둘이 각각 1건씩 그대로 죽는다(감지력 무회귀) ·
6 맨몸 전수 `Ran 620 tests in 15.874s · OK · rc 0` 이고 `README.md` 「단위 620건」·
「e2e 시나리오 21종」이 실물과 일치 · 7 범위 diff 빈손 · `data/crawl.db` sha256 무변 ·
8 `status.md` `step: 1/1` ↔ `index.md` 63번 행 `1/1`, 그리고 실물 복사본에서 두 값을
서로 반대 방향으로 어긋내면 `StepSyncTest` 가 양쪽 다 문다.

**6번의 정정도 유효성을 다시 쟀다 — 단언을 안 낮췄다.** `test_readme.UNIT_COUNT` 를
「못 뽑는 꼴」·「다른 수를 뽑는 꼴」로, `E2E_COUNT` 를 「다른 수를 뽑는 꼴」로 갈면
`test_verification_counts_match_reality` 가 **각각 1건씩** 죽고 무변이 대조군은 `OK`
다. 정정이 지운 것은 「메서드 수가 는다」는 예측 하나뿐이고 「전수 초록 + README 일치」는
세 갈래로 살아 있다.

## 5. 하지 않을 것

- **`ARCHIVE` 의 `^…$`** — 오늘 탐침에서 이것도 죽은 단언 0 이지만 `.match()` 로만
  쓰여 `^` 가 애초에 잉여다(`digest` 항목이 「값이 더 낮다」로 적어 뒀다). 값이 0에
  가까운 자리에 단언을 세우면 `digest [5]`(`sys.path`)와 같은 「닿을 수 없는 가드」가
  하나 더 는다. **`ARCHIVE` 를 정말 고치려면 `^` 를 지우는 쪽**이지 재는 쪽이 아니고,
  그것은 이 계획의 범위가 아니다.
- **`CITATION`·`DOC_HEAD`·`ITER_LINE`** — 계획 42·62 가 이미 양쪽으로 붙들었다.
- **판정을 순수 함수로 빼는 일반화** — 여기 축은 정규식이지 두 문서 대조가 아니다.
  계획 62 가 같은 이유로 거부했다(ponytail 사다리 1번).
- **`PLAN_SLUG` 에 `$` 를 붙이는 것** — 1절이 계약으로 거부했다(슬러그 뒤 설명은
  정상이고 `tests/test_docs.py:333` 이 그것을 잰다). **판정을 바꾸는 편집은 0줄이다.**
- **`step_gap`·`iter_gap` 을 공통 헬퍼로 합치기** — 계획 61 리뷰가 이미 거부했다.
- **제품 `src/` · `e2e/` · `docs/specs/` · `data/`** — 한 줄도 안 건드린다.
- **원격 조작** — `--force`·`--amend`·`rebase`·PR 생성 없음. 병합은 사람 몫.

## 6. 설계 생략 사유

**설계 생략 — 트리거 0.** 새 모듈·파일 0(기존 `tests/test_docs.py` 안) · 공개
인터페이스 무변(제품 `src/` 0줄) · 데이터 구조 무변 · 파일 2개(3 미만) · 되돌리기는
커밋 하나 revert. **저울질할 대안이 남아 있지 않다** — 계획 62 가 「정규식 축은
`CITATION`·`ITER_ROW` 의 합성 리터럴, 대조 판정 축은 `step_gap`·`iter_gap` 의 순수
함수」로 선례를 갈라 두었고 여기는 **정규식 축이며, 심지어 계획 62 가 쓴 것과 같은
클래스에 같은 모양의 줄을 더하는 편집**이다. 2절이 다섯 리터럴의 갈림을 실측으로
확인했으므로 갈릴 것이 없다.

## 7. 위험

- **잡음 행이 다른 단언을 함께 움직인다** — `IterationPatternTest.TABLE` 과
  `StepPatternTest.TABLE` 은 같은 클래스의 여러 시험이 공유한다. 2절 실측에서 실물
  정규식의 결과값(`232`·`1/1`)이 안 움직이는 것을 확인했지만, 개발 phase 는
  **`test_absent_slug_matches_nothing`(`tests/test_docs.py:322`)이 여전히 `None`
  인지**를 함께 본다. `StepGapTest.INDEX` 는 **안 건드린다**(다른 상수다).
- **건수 줄 어긋남** — `README.md` 의 「단위 620건」을 같은 커밋에서 안 고치면
  `test_readme.py` 가 빨개진다. 계획 61·62 가 같은 자리를 밟았으니 잊지 않는다.
- **잡음 행이 마크다운 표처럼 읽힌다** — 새 잡음 행은 파이썬 문자열 리터럴 안에만
  살고 문서에는 안 들어간다. 문서 쪽 표를 흉내 내는 것은 이 계획의 범위 밖이다.
- **`-b` 는 통과한 테스트의 경고를 삼킨다**(`digest [4]`) — 이 계획은 정규식만 다뤄
  경고를 낼 경로가 없다.
