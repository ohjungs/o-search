---
signal: DONE
phase: e2e
step: 0/0
attempt: 0
iteration: 370
updated: 2026-09-06
ctx: 52
night_iterations: 187
night_red: 2
night_retries: 4
plan: null
---

## 현재 상태

**계획 63 `anchor-net-cover` 를 e2e 1/1 로 닫았다 — 통과 · 완료 기준 8/8 · 활성 계획 0.**
e2e 21종을 전부 맨몸으로 다시 돌려 **rc 0 · 21/21** 이고, 전수는 `Ran 620 tests in
15.874s` · `OK` · rc 0 이다. 결과는 `docs/e2e/anchor-net-cover/result.md`.

## e2e 결과

**새 e2e 파일 0개를 「해당 없음」으로 넘기지 않고 근거 셋으로 쟀다**(`rules/e2e.md` 3절) —
프로세스 밖 변화 0(`src/`·`e2e/`·`docs/specs/`·`data/` diff **빈손**) · 고친 상수 넷이
`tests/` 안이라 네 수단(웹 UI·HTTP API·CLI·라이브러리) 어디에도 걸 곳이 없다
(`src/` 에 `tests` 를 import 하는 줄 **0건**) · 새로 만들면 전수 명령과 겹쳐 「1회만」이
깨진다. 계획 60·61·62 가 밟은 자리와 같고 형식도 같다.

**대신 사용자 관점 검증을 실행했다.** 실물 `docs/` 를 `mktemp -d` 로 복사해 사람이 낼
법한 **편집 여덟**을 넣었다. 어긋냄 넷은 전부 `StepSyncTest` 가 문장으로 울고(스텝을
양방향으로 어긋냄 · `step:` 줄 들여쓰기 · `step: 1/1` 뒤 메모 · `plan:` 슬러그에 `-2`
접미 → 「등재가 빠졌다」), **표에 메모 행을 끼운 둘(D5·D6)은 오판 0 으로 조용하다.**
**오늘 계획이 산 자리가 그 「조용함」이다** — 이 계획 전이라면 판정은 같았겠지만 그것을
지키는 앵커가 무방비였고, 이제 앵커가 죽으면 그 자리에서 `9/9`·`999` 를 집어 빨개진다.

**완료 기준 8/8 을 오늘 다시 쟀다.** M0 대조군 `Ran 620 · OK · 죽은 단언 0`(오탐 0) ·
**M1a**(`STEP_LINE` `^`)·**M1b**(`$`) → `test_status_lines_need_the_whole_line` 각 1건 ·
**M2**(`PLAN_SLUG` `^`) → 같은 시험 1건 · **M3**(`ITER_ROW` `^`) →
`test_only_the_exact_row_matches` 1건 · **M4**(`STEP_ROW` `^`) →
`test_row_is_picked_by_exact_slug` 1건 · 계획 62 의 `ITER_LINE` 변이 둘도 여전히 각 1건
(감지력 무회귀). 기준선은 8축 전부 회귀 0 이라 `docs/project.md` 를 한 줄도 안 갱신했다.

## 계획서 6번의 「정정」도 유효성을 다시 쟀다 — 단언을 안 낮췄다

테스트 phase 가 완료 기준 6번의 「건수가 620 → 늘어난 수」를 **620 무변**으로 정정했고,
e2e 가 그 정정이 단언을 낮춘 것인지 재측했다. `test_readme.UNIT_COUNT` 를 「못 뽑는 꼴」
(`단위 N개`)로도 「다른 수를 뽑는 꼴」(`(\d+)`)로도 갈면 `test_verification_counts_match
_reality` 가 **각각 1건씩** 죽고, `E2E_COUNT` 를 같은 식으로 갈아도 1건 죽는다.
무변이 대조군은 `OK`. **정정이 지운 것은 「메서드 수가 는다」는 예측 하나뿐이다.**

## e2e 가 잡은 것 — 없음

계획 62 e2e 의 교훈(「실물을 좇는다고 읽히는 주석이 실물과 어긋난다」)을 오늘 그대로
적용해 diff 의 주석·실패 메시지 리터럴 여섯 주장을 실물과 대조했다 — **어긋난 곳 0**.
`^` 를 지운 변이가 정말 `8/8` 을 집고(주석 ④), 잡음 행은 정말 표의 네 번째 행이며
(`IterationPatternTest`), `^` 를 지우면 정말 `999` 를 집는다. 실패 메시지의 값→범인 대응
셋(`9/9`=슬러그 무시 · `3/7`=접두 · `8/8`=`^` 사망)도 셋 다 그 값이 나오고, 표의 수 넷은
`9/9`·`3/7`·`8/8`·`1/1` 로 겹침이 없다(리뷰가 넣은 조건이 실물에서 성립한다).

## 검증

전수 **맨몸** `Ran 620 tests in 15.874s` · `OK` · **rc 0**.
e2e 21종 개별 실행 **전부 rc 0**. `ls e2e/*.py` **21개** ↔ `README.md` 「e2e 시나리오 21종」 ·
`README.md:104` 「단위 620건」 ↔ 실제 620.
범위 무접촉 — `git diff --stat 1752ecc HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변.

## 다음

**활성 계획 0 — 다음 반복은 계획 phase 다.** 후보 탐색은 이 반복에서 하지 않았다
(`digest ## 다음 계획 후보` 두 절이 그대로 있고, 계획 63 이 소비한 `[6]` 은 테스트 phase
가 이미 취소선으로 닫았다). 계획 63 테스트 phase 가 등재한 `[5]`(`APPEND_TARGETS`)·
`[4]`(`ARCHIVE`)는 8점 미만이라 여는 조건이 올 때까지 후보 절에 둔다.

## 한도

- 병합은 사람 몫이다 — 계획 57~63 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`), 문서는 `mktemp -d` 복사본.
  워킹트리는 변이 열두 판·문서 편집 여덟 판 내내 `git status --porcelain` 빈손이었다.
- `docs/digest.md` 는 **200줄 정각**이다 — 완료 한 줄을 더하면서 가장 오래된 완료 항목
  하나(계획 57 `passage-cost-axis` · 원본 `plan_history_043.md`)를 지워 정각을 지켰다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_065.md` 다.
