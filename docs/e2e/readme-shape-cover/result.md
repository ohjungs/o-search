# e2e 결과 — 계획 66 `readme-shape-cover` (반복 386 · 2026-09-06)

**판정: 통과 — 전수 `Ran 625 tests in 15.899s` · `OK` · rc 0 · 대조군 판 3/3 기대대로 → DONE.**
**이번 phase 는 예산이 하드했다** — 같은 계획의 리뷰 스텝에서 앞선 두 시도가 변이 실험에
들어가 산출물 없이 48분·39분 정지했다(`digest ## 반복 실패` 2회 등재). 그래서 **전수 1회 ·
변이 2판**으로 못박고 들어와 그 안에서 끝냈다.

## 0. 면제 — 새 e2e 를 안 만들고, 21종 재실행도 안 한다 (`rules/e2e.md` 3절)

계획 61~65 와 같은 자리다. 「해당 없음」으로 넘기지 않고 **오늘 실측으로 근거를 댄다.**

1. **프로세스 밖에서 달라진 것이 0.** 계획 66 직전(`3566374`)부터 `HEAD` 까지
   `git diff --stat 3566374 HEAD -- src/ e2e/ docs/specs/ data/` 가 **빈손**(무출력 · rc 0)이다.
   이 계획이 움직인 파일은 `tests/test_readme.py`(`BandTableShapeTest` 하나)와 `README.md`
   건수 한 줄(623→625), 그리고 기록 문서들뿐이라 HTTP 응답·CLI stdout·exit code·DB 스키마
   중 무엇도 어제와 다르지 않다.
2. **산출물이 제품 경로에서 도달 불가능하다.** `src/` 에 `tests` 를 import 하는 줄은 0건이고,
   새 검사가 읽는 것은 `README.md` 텍스트와 `(README.parent / 경로).is_file()` 뿐이다.
3. **전체 명령이 이미 집어간다.** 새 파일을 만들면 `unittest discover -b -s tests` 와 겹쳐
   「1회만」이 깨진다(`rules/e2e.md` 1절).

**새 e2e 파일 0개** — `ls e2e/*.py` 는 어제와 같은 **21개**고 `README.md:105` 의
「e2e 시나리오 21종」이 그대로 맞다. **21종 개별 재실행도 0회다** — 계획 65 e2e(반복 381)가
21/21 rc 0 을 실측했고 그 뒤로 `src/`·`e2e/`·`data/` diff 가 빈손이라 **재실행이 살 값이 0**
이다(리뷰 385 가 같은 판정을 이미 냈다). 재실행하지 않은 것을 「통과」로 적지 않는다 —
위 diff 가 그 자리의 증거고, 오늘 산 것은 전수와 대조군 판이다.

## 1. 전수 — `Ran 625` · `OK` · rc 0 (1회)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src \
  python3 -m unittest discover -b -s tests
Ran 625 tests in 15.899s
OK
rc=0
```

맨몸으로 돌렸다 — 파이프·리다이렉션 **0회**(`docs/project.md` 「명령」 절 규율).
문서 동기 가드 넷(`IterationSyncTest`·`StepSyncTest`·`StepGapTest`·`ArchiveIndexTest`)도
이 625 안에 있다.

## 2. 대조군 판 — 실물 사본에 사람이 낼 편집 둘 (변이 2판)

저장소(`src`·`tests`·`e2e`·`docs`·`README.md`)를 `mktemp -d` 아래로 복사하고 **복사본만**
고친 뒤 그 안에서 `python3 -m unittest -b tests.test_readme` 를 진짜 서브프로세스로 돌렸다.
매 판 `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 줬고,
심기 전에 **앵커 줄이 정확히 1개인지 먼저 단언**했다(`digest [8]` 의 BSD `sed` 거짓 초록 대응 —
오늘은 `sed` 가 아니라 파이썬 줄 편집이다). 끝난 뒤 저장소 `git status --porcelain` **빈손**.

| # | 편집(사람이 낼 법한 것) | 판정 줄 | 가드가 낸 말 |
|---|---|---|---|
| U0 | 손 안 댐 (성한 원본) | `Ran 8 tests in 0.157s` · `OK` · **rc 0** | — (오탐 0) |
| U1 | 표에 여덟 번째 행을 끼움 — `\| 새 축인가 \| 뭔가 7배 이상 \| \`e2e/design_check.py\` \|` | `FAILED (failures=1)` · **rc 1** | `test_every_band_row_is_covered` (row=…새 축인가…) — 「이 행의 합격선을 `QUALITY_BAND` 가 아무것도 안 잰다」 |
| U2 | 셋째 칸 개명 오타 — `` `e2e/quality_eval.py` `` → `` `e2e/quality_evals.py` `` | `FAILED (failures=1)` · **rc 1** | `test_every_band_row_names_an_existing_meter` — 「표가 가리키는 측정기가 없다: e2e/quality_evals.py」 |

**이 두 판이 계획 66 이 열려고 한 구멍 정확히 둘이다** — 착수 탐침(반복 382)에서 **둘 다
`Ran 6 · OK · rc 0` 으로 생존**했던 편집이고, 오늘 같은 편집이 **각각 1건씩 죽는다.**
그리고 **서로 다른 단언에서** 죽는다(커버 축 / 실재 축) — 한 단언이 둘을 다 덮어 라벨이
뭉개지는 모양이 아니다. `subTest` 라벨에 **문제의 행 원문이 통째로** 찍혀 어느 줄을
고쳐야 하는지가 화면에 있다.

