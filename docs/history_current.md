# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

**회전 명부는 `digest.md` 의 `## 완료` 절 «아카이브 명부» 줄이 정본이다.**
여기 있던 스물한 회전의 서술(233줄)은 그 줄과 내용이 겹쳤고, 검사가 강제하는 명부도
그쪽 하나뿐이라(`tests/test_docs.py` 의 `ArchiveIndexTest`) **개발 9(반복 269)가 이
자리에서 지웠다** — 회전으로는 300줄 상한을 못 맞추던 세 반복(309 → 372 → 418줄)의
원인이 이 명부였다. **지운 것은 머리말이지 반복 기록이 아니다** — 항목은 여전히
append 전용이고 수정·삭제 금지다. 각 회전의 사유는 `digest.md` 의 같은 줄에, 원문은
`history_<NNN>.md` 에 그대로 있다.

## 2026-09-06 20:10 | readme-shape-cover | 계획 0/1 | 시도0
- 한 일: **계획 66 `readme-shape-cover` 등재** — `docs/plan_readme-shape-cover.md` 신규 ·
  `docs/status.md`(signal GREEN · phase 개발 · step 0/1 · 반복 382 · plan 슬러그) ·
  `docs/index.md` 계획 행 1줄 · `docs/metrics.md` 누적 셋. 앞 반복이 `digest [7]` 에 ①④ 로
  남긴 **README 표 «구조» 축 두 구멍**을 한 계획으로 묶었다 — ① 표에 행을 끼워도 조용하다 ·
  ④ 셋째 칸(측정기 파일 이름)이 실재하는지 아무도 안 잰다.
- 결과: **착수 탐침 4판**(전수 1 · `test_readme.py` 3)으로 **두 구멍이 오늘도 살아 있는 것**을
  실물 파일 편집으로 확인했다 — 기준선 전수 `Ran 623 tests in 15.724s` `OK` rc 0 ·
  사본 무변이 M0 `Ran 6` `OK` rc 0(오탐 0) · U1(행 하나 추가) `Ran 6` `OK` rc 0 **생존** ·
  U2(`quality_eval`→`quality_evals` 오타) `Ran 6` `OK` rc 0 **생존**. 저장소 밖 사본에서
  돌렸고 워킹트리는 무변경, 매 판 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 줬다.
  **digest 의 처방 한 줄을 정정했다** — `[7]①` 이 적어 둔 「표 행 수를 `len(QUALITY_BAND)` 와
  대조」는 **7≠9 라 성립하지 않는다**(표는 일곱 행, 밴드는 아홉 — 첫 행과 마지막 행이 각각
  둘을 담는다). 상수 7 을 적는 안은 그것이야말로 거울이라, 방향을 **「각 행이 밴드 하나
  이상에 물리는가」**로 바꿔 적었다. 셋째 칸은 `(README.parent / 경로).is_file()` 이고
  `〃` 는 건너뛰지 않고 윗 행 경로를 이어받는다(건너뛰면 눈먼 자리가 생긴다).
  **기점을 `origin/main` 으로 다시 쟀다** — 사람이 `bff2580` 로 병합해 `QualityBandTest` 가
  이미 `main` 안에 있다(`git diff --stat origin/main HEAD -- tests/test_readme.py README.md`
  빈손). 계획 58 이 「기점은 아카이브 커밋」으로 판단했던 근거는 오늘 안 썼다.
  설계 생략 — 트리거 0(파일 2개 · 새 파일 0 · 인터페이스 0 · 되돌리기 쉬움) · 대안 무분기.
  범위 무접촉: 제품 `src/`·`e2e/` **0줄** · `README.md` 무변 · `docs/specs/` 읽기만 ·
  `data/crawl.db` 무변경 · 재색인 0 · 스키마 0 · 새 의존성 0 · PR #7 무접촉(`gh` 호출 0).
  러너 규율 위반 **0회**(누적 38 유지).
- 배운 것: **보류 항목의 «처방» 은 진단과 같은 신뢰도가 아니다 — 세 번째 사례다.**
  `digest [7]` 이 스스로 「기록된 답을 실행 전에 다시 재라」로 적어 둔 그 자리에서, 오늘
  틀린 것은 값도 진단도 아니고 **한 줄짜리 처방**이었다. 진단(「행이 늘어도 조용하다」)은
  실측으로 그대로 참인데, 같은 항목이 이어 적은 처방은 표 행 수(7)와 밴드 수(9)를 같은
  것으로 놓고 있었다 — **처방을 쓴 순간에는 둘이 같아 보였다.** 계획 phase 가 진단만
  다시 재고 처방을 그대로 받았다면 개발이 성립하지 않는 단언을 짜다 멈췄을 것이다.
