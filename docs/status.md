---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 384
updated: 2026-09-06
ctx: 46
night_iterations: 188
night_red: 2
night_retries: 4
plan: readme-shape-cover — 계획 66 (테스트 1/1 완료 · 다음은 리뷰 phase)
---

## 현재 상태

**계획 66 스텝 1/1 을 테스트했다 — 완료 기준 8/8 통과(4번은 U4′ 로 읽는다).**
개발이 남긴 판정을 받아 적지 않고 **전수 1판 + 변이 8판을 처음부터 다시 쟀다**
(`rules/test.md` 1절 「안 돌렸으면 통과라고 쓰지 않는다」). 제품·테스트 코드 **0줄 변경** —
이번 반복이 고친 것은 문서 다섯뿐이다.

전수 **`Ran 625 tests in 15.851s` · `OK` · rc 0**(맨몸 · 리다이렉션 0회 ·
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest
discover -b -s tests`). 네 동기 가드(`IterationSyncTest`·`StepSyncTest`·`StepGapTest`·
`ArchiveIndexTest`) 포함이다.

## 변이 여덟 판 — 독립 재현, 그리고 한 판이 무효였다

저장소 밖 사본(`src`·`tests`·`e2e`·`docs`·`README.md`)에 실물 파일로 심었다. 각 판
`-p test_readme.py` · `Ran 8` · 매 판 원본에서 복원 후 하나만 심는다.

| 판 | 무엇을 심었나 | 결과 | 판정 |
|---|---|---|---|
| **M0** | 무변이 | `Ran 8` · `OK` · rc 0 | 오탐 0 |
| ~~U1(1차)~~ | 표에 행 추가 — **심는 쪽이 README 를 잘랐다** | `FAILED (failures=3)` | **무효** |
| **U1** | 표에 대조 밖 행 하나 | `test_every_band_row_is_covered` **1건** · rc 1 | 기준 1 ✅ |
| **U4′** | U1 + 커버 판정 `True` 고정 | `Ran 8` · `OK` · rc 0 | **생존 = 귀속 증명** ✅ |
| **U2** | 셋째 칸 → 없는 `quality_evals.py` | `..._names_an_existing_meter` **1건** · rc 1 | 기준 2 ✅ |
| **U3** | 표 제목 개명(잘라내기 죽이기) | `setUp` 에서 **둘 다**(2건) · rc 1 | 기준 3 ✅ |
| **M0b** | 셋째 칸 → 실재하는 `perf_crawl.py` | `Ran 8` · `OK` · rc 0 | 기준 5 ✅ |
| **R1** | 표에서 행 삭제(「잘 주워 오나」) | 기존 `..._bands_match_e2e_constants` 1건 · rc 1 | 기준 6 ✅ |

**R1 이 개발 phase 의 2건과 다른 것은 지운 행이 달라서다** — 첫 행(「잘 찾나」)은 수치를
**둘** 담고 나머지 행은 하나다. 어느 쪽이든 회귀 방향은 같다(행 삭제는 새 단언이 아니라
**기존** 값 대조가 잡는다).

여덟 판이 예산 상한이라 **`〃` 이어받기 변이는 못 돌렸다** — `digest` 에 [4] 로 남겼고
「실측이 아니다」를 항목 안에 적었다.

## 이번 반복이 새로 안 것 — `assert new != old` 는 변이 검증이 아니다

첫 U1 판이 `FAILED (failures=3)` 을 냈고 **그대로 읽었으면 「새 단언이 세다」였다.**
실제로는 변이를 심는 파이썬이 `text[:end] + ROW` 로 **README 뒤를 통째로 잘라** 반 토막을
냈고, 죽은 셋 중 둘은 새 단언과 무관하게 **사라진 `## 검증` 절** 때문이었다. 심는 쪽에
`assert new != old` 는 이미 있었다 — 그것은 «바뀌었나» 만 재고 «의도한 것만 바뀌었나» 는
안 잰다. 러너 앞에 `diff -u 원본 사본` 을 붙이자 그 자리에서 보였고, 고친 뒤 다시 재니
죽는 것은 목표 하나뿐이다(`failures=1`). `digest [8]`(「변이가 실제로 심어졌는지를 먼저
단언한다」)의 **3회**로 등재했다 — 앞의 둘은 BSD sed 미적용과 revert 누락이었고, 이번은
심기는 심었는데 **너무 많이** 심은 반대편이다.

## 갭 탐색 — 8점 이상 0건

여섯 카테고리를 훑었다. 부정 경로는 `setUp` 두 가드(표 못 자름 · 행 0)와
`assertTrue(path)`(첫 행부터 `〃`)가 이미 덮고, 상태·동시성 축은 이 검사에 없다.
8점 미만 하나만 나왔다 — **`〃` 이어받기 가지가 변이로 안 눌린다**([4]): README 의 유일한
`〃` 행이 이어받는 `e2e/design_check.py` 를 **바로 윗 행이 이미 이름으로 적어** 검사가
그쪽으로 통과한다. 뚫려도 오늘 잃는 것이 0이라 이번 스텝에서 처리하지 않았다.

## 범위·집안일

`src/` 0줄 · `e2e/` 0줄 · `tests/` **0줄** · `README.md` **0줄** · `docs/specs/` 무변 ·
`data/crawl.db` 무변 · 재색인 0회 · 스키마 0 · 새 의존성 0 · PR #7 무접촉 · `gh` 0회.
전수 **2회**(예산 2회) — 착수 기준선 하나, 문서를 다 고친 뒤 **네 동기 가드가 새 반복
번호 위에서 초록인지** 확인하는 최종 하나. `history_current.md` 는 90 → 116줄이라 회전
없음(상한 300 · 20회 중 3회).

## 다음

**리뷰 phase.** 계획서 완료 기준 4번은 이제 U4′ 로 적혀 있으니 리뷰는 그 정정 자체를
포함해 읽는다. e2e 는 그다음이다.
