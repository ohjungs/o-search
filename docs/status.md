---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 382
updated: 2026-09-06
ctx: 48
night_iterations: 187
night_red: 2
night_retries: 4
plan: readme-shape-cover — 계획 66 (계획 완료 · 설계 생략 · 다음은 개발 1/1)
---

## 현재 상태

**계획 66 `readme-shape-cover` 를 등재했다.** 계획서는 `docs/plan_readme-shape-cover.md` 다.
계획 65 가 닫은 것은 「README 에 적힌 아홉 수치가 `e2e/*.py` 상수와 같은가」 한 축이고,
**표 자신의 «모양»** — 행이 늘어나는 것과 셋째 칸이 실재하지 않는 파일을 가리키는 것 —
은 오늘도 아무도 안 잰다. `digest [7]` 의 ①·④ 를 한 계획으로 묶는다(digest 자신이
「같은 「표 구조」 축이라 한 계획으로 묶는 편이 싸다」로 적어 뒀다).

**닫을 것 둘.**
① README 「잘하고 있나 재는 자」 표에 **여덟 번째 행을 끼워도 조용하다** — `QUALITY_BAND`
는 리터럴 아홉 줄이라 자기가 모르는 행을 셀 방법이 없고, 새 합격선은 **대조 없이** 들어온다.
④ 표의 **셋째 칸(측정기 파일 이름)이 실재하는지 아무도 안 잰다** — 임포트하는 것은 튜플
자신의 셋째 원소(`"quality_eval"` 리터럴)이지 README 의 칸이 아니고, `E2E_COUNT` 대조는
파일 **개수**만 센다. **이 파일이 존재하는 이유(『README 가 없는 모듈 `websearch.cli` 를
안내한 채 푸시됐다』)와 정확히 같은 모양의 구멍**이다.

## 착수 탐침 — 두 구멍이 오늘도 살아 있다

저장소 밖 사본(`.git`·`data/` 제외)에 편집을 **실물 파일로** 심었다. 워킹트리는 무변경이고
(`git status --porcelain` 빈손) 러너에 리다이렉션·파이프는 0회다. 매 판
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.

| 판 | 무엇을 심었나 | 결과 |
|---|---|---|
| **기준선** | 저장소 원본 · 전수 | `Ran 623 tests in 15.724s` · `OK` · rc 0 |
| **M0** | 사본 무변이 · `test_readme.py` | `Ran 6` · `OK` · rc 0 (오탐 0) |
| **U1** | 표에 `\| 새 축 \| 뭔가 7배 이상 \| e2e/design_check.py \|` 추가 | `Ran 6` · `OK` · rc 0 — **생존** |
| **U2** | 셋째 칸 `quality_eval` → `quality_evals` 오타 | `Ran 6` · `OK` · rc 0 — **생존** |

**전수는 기준선 한 판만 돌렸다.** U1·U2 가 건드리는 것은 README 텍스트뿐이고 그것을 읽는
단언은 `tests/test_readme.py` 에만 있어 `-p test_readme.py` 6건으로 충분하다(계획 65 e2e 도
같은 이유로 `Ran 6` 으로 쟀다).

**digest 의 처방 한 줄을 정정했다.** `[7]①` 은 처방을 「표 행 수를 `len(QUALITY_BAND)` 와
대조」로 적어 뒀는데 **그대로는 성립하지 않는다** — 표는 **일곱 행**이고 밴드는 **아홉**이다
(첫 행과 마지막 행이 각각 수치 둘을 담는다). 상수 `7` 을 적는 안은 그것이야말로 거울이라,
방향을 「각 행이 밴드 하나 이상에 물리는가」로 바꿔 적었다. **진단은 옳았고 처방이 그때의
추정이었다** — `digest [7]`(「기록된 답을 실행 전에 다시 재라」)의 세 번째 사례다.