**U1 은 셋째 칸을 실재하는 파일(`e2e/design_check.py`)로 뒀다** — 그래야 죽는 것이 커버
단언 하나임이 증명된다. 실재하지 않는 이름을 썼으면 두 단언이 함께 울어 어느 쪽이
잡았는지 못 가른다.

**U0 이 반대 방향이다** — 성한 원본에서 새 단언 둘을 포함해 `Ran 8` 이 전부 초록이라
오탐이 0 이다. 계획 65 e2e 가 잰 「정당한 편집은 안 막는다」 축(U4·U6)은 오늘 다시 안 샀다 —
그 축은 값 대조 쪽이고 오늘 넣은 둘은 모양 대조라 겹치지 않으며, 예산 안에서 살 값이 있는
것은 **생존→사망이 뒤집혔는가** 하나였다.

## 3. 완료 기준 — 오늘 실행으로 다시 쟀다

| # | 기준 | 실측 | 판정 |
|---|---|---|---|
| 1 | U1(README 표에 행 하나 추가)이 1건 이상 죽는다 | `failures=1` · rc 1 · `test_every_band_row_is_covered` | 충족 |
| 2 | U2(셋째 칸을 없는 파일로 개명)가 1건 이상 죽는다 | `failures=1` · rc 1 · `test_every_band_row_names_an_existing_meter` | 충족 |
| 3 | U3(표 잘라내기 정규식 사망 = 빈 목록 위 침묵 금지)가 1건 이상 죽는다 | 개발·테스트 phase 실측(반복 383·384). `setUp` 의 `assertTrue(block…)`·`assertTrue(self.rows…)` 두 단언이 그 자리고, 오늘 정적 대조로 재확인(구분 줄 3개 중 합격선 표 하나를 잘라 데이터 행 7) | 충족 |
| 4 | ~~U4 판정 무력화~~ → **U4′**: 무력화를 U1 편집과 **함께** 심으면 생존 | 개발 383 · 테스트 384 실측 (`Ran 8 · OK · rc 0`). 성한 트리 위 단독 무력화는 죽을 것이 없어 기준으로 성립하지 않는다 — 계획 4절이 이미 정정 | 충족(정정된 형태로) |
| 5 | M0 오탐 0 — 오늘 트리에서 단언 둘이 통과 | U0 `Ran 8 · OK · rc 0` · 전수 `Ran 625 · OK · rc 0` | 충족 |
| 6 | `QualityBandTest` 아홉 축 무회귀 | 전수 625 안에서 초록. 리뷰 385 가 아홉 정규식을 README 원문에 태워 행별 인덱스 `[0,1] [2] [3] [4] [5] [6] [7,8]` 로 확인(커버 안 되는 행 0 · 안 걸리는 밴드 0) | 충족 |
| 7 | 전수 `Ran 625` `OK` rc 0 · 동기 가드 넷 OK | 1절 그대로 | 충족 |
| 8 | `README.md:104` 건수가 실제와 일치 | 「단위 625건」 ↔ `Ran 625` · 「e2e 21종」 ↔ `ls e2e/*.py` **21** | 충족 |

**범위도 다시 쟀다**: `git diff --stat 3566374 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` **무변**(계획 65 e2e 가 적은 값과 한 자도 안 다르다) ·
재색인 0 · 스키마 0 · 새 의존성 0(stdlib).

## 4. e2e 가 잡은 것 — 0건

diff 의 주장을 실물과 다시 대조해 어긋난 곳이 없었다. 계획 65 e2e 가 계획서의 「안 잰다」
근거 한 줄을 뒤집었던 것과 달리, 이번 계획서의 배제 목록(둘째 칸 문구 · 다른 두 표 ·
`concept.md` 세 번째 사본 · `digest [5]`)은 오늘 실측에서 하나도 안 흔들렸다.

**남기는 관찰 하나 — 이 phase 가 산 것과 안 산 것.** 오늘 전수와 대조군 두 판으로
「생존→사망」이 뒤집힌 것을 샀고, **21종 개별 재실행과 기준선 8축 표는 안 샀다**(0절).
그 값이 살아나는 조건은 `src/`·`e2e/` diff 가 빈손이 아니게 되는 날이다.

## 5. 한도 — 지킨 것

- **러너 규율 위반 0회(누적 38 유지).** 전수 1회와 사본 3판(U0·U1·U2)을 전부 맨몸으로
  돌렸고 판정 줄(`Ran … / OK / FAILED / rc`)을 매번 눈으로 확인했다.
- **편집은 저장소 밖에서만** — `mktemp -d` 사본. 끝난 뒤 `git status --porcelain` 빈손.
  실물 `README.md`·`e2e/*.py`·`src/` 는 이 phase 에서 **0줄** 움직였다.
- **예산** — 도구 호출 25회 이내 · 전수 1회 · 변이 2판. 앞선 두 시도가 여기서 정지한
  자리라 상한을 먼저 정하고 들어왔다.
- `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0(stdlib) · `docs/specs/` 읽기만.
- 원격 `loop/passage-cost-band` 위에 오늘 커밋을 쌓는다. `main` 직접 커밋 0 ·
  PR #7 무접촉(`gh` 호출 **0회**) · `--no-verify`·`--force`·`--amend`·`rebase` **0회**.
  병합은 사람 몫이다.
- 도구 산출물 없음 — 브라우저 도구를 쓰지 않는 프로젝트라 `test-results/` 에 해당하는
  경로가 없다. 위 표의 판정 줄이 실행 출력 전부다.
