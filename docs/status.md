---
signal: GREEN
phase: 개발
step: 1/1
attempt: 0
iteration: 378
updated: 2026-09-06
ctx: 58
night_iterations: 187
night_red: 2
night_retries: 4
plan: readme-band-cover 계획 65 (개발 1/1 완료 · 완료 기준 10/10 · 다음은 테스트)
---

## 현재 상태

**계획 65 의 한 스텝을 닫았다.** `tests/test_readme.py` 에 `QualityBandTest` 가 서서
`README.md` 「잘하고 있나 재는 자」 표의 **아홉 수치**를 `e2e/*.py` 의 실제 상수와 대조한다.
파일 머리에 아홉 줄 리터럴 표 `QUALITY_BAND`(이름 · README 에서 수치만 뽑는 정규식 ·
모듈 · 상수 · 환산 배율)를 두고, 메서드 하나가 `subTest` 로 아홉을 돈다.
제품 `src/` **0줄** · `e2e/` **0줄** · README 의 수치는 한 글자도 안 움직였다.

**본 축이 뒤집혔다.** 어제 README 쪽 변이 R1·R2·R3 은 **0/3 생존**이었는데 오늘 **3/3 사망**이다.
문서만 고쳐도, 상수만 고쳐도 빨개진다.

## 어떻게 지었나

- **문구가 아니라 수치를 잰다.** 표에 `51200` 을 적으면 README 의 「50KB」가 바뀌어도 안 울고,
  문구를 통째로 적으면 문구를 다듬는 날 표도 같이 고쳐져 **거울**이 된다(계획 62 e2e 가 잡은
  자리가 정확히 그것이다). 그래서 정규식은 숫자만 잡고 환산(초→ms · KB→B)은 단언이 곱한다.
- **곱셈은 `decimal.Decimal` 로 한다.** `0.3 * 1000` 이 부동소수라 `300` 과 안 같아지는 갈래를
  아예 없앤다(계획 7절 둘째 위험). 상수 쪽 `5.0`·`4.5`·`3.0` 은 이진에서 정확해 비교도 정확하다.
- **정규식이 죽으면 대조가 빈손 위에서 조용히 통과한다.** 그래서 각 행이 「정확히 하나」를
  단언한다 — 0개(문구가 바뀜)도 2개 이상(어느 것을 잰 것인지 모름)도 실패다.
  「95번은 N초」는 두 행에 있어 행 머리(`| 빠른가 |` · `| 문단도 빠른가 |`)로 갈랐다.
- **새로 만든 구조 0.** `sys.path.insert` 로 e2e 모듈을 이름으로 임포트하는 관용구는
  `test_design_check.py`·`test_quality_eval.py`·`test_passage_eval.py` 가 이미 세 번 썼다
  (사다리 2번). 다섯 모듈 임포트 비용 **0.116초** · 부작용 0.

## 완료 기준 10/10

저장소 밖 사본에서 변이 열셋을 각각 전수(623건)로 돌렸다. 워킹트리 무변경 · 리다이렉션 0.

| 변이 | 어제 | 오늘 |
|---|---|---|
| M0 무변이 대조군 | 0 | **0** (오탐 0 · `Ran 623` · `OK` · rc 0) |
| M3 `passage_eval.ACCURACY` 90→95 | 0 생존 | **1** |
| M4 `perf_search.BUDGET_MS` 300→400 | 0 생존 | **1** |
| M5 `passage_eval.BUDGET_MS` 500→700 | 0 생존 | **1** |
| M6 `perf_crawl.TARGET_RATE` 5.0→8.0 | 0 생존 | **1** |
| M7 `design_check.JS_BUDGET` 50→80KB | 0 생존 | **1** |
| M1 `THRESHOLD` 80→85 | 1 | **2** (기존 + 새 단언) |
| M2 `TOP_N` 10→5 | 1 | **2** |
| M8 `MIN_CONTRAST` 4.5→3.0 | 1 | **2** |
| M9 `MIN_CONTRAST_NONTEXT` 3.0→2.0 | 2 | **3** |
| **R1** README 「80%」→「55%」 | **0 생존** | **1** |
| **R2** README 「0.3초」→「9.9초」 | **0 생존** | **1** |
| **R3** README 「JS 50KB」→「500KB」 | **0 생존** | **1** |

기준 7(감지력 무회귀)은 **증강**으로 통과했다 — 기존 `test_quality_eval.TestVerdict`·
`TestGuards`·`test_design_check.ContrastAxisTest` 단언이 그대로 죽고 새 단언이 겹쳐 문다.
실패 메시지는 어느 행·어느 상수인지를 적는다(`band='검색 합격선 %'`).

## 문서 가드가 자기가 늘린 수를 잡았다

메서드가 하나 늘자 `test_verification_counts_match_reality` 가 `(622, 21) != (623, 21)` 로
즉시 빨개졌다. **설계대로다.** 같은 커밋에서 README 「단위 622건」을 623 으로 고쳤다.

## 검증

- 전수 **맨몸**(리다이렉션·파이프 0) `Ran 623 tests in 15.896s` · `OK` · **rc 0**.
- 범위 무접촉: `git diff --stat 535e8fc -- src/ e2e/ docs/specs/ data/` **빈손** ·
  `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 재색인 0회.
- 고친 파일은 둘뿐 — `tests/test_readme.py`(+57) · `README.md`(1줄).
- PR #7 무접촉(`gh` 호출 0) · `main` 무접촉 · 러너 위반 0(누적 38).

## 다음

**테스트 phase — 갭 탐색.** 계획 5절이 남긴 후보 하나가 있다: `docs/specs/concept.md` 가
이 수치들의 **세 번째 사본**인데(`e2e/*.py` 주석이 23·43·44·51·53·115·128·129행을 인용) 그
축은 안 닫혀 있다. 사양은 사람이 고치는 읽기 전용 문서라 이 계획에서 안 열었고, 오늘 셋이
일치하는 것은 눈으로 확인했다. `digest` 후보로 남긴다.

## 한도

- 병합은 사람 몫이다 — 계획 57~65 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉.
- `--force`·`--amend`·`rebase` 없음. 스텝 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 이번 반복도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `night_iterations` 는 187 그대로다(대화형 반복이라 안 올린다).
- `docs/history_current.md` 는 **286줄**(상한 300) — 다음 반복의 append 가 넘기면
  `history_066.md` 로 회전하고 `digest.md` 명부도 함께 채운다(계획 64 e2e 가 명부 누락으로
  대조군이 빨개진 사례가 있다).
