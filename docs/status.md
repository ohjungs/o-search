---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 366
updated: 2026-09-06
ctx: 61
night_iterations: 183
night_red: 2
night_retries: 4
plan: anchor-net-cover 계획 63 (계획 완료 · 설계 생략 · 다음은 개발 1/1)
---

## 현재 상태

**계획 62 가 반복 365 에 DONE 으로 닫혀 활성 계획이 0 이었다 — 탐색을 돌려 계획 63
`anchor-net-cover` 를 등재했다.** 계획서 `docs/plan_anchor-net-cover.md` ·
`index.md` 63번 행 `0/1` · 설계 생략(트리거 0) · 다음 반복은 **개발 1/1** 이다.

## 무엇을 여는가

`tests/test_docs.py` 의 **문서 가드 정규식 넷이 자기 앵커를 못 잰다.** 넷 다 오늘
앵커가 붙어 있고 판정도 옳지만, 그 앵커를 지우는 편집을 아무도 못 본다.

| 상수 | 자리 | 앵커를 지워도 죽는 단언 |
|---|---|---|
| `STEP_LINE` | `tests/test_docs.py:58` | **0** (`^`·`$` 둘 다 제거) |
| `PLAN_SLUG` | `tests/test_docs.py:59` | **0** (`^` 제거) |
| `ITER_ROW` | `tests/test_docs.py:47` | **0** (`^` 제거) |
| `STEP_ROW` | `tests/test_docs.py:60` | **0** (`^` 제거) |

앵커를 재는 줄처럼 보이는 것이 둘 있는데 **둘 다 다른 것을 잰다** — ①
`StepPatternTest` 의 `STEP_LINE.search("step: 1")` 이 막는 것은 앵커가 아니라
**`N/M` 모양**이고(앵커를 지워도 그 줄은 초록) ② `ITER_ROW` 쪽 단언은 표의
**이웃 행**을 가르지 앵커를 안 잰다. **계획 62 가 `ITER_LINE` 의
`night_iterations: 90` 에서 본 착시와 글자 그대로 같은 모양이다.**

## 1~5순위 실측 0건 — 「없다」가 아니라 재고 적었다

전수 `Ran 620 tests in 15.930s` · `OK` · **rc 0 맨몸** · 린터/타입체커 설정 파일 0개
(`docs/project.md` 「린트/타입체크: 없음」 · 저장소 최상위에 `pyproject.toml`·
`setup.cfg`·`.ruff.toml`·`mypy.ini` 가 하나도 없다 — `ls -a` 로 확인, 설정은
`.gitignore` 하나뿐) · `TODO`/`FIXME`/`HACK` 이 `src/`·`tests/`·`e2e/` 에 **1건**인데
그것은 `tests/test_indexer.py:759` 의 **파서 입력 문자열 안**
(`"<p>김치찌개 <!-- TODO: <a href=x> 옛 링크"`)이라 코드 부채가 아니다 ·
`docs/candidates.md` 없음 · `docs/patches/` 없음 · `digest ## 보류 (승인 대기)` 절
본문이 주석 한 줄뿐이라 **0건** · `gh issue list --state open` **0건 rc 0**(조회만,
PR 무접촉).

**6순위의 더 높은 점수는 전부 「여는 조건 미도래」다** — `[9]` `/search` 몫 · `[8]`
숨은 텍스트 뒷절반 · `[8]` 토크나이저는 실물 코퍼스/재색인, `[7]` macOS pycache 는
처방이 이미 들어갔고, `[7]` 재파싱 몫 배정과 `[7]` 키셋 페이지네이션은 사람 결정,
`[6]` 캡 하향 · `[6]` `_IMPLIED_END` 표 · `[6]` `extract_blocks` 이름표는 각각
「캡을 내리는 날」·「표를 손으로 고치는 날」·「실물 코퍼스」다. **여는 조건이 실제로
온 항목은 `[6]` 하나이고, 그것을 오게 만든 것이 어제 닫힌 계획 62 다** — 계획 62 의
5절 「하지 않을 것」이 이 넷을 이름으로 적어 미뤘다.

## 착수 탐침 — 기록된 답을 다시 쟀고 이번에도 맞았다