**기점을 `origin/main` 으로 다시 쟀다.** 사람이 `bff2580` 로 병합해 `QualityBandTest` 는
이미 `main` 안에 있다(`git show origin/main:tests/test_readme.py | grep -c QUALITY_BAND` → 2 ·
`git diff --stat origin/main HEAD -- tests/test_readme.py README.md` **빈손**). 계획 58 이
「기점은 `main` 이 아니라 아카이브 커밋」으로 판단했던 근거는 오늘 안 쓴다.

## 1~5순위도 그대로 쟀다

전수 맨몸 `Ran 623 tests in 15.724s` · `OK` · rc 0 · 린터/타입체커 설정 파일 **0개** ·
`TODO`/`FIXME`/`HACK` 이 `src/`·`tests/`·`e2e/` 에 **1건**인데 `tests/test_indexer.py:759`
의 **파서 입력 문자열 안**(계획 65 와 같은 건) · `docs/candidates.md` 부재 ·
`docs/patches/` 부재 · `digest ## 보류 (승인 대기)` **0건**(본문이 통째로 HTML 주석) ·
활성 계획 0. **`gh` 는 한 번도 안 불렀다** — 이번 반복의 하드 제약이라 이슈 목록은 안 쟀다.

## 설계 생략

**트리거 0.** 새 모듈·파일 0(기존 `tests/test_readme.py` 안) · 공개 인터페이스 0 ·
데이터 구조·스키마 0 · 파일 **2개**(`tests/test_readme.py` · `README.md` 의 건수 한 줄) ·
되돌리기 쉬움. **대안이 안 갈린다** — digest 처방(행 수 대조)은 7≠9 로 성립하지 않고,
상수 7 을 적는 안은 거울이라 값이 0 이다. 남는 갈래가 하나다.

## 검증

- 문서를 고친 **뒤** 전수 맨몸 **`Ran 623 tests in 15.895s` · `OK` · rc 0**
  (리다이렉션·파이프 0회 · 판정 줄을 눈으로 봤다). 착수 탐침의 기준선도 같은 명령으로
  `Ran 623 tests in 15.724s` · `OK` · rc 0 이었다.
- 네 동기 가드 별도 재실행 — `IterationSyncTest`·`StepSyncTest`·`StepGapTest`·
  `ArchiveIndexTest` **`Ran 8` · `OK` · rc 0**(`metrics.md` 반복 382 ↔ `status.md`
  `iteration: 382` · `index.md` 새 행 `0/1` ↔ `step: 0/1`).
- 착수 탐침 **총 4판**(전수 1 · `test_readme.py` 3). 항목당 1판이고 상한 6 안이다.
- 범위 무접촉: 제품 `src/`·`e2e/` **0줄** · `README.md` 무변 · `docs/specs/` 읽기만 ·
  `data/crawl.db` 무변경 · 재색인 0회 · 스키마 0 · 새 의존성 0 · PR #7 무접촉(`gh` 호출 0).
- 러너 규율 위반 **0회**(누적 38 유지).

## 다음

**개발 1/1** — `tests/test_readme.py` 의 `QualityBandTest` 다음(그리고
`if __name__ == "__main__"` 가드 **앞**)에 `BandTableShapeTest` 를 붙인다. 셋을 넣는다:
표 데이터 행을 제목으로 잘라내는 정규식 하나 · 각 행이 `QUALITY_BAND` 정규식 하나 이상에
걸리는지 보는 커버 단언 · 셋째 칸 경로를 뽑아 `(README.parent / 경로).is_file()` 로 거는
실재 단언(`〃` 는 건너뛰지 말고 **윗 행 경로를 이어받는다**). 전수가 623 → **625** 가 되므로
`README.md:104` 의 건수 한 줄을 **같은 커밋에서** 고친다.

## 한도

`docs/digest.md` 200줄 정각 유지(이번 반복에 한 줄도 안 더했다) ·
`docs/history_current.md` 는 7항목 / 상한 20, **287줄 / 상한 300** — 이번 반복은 회전 미달이나
다음 반복이 한 항목만 더 붙여도 넘는다. **다음 반복의 집안일은 회전이다.**