- 다음: **개발 1/1** — `tests/test_readme.py` 에 `BandTableShapeTest`(`__main__` 가드 **앞**).
  전수가 623 → **625** 가 되므로 `README.md:104` 의 건수 한 줄을 같은 커밋에서 고친다.

## 2026-09-06 21:00 | readme-shape-cover | 개발 1/1 | 시도0
- 한 일: **계획 66 스텝 1/1 — 표 «모양» 축 단언 둘을 넣었다.** `tests/test_readme.py` 에
  모듈 수준 정규식 둘(`BAND_TABLE` 제목으로 표를 잘라낸다 · `METER_CELL` 셋째 칸의 백틱 경로)
  과 `BandTableShapeTest`(`QualityBandTest` 다음 · `__main__` 가드 **앞**) 를 붙였다 —
  `test_every_band_row_is_covered`(각 행이 `QUALITY_BAND` 정규식 하나 이상에 물리는가) ·
  `test_every_band_row_names_an_existing_meter`(셋째 칸 경로가 `(README.parent/경로).is_file()`
  이고 `〃` 는 건너뛰지 않고 **윗 행 값을 이어받는다**). `setUp` 이 표를 못 자르거나 행이
  0 이면 먼저 죽는다(빈손 위 조용한 통과 차단). `README.md:104` 건수 `623` → `625` 를
  **같은 커밋에서** 고쳤다. 제품 `src/` 0줄 · `e2e/` 0줄 · 고친 파일 둘(+47/-1).
- 결과: **TDD 빨간 줄을 눈으로 봤다** — 클래스만 넣고 돌린 전수가 `Ran 625` ·
  `FAILED (failures=1)` · rc 1 이고 죽은 것이 `test_verification_counts_match_reality`
  (`(623, 21) != (625, 21)`) 였다. 건수를 고친 뒤 **전수 `Ran 625 tests in 15.841s` · `OK` ·
  rc 0**(맨몸 · 리다이렉션 0회 · `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)`).
  변이 **여덟 판**(저장소 밖 사본 · 각 판 `-p test_readme.py` `Ran 8`): M0 무변이 `OK` rc 0
  (**오탐 0**) · U1 행 추가 → `test_every_band_row_is_covered` **1건** · U2 셋째 칸을 없는
  파일로 → `test_every_band_row_names_an_existing_meter` **1건** · U3 제목 개명 → **둘 다**
  (2건) · M0b 실재하는 다른 파일로 개명(`perf_crawl.py`) `OK` rc 0(**정당한 편집을 안 막는다**)
  · R1 행 삭제 → 기존 `test_readme_bands_match_e2e_constants` 2건(**회귀 0**).
- 다음: **완료 기준 4번(U4)이 계획서에 적힌 대로는 성립하지 않았다.** 「`any(...)` 를 참으로
  고정하면 1건 이상 죽는다」인데, 판정을 무력화해도 **README 가 성한 트리에서는 죽을 것이
  없다** — 실측 `Ran 8 · OK · rc 0`. 그 항목이 재려던 것(판정이 실제로 판정하는가)은
  **U4′ = U1 + 판정 무력화**로 다시 쟀고 `Ran 8 · OK · rc 0` 으로 **생존**했다 — U1 에서
  죽은 것이 곁가지가 아니라 커버 단언 자신이었다는 귀속 증명이다. `digest [7]`(「기록된 것을
  실행 전에 다시 재라」)의 **네 번째** 사례이고 계획 65 의 `len(QUALITY_BAND)` 7≠9 와 같은 모양
  이다 — **진단은 옳았고 처방이 그때의 추정이었다.** 집안일: `history_current.md` 287줄 +
  이번 항목이 상한 300 을 넘어 여섯 항목(반복 376~381)을 `docs/history_067.md` 로 회전했고
  `digest.md` 아카이브 명부에 등재했다(계획 64 e2e 가 명부 누락으로 대조군이 빨개진 선례).
  다음 반복은 **테스트 phase** 다.
