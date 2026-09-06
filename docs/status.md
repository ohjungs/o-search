---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 377
updated: 2026-09-06
ctx: 52
night_iterations: 187
night_red: 2
night_retries: 4
plan: readme-band-cover 계획 65 (계획 완료 · 설계 생략 · 다음은 개발 1/1)
---

## 현재 상태

**YELLOW 를 풀고 계획 65 `readme-band-cover` 를 등재했다.** 반복 376 이 물은 셋 중
사람이 **①(여섯 번째 문서 하네스 허용)만** 열었다 — ②(`digest ## 판단 필요` 개방)와
③(`docs/specs/` 방향 기입)은 **열리지 않았고**, 보안·재색인·스키마 게이트는 그대로 닫힘이다.
그래서 이번 반복은 **탐색을 다시 돌리지 않는다.** 사용자 지시가 곧 근거다
(`rules/discover.md` 0절). 계획서는 `docs/plan_readme-band-cover.md` 다.

**닫을 것.** `README.md` 「잘하고 있나 재는 자」 표의 **아홉 수치**(상위 10 · 80% · 90% ·
0.3초 · 0.5초 · 초당 5장 · JS 50KB · 대비 4.5 · 비텍스트 3)가 `e2e/*.py` 상수의 복제인데
둘을 대조하는 단언이 **0개**다. 값은 오늘 아홉이 전부 맞다 — 결함은 **대조의 부재**다.

## 지시 모드에서도 그대로 잰 것

`rules/discover.md` 0절이 지시 모드에서도 요구하는 셋을 다 통과시켰다.

- **중복 방지**: 활성 계획 0 · `digest ## 보류 (승인 대기)` 0건(본문이 통째로 HTML 주석) ·
  `docs/patches/` 부재 · `docs/candidates.md` 부재. `digest` 의 `test_readme.py` 항목
  **`[5]`** 은 `RUNNER_LINE`·`BUFFERED` 의 **거짓 RED 방향 둘**이라 이 계획과 안 겹친다.
- **`rules/plan.md` 전부**: 스텝 분할(1개) · 검증 가능한 완료 기준(10개) · 「하지 않을 것」 6줄.
- **`design.md` 트리거**: 0개 — 아래 「설계 생략」.

**탐색은 안 했지만 1~5순위는 그래도 쟀다.** 전수 맨몸 `Ran 622 tests in 15.828s` · `OK` ·
rc 0 · 린터/타입체커 설정 파일 0개(최상위는 `.gitignore` 하나) · `TODO`/`FIXME`/`HACK` 이
`src/`·`tests/`·`e2e/` 에 1건인데 `tests/test_indexer.py:759` 의 **파서 입력 문자열 안** ·
`gh issue list --state open` 0건 rc 0.

## 착수 탐침 — 반복 376 의 기록이 절반 틀렸다

저장소 밖 사본에서 변이 열셋을 각각 전수로 돌렸다(워킹트리 무변경 · 리다이렉션 0).
대조군 M0 는 사본에서도 `Ran 622` · `OK` · rc 0 이다.

| 변이 | README 의 어느 수치 | 죽은 단언 |
|---|---|---|
| M1 `quality_eval.THRESHOLD` 80→85 | 「맞는 게 80% 이상」 | 1 |
| M2 `quality_eval.TOP_N` 10→5 | 「10개 중에」 | 1 |
| M3 `passage_eval.ACCURACY` 90→95 | 「문단의 90% 이상」 | **0 생존** |
| M4 `perf_search.BUDGET_MS` 300→400 | 「0.3초 안에」 | **0 생존** |
| M5 `passage_eval.BUDGET_MS` 500→700 | 「0.5초 안에」 | **0 생존** |
| M6 `perf_crawl.TARGET_RATE` 5.0→8.0 | 「1초에 5장 이상」 | **0 생존** |
| M7 `design_check.JS_BUDGET` 50→80KB | 「JS 50KB 이하」 | **0 생존** |
| M8 `design_check.MIN_CONTRAST` 4.5→3.0 | 「4.5배 이상」 | 1 |
| M9 `design_check.MIN_CONTRAST_NONTEXT` 3.0→2.0 | 「(글씨 아닌 것은) 3배」 | 2 |
| **R1·R2·R3** README 쪽 세 수치를 비틀기 | 문서 쪽 | **0/3 전부 생존** |

**정정 셋** (`digest [7]` 「기록된 답을 실행 전에 다시 재라」의 다음 적용):
① 수치는 **일곱이 아니라 아홉**이다(첫 행이 둘, 마지막 행이 둘을 담는다).
② **상수 축은 무가드가 아니다** — 넷(M1·M2·M8·M9)은 `test_quality_eval`·`test_design_check`
가 경계 판정으로 이미 문다. 「고쳐도 아무도 안 운다」는 다섯에서만 참이다.
③ **그러나 문서 축은 아홉이 다 열려 있다** — R1·R2·R3 이 3/3 생존한다. 상수를 물고 있는
넷조차 README 와는 안 묶여 있다. **닫을 축은 「상수가 움직이나」가 아니라 「문서와 상수가
같은가」다.**

**세 번째 사본**은 `docs/specs/concept.md` 이고(상수 주석이 줄번호로 인용한다), 오늘
사양·상수·README 셋이 전부 일치하는 것은 눈으로 확인했다. 그 축은 계획 5절에서 안 연다.

## 설계 생략

**트리거 0** — 새 파일 0(기존 `tests/test_readme.py` 안) · 공개 인터페이스 무변 ·
데이터 구조 변경 0 · 파일 2개 · 커밋 하나로 revert. 대안도 안 갈린다: e2e 상수를
임포트해 읽는 길은 `tests/test_design_check.py`·`tests/test_quality_eval.py`·
`tests/test_passage_eval.py` 가 **이미 세 번 고른 관용구**이고(사다리 2번), 소스를
정규식으로 파싱하는 안은 `50 * 1024` 같은 식을 다시 계산해야 해서 더 크고 더 약하다.
다섯 모듈 동시 임포트는 오늘 **부작용 0 · 0.138초**로 쟀다.

## 검증

- 전수 **맨몸**(리다이렉션·파이프 0) `Ran 622 tests in 15.828s` · `OK` · **rc 0**.
- 변이 열셋은 **저장소 밖 사본에서만** — 실물 `src/`·`e2e/`·`README.md`·`docs/specs/`·
  `data/` **0줄**. `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 재색인 0회.
- 기점 `535e8fc` 는 원격과 같다(`git ls-remote origin loop/passage-cost-band`).

## 다음

**개발 phase — 스텝 1/1.** `QualityBandTest` 를 `ReadmeCommandsTest` 아래에 세운다
(아홉 줄 리터럴 표 + 대조 단언). 완료 기준 10개는 계획서 4절에 있다. 제품 `src/` **0줄** ·
`e2e/` **0줄**. 메서드가 늘면 `README.md` 의 「단위 N건」을 **같은 커밋에서** 함께 고친다.

## 한도

- 병합은 사람 몫이다 — 계획 57~65 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 이번 반복도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- **`night_iterations` 는 187 그대로 둔다** — 이 반복은 대화형이라 야간 예산을 안 쓴다.
- `docs/digest.md` 는 **200줄 정각**이라 이번에도 한 줄도 안 더했다 — 오늘 남길 정정은
  계획서 2절과 `history_current.md` 가 진다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_066.md` 다.
