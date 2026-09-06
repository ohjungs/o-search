---
signal: GREEN
phase: 개발
step: 1/1
attempt: 0
iteration: 383
updated: 2026-09-06
ctx: 52
night_iterations: 187
night_red: 2
night_retries: 4
plan: readme-shape-cover — 계획 66 (개발 1/1 완료 · 다음은 테스트 phase)
---

## 현재 상태

**계획 66 스텝 1/1 을 개발했다 — README 표의 «모양» 축 단언 둘이 들어갔다.**
고친 파일은 둘뿐이다(`tests/test_readme.py` +47 · `README.md` -1/+1). 제품 `src/` 0줄 ·
`e2e/` 0줄. 단위 **623 → 625건**.

- `BAND_TABLE` — 「잘하고 있나 재는 자」 표를 **제목으로 잘라** 데이터 행만 뽑는다.
  README 에 표가 셋이라 제목으로 안 자르면 엉뚱한 표를 잰다.
- `METER_CELL` — 셋째 칸의 백틱 안 경로. `〃` 행은 안 걸리고 윗 행 값을 이어받는다.
- `BandTableShapeTest` — `QualityBandTest` 다음, `if __name__` 가드 **앞**.
  `setUp` 이 표를 못 자르거나 행이 0 이면 먼저 죽는다(빈손 위 조용한 통과 차단).
  `test_every_band_row_is_covered` · `test_every_band_row_names_an_existing_meter`.

## TDD 빨간 줄을 눈으로 봤다

클래스만 넣고 전수를 돌리니 `Ran 625` · `FAILED (failures=1)` · rc 1 이고 죽은 것이
`test_verification_counts_match_reality` 였다 — `(623, 21) != (625, 21)`. 계획 4절 8번이
「같은 커밋에서 안 고치면 즉시 빨개진다, **그것이 설계대로다**」로 예고한 그 줄이다.
`README.md:104` 을 `625` 로 고쳐 초록으로 되돌렸다.

## 변이 여덟 판 — 완료 기준 1·2·3·5·6·7·8 통과, 4 는 성립하지 않았다

저장소 밖 사본에 편집을 **실물 파일로** 심었다(심기 전 `count(원문) == 1` 단언 —
`digest [8]` BSD sed 대응). 각 판 `-p test_readme.py` · `Ran 8` ·
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)`.

| 판 | 무엇을 심었나 | 결과 |
|---|---|---|
| **M0** | 무변이 | `OK` · rc 0 — **오탐 0** |
| **U1** | 표에 여덟 번째 행 추가 | `test_every_band_row_is_covered` **1건** |
| **U2** | 셋째 칸 → `quality_evals.py` | `test_every_band_row_names_an_existing_meter` **1건** |
| **U3** | 표 제목 개명(잘라내기 죽이기) | **둘 다** (2건) |
| **U4** | 커버 판정을 `True` 로 고정 | `OK` · rc 0 — **안 죽었다** |
| **U4′** | U1 + 판정 무력화 | `OK` · rc 0 — **생존(귀속 증명)** |
| **M0b** | 셋째 칸 → 실재하는 `perf_crawl.py` | `OK` · rc 0 — **정당한 편집을 안 막는다** |
| **R1** | 표에서 행 삭제 | 기존 `test_readme_bands_match_e2e_constants` 2건 — **회귀 0** |

**완료 기준 4번(U4)이 계획서에 적힌 대로는 성립하지 않는다.** 「판정을 참으로 고정하면
1건 이상 죽는다」인데, README 가 성한 트리에서는 판정을 무력화해도 **죽을 것이 없다**.
그 항목이 재려던 것은 「판정이 실제로 판정하는가」이고, 그것은 **U4′ = U1 + 무력화**가
잰다 — 생존이므로 U1 에서 죽은 것은 곁가지가 아니라 커버 단언 자신이었다.
`digest [7]`(「기록된 것을 실행 전에 다시 재라」)의 **네 번째** 사례이고, 계획 65 의
`len(QUALITY_BAND)` 7≠9 와 같은 모양이다 — **진단은 옳았고 처방이 그때의 추정이었다.**

## 범위·집안일

전수 최종 **`Ran 625 tests in 15.841s` · `OK` · rc 0**(맨몸 · 리다이렉션 0회). 네 동기
가드(`IterationSyncTest`·`StepSyncTest`·`StepGapTest`·`ArchiveIndexTest`) 포함이다.
`docs/specs/` 무변 · `data/crawl.db` 무변 · 재색인 0회 · 스키마 0 · 새 의존성 0 ·
PR #7 무접촉 · `gh` 0회.
`history_current.md` 가 287줄 + 이번 항목으로 상한 300 을 넘어 여섯 항목(반복 376~381)을
`docs/history_067.md` 로 회전했고 **`digest.md` 아카이브 명부에 등재**했다(계획 64 e2e 가
명부 누락으로 대조군이 빨개진 선례). `digest.md` 는 200줄 정각 유지 — 기존 줄에 덧붙였다.

## 다음

**테스트 phase.** 계획 4절 완료 기준을 다시 재되 **4번은 U4′ 로 읽는다** — 그 정정이
이 반복의 산출물 중 하나다.
