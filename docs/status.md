---
signal: GREEN
phase: 계획
step: 0/1
attempt: 0
iteration: 339
updated: 2026-09-05
ctx: 55
night_iterations: 159
night_red: 2
night_retries: 0
plan: passage-cost-band 계획 58 (계획서 작성 완료 · 다음은 설계)
---

# 현재 상태

**계획 57 을 아카이브하고 계획 58 `passage-cost-band` 를 열었다.** 이 반복이 한 일은
둘이다: 닫힌 계획의 문서 회전, 그리고 탐색 1~5순위를 실측으로 비운 뒤 6순위에서
**실행 가능한 최상위 항목**을 골라 계획서를 쓴 것.

## 아카이브 — 계획 57 `passage-cost-axis`

`docs/plan_passage-cost-axis.md` → `docs/plan_history_043.md` ·
`docs/design_passage-cost-axis.md` → `docs/design_history_043.md`(내용 무변경 · `git mv`).
`index.md` 의 계획 57 줄을 **완료**(1/1 · 완료 기준 7/7 · 21종 rc 0 · 회귀 0)로 닫고
아카이브 파일명을 적었다. 문서 가드 `ArchiveIndexTest`·`DocCitationTest`·`IterationSyncTest`
`Ran 3 tests · OK · rc 0`.

## 탐색 — 1~5순위 **0건**, 6순위에서 골랐다

전수 `Ran 605 tests · OK · rc 0` · 린터/타입체커 없음 · `TODO`/`FIXME`/`HACK` 은
`src`·`tests`·`e2e` 통틀어 1건인데 그것은 파서 입력 문자열 안이다 ·
`docs/candidates.md` 없음 · `digest ## 보류` 0건.

6순위에서 **더 높은 점수 넷을 안 고른 이유는 전부 «막혀 있다»** 다 — `[9]` `/search` 몫은
자기 여는 조건이 실물 분포(재색인 필요) · `[8]` 숨은 텍스트는 `_SKIP_TAGS` 공유라 재색인 ·
`[7]` macOS `sys.pycache_prefix` 는 처방이 이미 `project.md` 에 들어갔고 여는 조건이
「**옛** 변이 결론에 기대는 계획」 · `[7]` 재파싱 몫 배정은 `docs/specs/` 판단이라
사람 결정 대기 5번이다. 나머지 둘(`[9]` 러너 잡음 · `[7]` 캡 안 최악)은 이미 닫혔고
이 반복이 `digest` 에 취소선을 그었다.

## 계획 58 — `passage-cost-band` (`docs/plan_passage-cost-band.md`)

**② 의 상한 1.60 과 예산 정각 1.4286 사이가 열려 있다.** 계수가 그 사이면 실제 최악이
500~560ms 로 **사양 성능 5 밖**인데 ①(리터럴 350ms)도 ②도 초록이다. 오늘 값 기준
파서가 **1.51~1.69배** 느려지는 구간이고, 그 미완은 테스트 안 `ponytail:` 주석이
이미 적어 두었다. 목표는 **「② 초록 = 최악 ≤ 500ms」를 참으로 만들되 오탐 RED 를 안
만드는 것**이다. 스텝 1개 · 건드릴 파일 `tests/test_indexer.py` 하나 · 제품 0줄.

**phase 는 설계다** — 대안 셋이 갈린다: **A** 상한을 예산에서 유도(1.4286 · 창 0 ·
부하 여유 1.21배) · **B** 리터럴 1.20(계획 57 주석의 처방 · 여유 1.02배로 오탐 위험 최대) ·
**C** 자를 `time.perf_counter` 에서 `time.process_time` 으로 바꿔 부하 배수 자체를 줄인다.
갈림의 축은 「창을 얼마나 닫나」 대 「부하에서 안 흔들리나」이고 값을 재야 고른다.

## 기점을 `main` 으로 안 잡았다

고칠 단언이 `main` 에 **없다** — `git ls-remote origin main` = `d1fe3e9`(계획 56)이고
`git show origin/main:tests/test_indexer.py` 에 `1.60` 은 0건이다. 계획 57 은 미병합이고
열린 PR 은 0건이다. 기점은 `loop/passage-cost-axis` 의 아카이브 커밋이다.

## 사람 결정 대기 (계획 58 과 무관하게 계속 열려 있다)

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 봤다.
4. **3시간 자동 스냅샷 잡을 루프 작업 중에도 세울 것인가**(반복 328 사고). RED 중간을
   덮치면 깨진 상태가 원격에 올라간다. 반복 334 에서 RED 아닌 자리에서 실제로 일어났다.
5. **재파싱에 예산 얼마를 줄 것인가** — 캡 최악이 예산의 **70%** 라는 사실이 세 자리에
   모두 적혀 있다. 계획 58 은 이 몫을 **안 건드리고** 500ms 정각을 그대로 쓴다.
6. **계획 57(`loop/passage-cost-axis`)의 병합** — `main` 은 계획 56 까지고 열린 PR 은
   0건이다. 계획 58 이 그 브랜치 위에 쌓이므로 병합은 순서대로 하면 된다.
