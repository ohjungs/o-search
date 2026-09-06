---
signal: GREEN
phase: 개발
step: 1/1
attempt: 0
iteration: 367
updated: 2026-09-06
ctx: 47
night_iterations: 184
night_red: 2
night_retries: 4
plan: anchor-net-cover 계획 63 (개발 1/1 완료 · 다음은 테스트)
---

## 현재 상태

**계획 63 의 유일한 스텝을 닫았다 — 정규식 넷의 앵커가 이제 자기를 잰다.**
`tests/test_docs.py` 한 파일 15줄(+1 −1)이고 완료 기준 8개 중 7개가 그대로 맞았다.
남은 하나(6번의 「건수가 620 → 늘어난 수」)는 **아래 「계획서와 어긋난 것」** 에 적었다.

## 무엇을 세웠나

| 세운 것 | 자리 | 죽이는 변이 |
|---|---|---|
| `STEP_LINE.search("x step: 1/1")` → `None` | `StepPatternTest.test_status_lines_need_the_whole_line` | M1a (`^` 제거) |
| `STEP_LINE.search("step: 1/1x")` → `None` | 같은 곳 | M1b (`$` 제거) |
| `PLAN_SLUG.search("x plan: a")` → `None` | 같은 곳 | M2 (`^` 제거) |
| `IterationPatternTest.TABLE` 에 잡음 행(`메모` 칸 뒤에 `반복`·`999` 칸) | 정확한 행 **앞** | M3 (`^` 제거) |
| `StepPatternTest.TABLE` 에 잡음 행(`메모` 칸 뒤에 `plan_index-step-sync`·`완료`·`loop/x`·`9/9` 칸) | 정확한 행 **앞** | M4 (`^` 제거) |

잡음 행은 **줄 중간에서 시작한다** — 앵커가 살아 있으면 `re.M` 의 `^` 가 그 행을
아예 안 보고, 앵커를 지우면 `999`·`9/9` 를 집어 `assertEqual` 이 터진다. 실물
정규식의 결과값은 `232`·`1/1` 그대로다.

## RED 를 이 반복에서 직접 봤다

`rules/dev.md` 0절의 2번은 남의 관찰로 대신할 수 없다. 그래서 **편집 전에 먼저**
M0·M1a·M1b·M2·M3·M4 를 이 반복에서 다시 돌려 `Ran 620 · OK · 죽은 단언 0` 으로
**6/6 생존**하는 것을 눈으로 본 뒤, 다섯 줄을 넣고 같은 여섯을 다시 돌렸다.

| 변이 | 편집 전 | 편집 후 |
|---|---|---|
| **M0** 무변이 대조군 | 죽은 단언 0 | 죽은 단언 **0** (오탐 0) |
| **M1a** `STEP_LINE` 의 `^` 만 제거 | 0 (생존) | **1** — `StepPatternTest.test_status_lines_need_the_whole_line` |
| **M1b** `STEP_LINE` 의 `$` 만 제거 | 0 (생존) | **1** — 같은 시험 |
| **M2** `PLAN_SLUG` 의 `^` 제거 | 0 (생존) | **1** — 같은 시험 |
| **M3** `ITER_ROW` 의 `^` 제거 | 0 (생존) | **1** — `IterationPatternTest.test_only_the_exact_row_matches` |
| **M4** `STEP_ROW` 의 `^` 제거 | 0 (생존) | **1** — `StepPatternTest.test_row_is_picked_by_exact_slug` |

빨강은 **정확히 새로 넣은 줄에서** 났다(실패 보고서의 소스 줄이 `assertIsNone(
STEP_LINE.search("x step: 1/1"), …)` 등으로 찍혔다) — 엉뚱한 데서 터진 것이 아니다.
하네스는 저장소 밖(`scratchpad/mutate.py`)이고 `mock.patch.object` 로 메모리에서만
갈아 끼웠다 — 저장소는 이 다섯 줄 말고 한 바이트도 안 움직였다.