`digest [7]` 의 **열네 번째 적용**. 저장소 파일은 한 바이트도 안 고치고 모듈 상수를
`mock.patch.object` 로 **메모리에서** 갈아 끼워 전수를 돌렸다(하네스는 저장소 밖 ·
이 phase 내내 `git status --porcelain` 은 문서 편집 전까지 빈손).

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 620 tests in 15.930s · OK · rc 0` — 죽은 단언 0 |
| **M1** `STEP_LINE` 앵커 `^`·`$` 제거 | `Ran 620` — **생존**(죽은 단언 0) |
| **M2** `PLAN_SLUG` 앵커 `^` 제거 | `Ran 620` — **생존**(죽은 단언 0) |
| **M3** `ITER_ROW` 앵커 `^` 제거 | `Ran 620` — **생존**(죽은 단언 0) |
| **M4** `STEP_ROW` 앵커 `^` 제거 | `Ran 620` — **생존**(죽은 단언 0) |
| **M5** 양성 대조, 같은 넷을 `^ZZZ` 꼴로 | **실패 6 · 6 · 5 · 3** |

**M5 가 붙든 것**: 패치가 실제로 그 상수에 꽂혔다는 증거다 — M1~M4 가 안 죽는 것은
배선 탓이 아니라 앵커가 정말 안 재지고 있기 때문이다(`digest [6]`「탐침의 배선을
먼저 의심한다」). **항목의 기록과 어긋난 것은 대조 건수 하나뿐이다** — 항목은
`6·6·4·1` 로 적었고 오늘은 `6·6·5·3` 인데, 원인은 대조 리터럴의 **모양 차이**이고
대조가 증명하는 것은 어느 쪽이든 같아 점수 `[6]` 을 그대로 뒀다.

**제안 리터럴이 갈래를 가르는 것도 미리 쟀다**: `"x step: 1/1"`·`"step: 1/1x"`·
`"x plan: a"` 는 실물 정규식이면 매치 없음이고 앵커를 지운 변이면 셋 다 매치 ·
두 합성 표(`IterationPatternTest.TABLE`·`StepPatternTest.TABLE`)에 **줄 중간에서
시작하는 잡음 행**을 정확한 행 앞에 끼우면 실물은 `232`·`1/1` 그대로인데 변이는
`999`·`9/9` 를 집는다. **다섯 줄이 M1~M4 를 전부 죽이고 오탐은 0 이다.**

## 설계 생략 — 트리거 0

새 모듈·파일 0 · 제품 인터페이스 무변(`src/` 0줄) · 데이터 구조 무변 · 파일 2개 ·
되돌리기는 커밋 하나 revert. **저울질할 대안이 없다** — 계획 62 가 「정규식 축은
`CITATION`·`ITER_ROW` 의 합성 리터럴, 두 문서를 대조하는 판정 축은 `step_gap`·
`iter_gap` 의 순수 함수」로 선례를 갈라 두었고, 여기는 정규식 축이며 **계획 62 가 쓴
것과 같은 클래스에 같은 모양의 줄을 더하는 편집**이다.

## 다음

**개발 1/1.** `tests/test_docs.py` 에서 ① `StepPatternTest.
test_status_lines_need_the_whole_line` 에 리터럴 세 줄(`"x step: 1/1"`·
`"step: 1/1x"`·`"x plan: a"`)을 더하고 ② `IterationPatternTest.TABLE` 과
`StepPatternTest.TABLE` 에 줄 중간에서 시작하는 잡음 행을 하나씩 끼운다.
`rules/dev.md` 0절대로 **RED 를 눈으로 먼저 본다**(잡음 행을 넣고 앵커를 지운 상태의
빨강 → 앵커를 되돌려 초록). 건드릴 파일은 `tests/test_docs.py`·`README.md`(단위 건수
줄) 둘뿐이고, 여기 없는 파일을 고쳐야 하면 YELLOW 다. 완료 기준 8개는 계획서 4절에
있다. **`StepGapTest.INDEX` 는 안 건드린다**(다른 상수다).

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61·62 의 커밋이 `loop/passage-cost-band` 에
  쌓여 있고 `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 반복 365 커밋(`1752ecc`)은 원격에 정상 반영돼 있다(`git ls-remote origin
  loop/passage-cost-band` = `1752ecc7b210…`). 이번 커밋도 같은 브랜치에 그대로 쌓는다
  — `--force`·`--amend`·`rebase` 없음.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `docs/digest.md` 는 실측 **200줄**(상한 200 정각)이다 — 후보 `[6]` 에 줄을 더하지
  않고 **같은 줄 끝에** 연 사실만 이어 붙였다. 다음에 한 줄이라도 더해야 하면
  `rules/docs.md` 3절대로 **완료 항목부터** 지운다.
- 이번 스텝은 `docs/` 만 만졌다 — `src/`·`tests/`·`e2e/`·`README.md` 무접촉.
- **회전했다** — 이 반복의 기록을 붙이면 `history_current.md` 가 307줄로 상한 300 을
  넘어, 계획 61·62 의 반복 기록 열 개(반복 356~365)를 `history_064.md` 로 밀었다.
  둘 다 DONE 이고 `digest ## 완료` 에 이미 압축돼 있어 새로 압축할 것이 없었고,
  `digest` 의 아카이브 명부 줄과 계획 62 완료 항목에 회전 사실만 이어 붙였다
  (200줄 정각 유지). 지금 `history_current.md` 는 **65줄**, 다음 회전 번호는
  `history_065.md` 다.
