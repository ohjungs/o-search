---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 380
updated: 2026-09-06
ctx: 58
night_iterations: 187
night_red: 2
night_retries: 4
plan: readme-band-cover 계획 65 (리뷰 1/1 완료 · low 2건 자동 수정 · 다음은 e2e)
---

## 현재 상태

**백지 패스가 후보 셋을 냈고, 둘을 고치고 하나를 버렸다 — 둘 다 low · 단언 무변.**
critical/high **0건**이라 개발 phase 로 안 돌아간다. 고친 것은 계획 65 의 파일
`tests/test_readme.py` 안 두 줄뿐이고 제품 `src/`·`e2e/` 는 **0줄**이다.

**[R65-1] (low · 신뢰도 95 · 자동 수정) 합격선 비교가 «맞는데도 빨개지는» 축을 갖고 있었다.**
`assertEqual(Decimal(found[0]) * scale, actual)` 의 오른쪽이 **float 상수**라, 이진 정확값이
아닌 합격선에서는 문서와 상수가 **완전히 일치해도** RED 다(`Decimal('5.1') != 5.1`).
`decimal.Decimal(str(actual))` 한 줄로 양쪽을 십진으로 재웠다.

**[R65-2] (low · 신뢰도 85 · 자동 수정) 파일 docstring 이 이 diff 로 거짓이 됐다.**
「`find_spec` 은 모듈을 임포트하지 않고 찾기만 한다」가 파일 전체의 비용 주장으로 읽히는데,
새 `QualityBandTest` 는 `e2e/*.py` 다섯을 **실제로 임포트**한다(그 아래로 `websearch.indexer`·
`serve`·`crawl` 까지). 두 검사의 비용이 다르다는 것을 문장으로 갈랐다 — 네트워크·서브프로세스
0 은 그대로이고, 임포트 시점에 상수만 서고 서버도 DB 도 안 연다는 것을 직접 읽어 확인했다.

**버린 후보 하나(80점 미만).** status 의 「`history_current.md` 는 회전 직후 128줄」이 실물
168줄과 어긋난다 — 계획 61 `[R61-1]` 과 같은 자리로 보였으나, 그 문장은 **「회전 직후」로
한정**되어 있어 참이고 회전 판단(상한 300)도 안 뒤집는다. 신뢰도 60 으로 버린다.
(이번 status 는 append 뒤의 실수를 아래 「한도」에 적는다.)

## 검증 — 앞 phase 가 「했다」고 적은 것을 직접 다시 걸었다