**감지력 무회귀도 같이 쟀다**: 계획 62 가 세운 `ITER_LINE` 앵커 변이 둘(`^` 제거·
`$` 제거)이 여전히 `IterationPatternTest.test_status_line_needs_the_whole_line` 을
**각각 1건씩** 죽인다. 양성 대조(정규식을 `ZZZ` 로 통째 죽이기)는 **6 · 6 · 5 · 4**
— 배선은 그대로다.

## 계획서와 어긋난 것 하나 — 테스트 건수가 안 늘었다

완료 기준 6번은 「건수가 620 → **늘어난 수**로 바뀌며 `README.md` 의 「단위 N건」이
같은 수다」로 적혀 있는데, 실제 건수는 **620 그대로**다. 계획서 3절의 처방이
**기존 시험 메서드에 단언을 더하고 기존 합성 표에 행을 끼우는 것**이지 새 메서드를
만드는 것이 아니기 때문이다 — 처방대로 했더니 메서드 수가 안 변한 것이다.
숫자를 맞추려고 시험을 쪼개는 것은 **계수기를 위한 편집**이라 하지 않았다.
그 결과 `README.md:104` 의 「단위 620건」이 **이미 맞고**, `test_readme.py` 의 건수
대조도 초록이다. 즉 기준 6번의 뜻(전수 초록 + README 일치)은 충족이고, 문장의
「늘어난 수」만 처방과 맞지 않았다. **`README.md` 는 무접촉이다.**

## 완료 기준 8개

1. **M1 사망** — `^` 만 지운 변이와 `$` 만 지운 변이를 **따로** 걸어 **둘 다** 죽었다. ✅
2. **M2 사망** — `PLAN_SLUG` 의 `^` 를 지우니 같은 시험이 죽었다. ✅
3. **M3 사망** — `ITER_ROW` 의 `^` 를 지우니 `test_only_the_exact_row_matches` 가 죽었다. ✅
4. **M4 사망** — `STEP_ROW` 의 `^` 를 지우니 `test_row_is_picked_by_exact_slug` 가 죽었다. ✅
5. **오탐 0 · 감지력 무회귀** — M0 `OK`(0건) · `ITER_LINE` 변이 둘이 여전히 죽인다. ✅
6. **전수 초록 맨몸** — `Ran 620 tests` · `OK` · **rc 0** · README 「단위 620건」과 일치. ⚠ 건수는 위 절대로 안 늘었다.
7. **범위 무접촉** — `git diff --stat HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 그대로. ✅
8. **`status.md` ↔ `index.md` 63번 행** — 둘 다 `1/1` 로 함께 움직였다(`StepSyncTest` 네 번째 시험대). ✅

## 하지 않은 것

- **`ARCHIVE` 의 `^…$`** — 계획서 5절이 이름으로 미룬 것이라 안 건드렸다.
- **`StepGapTest.INDEX`** — 다른 상수라 안 건드렸다. 위험 절이 함께 보라고 한
  `test_absent_slug_matches_nothing` 도 여전히 `None` 이다(전수 초록에 포함).
- **`README.md`** — 건수가 안 변해 고칠 것이 없었다(위 절).

## 다음

**테스트 phase.** 스텝이 1/1 로 다 닫혔으니 `rules/test.md` 로 넘어간다. 이번 스텝의
산출물이 곧 테스트라 새로 세울 것보다 **갭을 찾는 눈**이 할 일이다 — 계획 60·61·62·63
이 `step_gap`·`iter_gap`·`ITER_LINE`·`DOC_HEAD`·앵커 넷을 차례로 닫았으므로, 남은
자리는 `ARCHIVE` 의 `^…$`(`.match()` 로만 불려 앵커가 안 재진다)와 `APPEND_TARGETS`
쪽이다. `digest ## 다음 계획 후보` 의 `[6]` 항목은 **이번 반복이 닫았다**.

## 한도

- 병합은 사람 몫이다 — 계획 57~63 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 이번 커밋도 같은 브랜치에 그대로 쌓았다 — `--force`·`--amend`·`rebase` 없음.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
- `docs/digest.md` 는 **200줄 정각**이라 이번 반복도 줄을 안 늘렸다 — `[6]` 항목의
  같은 줄 끝에 닫힌 사실만 이어 붙였다.
- `history_current.md` 는 회전 직후 65줄에서 이번 5줄을 더해 **70줄**(상한 300).