계획·status 를 열기 전에 diff 만 보는 패스 A 를 먼저 끝냈다. 변이는 전부 **저장소 밖
사본**(`src`·`tests`·`e2e`·`docs`·`README.md` 만 tar 복사 · `.git`·`data/` 없음)에서
돌렸고 `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 매 판 줬다.

| 변이 | 반복 378·379 가 적은 값 | 리뷰 재측 | 죽은 자리 |
|---|---|---|---|
| M0 무변이 대조군 | 0 | **0** (`Ran 623` `OK` rc 0) | 오탐 0 |
| M3 `passage_eval.ACCURACY` 90→95 | 1 | **1** | `band='문단 정확도 %'` |
| M4 `perf_search.BUDGET_MS` 300→400 | 1 | **1** | `band='검색 예산 초'` |
| M5 `passage_eval.BUDGET_MS` 500→700 | 1 | **1** | `band='문단 예산 초'` |
| M6 `perf_crawl.TARGET_RATE` 5.0→8.0 | 1 | **1** | `band='크롤 속도 장/초'` |
| M7 `design_check.JS_BUDGET` 50→80KB | 1 | **1** | `band='JS 예산 KB'` |
| R1 README 「80%」→「55%」 | 1 | **1** | `band='검색 합격선 %'` |
| R2 README 「0.3초」→「9.9초」 | 1 | **1** | `band='검색 예산 초'` |
| R3 README 「JS 50KB」→「500KB」 | 1 | **1** | `band='JS 예산 KB'` |

**아홉 줄이 한 자도 안 움직였다.** 죽는 자리가 전부 `subTest` 라벨까지 맞고, 예산 두 행이
서로 안 섞인다(R2 는 `검색 예산 초` 만, M5 는 `문단 예산 초` 만). 계획서 4절 완료 기준
1~8 을 앞 phase 의 기록이 아니라 **오늘의 실행**으로 다시 통과시켰다.

**수정 뒤 같은 아홉을 다시 돌렸다 — 아홉 다 그대로 죽는다.** 단언을 낮추지 않았다는 증거가
건수가 아니라 **자리**로 붙는다(라벨 아홉이 재측 전후 동일).

## 등재된 갭 둘도 다시 걸었다 — 하나는 재현, 하나는 **판정이 틀렸다**

**[7]① 「표에 행을 더해도 조용하다」는 재현된다.** README 표에 `| 새 축 | 뭔가 7배 이상 |
e2e/design_check.py |` 를 끼운 판이 `Ran 623 · OK · rc 0 · 죽은 단언 0`. 열어 둔다.

**[7]② 「오늘 아홉은 다 이진 정확이라 잠복」은 틀렸다 — 도달 가능이었다.**
테스트 phase 는 4.5→4.6(README·상수 함께)으로 재고 거짓 RED 1건을 봤는데, 그 판은
`test_design_check.ContrastAxisTest` 의 **4.5 못이 함께 죽는** 자리라 「일치 상태」가 아니다.
못이 없는 축에서 다시 걸었다 — `perf_crawl.TARGET_RATE` 5.0→**5.1** 과 README 「1초에
**5.1**장」을 함께 옮긴 **완전 일치 상태**:

| 판 | 결과 | 죽은 자리 |
|---|---|---|
| 수정 전 · 일치 5.1 | **RED** rc 1 | `band='크롤 속도 장/초'` ← **거짓 RED 가 유일한 실패** |
| 수정 후 · 일치 5.1 | `Ran 623` `OK` rc 0 | — |
| 수정 후 · 불일치 5.1 vs 5.0 | **RED** rc 1 | `band='크롤 속도 장/초'` ← 진짜 갈림은 그대로 문다 |

「여는 조건(비정확 값으로 옮기는 날)을 기다린다」가 성립하지 않는 이유가 여기 있다 —
**합격선은 튜닝으로 움직이고, 튜닝은 이진 정확값을 골라 주지 않는다.** 그리고 거짓 RED 는
가장 나쁜 종류다: 맞는 변경을 한 사람이 자를 의심하게 만든다. `digest [7]②` 는 닫았고,
①(표 구조 축)과 ③(`docs/specs/concept.md` 미결속)은 그대로 열어 뒀다.

## 계획 대조 (패스 B)

- 완료 기준 **10/10**. 1~5(M3~M7 각 1건 이상) · 6(R1~R3 3/3) · 7(README 아홉 ↔ 상수 아홉
  일치) · 8(이미 물던 넷이 증강) · 9(README 「단위 623건」 갱신) · 10(전수 `Ran 623` `OK` rc 0).
- 계획 5절 범위 준수: 제품 `src/` **0줄** · `e2e/` **0줄** · 새 e2e 파일 0 · 의존성 추가 0
  (`decimal`·`sys` 는 stdlib) · 스키마·마이그레이션 0 · `docs/specs/` **`git diff --stat` 0줄**.
- 계획이 미룬 `[5]`(`RUNNER_LINE`·`BUFFERED` 의 RED 방향)은 오늘도 안 건드렸다 — 직교 편집.
- 렌즈 5(주석의 지침): `e2e/perf_crawl.py:53` 의 「제품 목표라 여기 맞춘다 — 올리지 않는다」를
  변이로만 건드렸고 저장소 안 값은 무변이다.

## 검증

- 저장소 안 전수는 **맨몸**(리다이렉션·파이프 0)으로 두 판 — 수정 전 `Ran 623 tests` `OK`
  **rc 0**, 수정 후 `Ran 623 tests` `OK` **rc 0**. 격리 `-p test_readme.py` 도 `Ran 6` `OK` rc 0.
- 변이 열둘은 **저장소 밖 사본에서만** 돌았고, 도는 내내 `git status --porcelain` 은
  `tests/test_readme.py` 한 줄뿐이었다(계획 33~41 의 「제자리 변이를 자동 스냅샷이 커밋한다」 처방).
- `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 재색인 0회 · `docs/specs/` 읽기만 ·
  PR #7 무접촉(`gh` 호출 0) · `main` 무접촉 · 러너 위반 0(누적 38 유지).
- 고친 파일은 `tests/test_readme.py`(두 줄) + 기록 다섯(`status.md`·`history_current.md`·
  `digest.md`·`index.md`·`metrics.md`)뿐이다. 회전은 없다.

## 다음

**e2e phase.** 제품이 0줄이라 `rules/e2e.md` 3절 면제를 근거 셋으로 다시 재는 것이 첫 일이고,
그다음이 완료 기준 10/10 확인과 계획 65 닫기다. 열려 있는 갭은 `digest [7]①`(표 행 수)과
`[7]③`(`concept.md` 축) 둘뿐이며 둘 다 8점 미만이라 이 계획에서 안 연다.

## 한도

- 병합은 사람 몫 — 계획 57~65 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉.
- `--force`·`--amend`·`rebase` 없음. 스텝 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 이번 반복도 위반 **0회**(누적 38 유지). 변이 배터리는
  저장소 밖 파이썬 하네스가 `Ran`·판정·rc·실패 이름을 그대로 찍어 눈으로 봤다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `night_iterations` 는 187 그대로다(대화형 반복이라 안 올린다).
- `docs/history_current.md` 는 이번 append **뒤 209줄**이다(상한 300 · 항목 5개/20) —
  다음 회전은 아직 아니다.
