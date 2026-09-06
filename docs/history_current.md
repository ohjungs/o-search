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

## 2026-09-06 15:00 | anchor-net-cover | 계획 0/1 | 시도0
- 한 일: 계획 62 가 반복 365 에 DONE 으로 닫혀 활성 계획이 0 이라 **탐색 → 계획 63
  등재**를 돌았다. `discover.md` 1절 1~5순위를 실측으로 훑고(전수 `Ran 620 tests in
  15.930s` `OK` rc 0 맨몸 · 린터/타입체커 설정 0개 — 최상위 설정은 `.gitignore` 하나뿐 ·
  `TODO`/`FIXME`/`HACK` 이 `src`·`tests`·`e2e` 에 1건인데 `tests/test_indexer.py:759`
  **파서 입력 문자열 안** · `docs/candidates.md` 없음 · `docs/patches/` 없음 ·
  `digest ## 보류` 절 본문이 주석 한 줄뿐이라 0건 · `gh issue list --state open` 0건
  rc 0) **전부 0건**이라 6순위 `digest ## 다음 계획 후보 (테스트 phase 갭, 8점 미만)`
  의 `[6]` 을 열었다. 계획서 `docs/plan_anchor-net-cover.md` · `index.md` 63번 행 등재.
  **회전도 함께 했다** — 이 항목을 붙이면 `history_current.md` 가 307줄이라 상한 300 을
  넘어, 계획 61·62 의 반복 기록 열 개(반복 356~365)를 `history_064.md` 로 밀었다.
  둘 다 DONE 이고 `digest ## 완료` 에 이미 압축돼 있어 새로 압축할 것이 없었다.
- 결과: **착수 탐침이 기록된 답을 다시 쟀고 이번에도 항목이 맞았다**(`digest [7]`
  열네 번째 적용). 저장소 밖 `mock.patch.object` 하네스로 모듈 상수를 메모리에서 갈아
  끼워(파일 무편집 · `git status --porcelain` 빈손) 전수를 네 번 돌리니 M1(`STEP_LINE`
  `^`·`$` 제거) · M2(`PLAN_SLUG` `^`) · M3(`ITER_ROW` `^`) · M4(`STEP_ROW` `^`)
  **넷 다 `Ran 620 · 죽은 단언 0` 으로 생존**했다. 같은 넷을 `^ZZZ` 꼴로 가는 양성
  대조는 각각 **6·6·5·3 건**을 죽여 배선을 증명했다(축별로 `StepGapTest`·
  `StepPatternTest`·`StepSyncTest` 와 `IterGapTest`·`IterationPatternTest`·
  `IterationSyncTest` 로 갈렸다). **어긋난 것은 대조 건수 하나뿐**이고(항목은
  `6·6·4·1`) 원인은 대조 리터럴의 모양 차이라 점수 `[6]` 을 그대로 뒀다. **처방 다섯
  줄도 실행 전에 갈래를 갈랐다** — `"x step: 1/1"`·`"step: 1/1x"`·`"x plan: a"` 는
  실물이면 매치 없음·변이면 매치이고, 두 합성 표에 줄 중간에서 시작하는 잡음 행을
  정확한 행 앞에 끼우면 실물은 `232`·`1/1` 그대로인데 변이는 `999`·`9/9` 를 집는다
  (**오탐 0**). **`ARCHIVE` 는 뺐다** — 항목이 「`.match()` 로만 쓰여 `^` 가 잉여」로
  적어 둔 그것이라 재는 쪽이 아니라 지우는 쪽이 답이고, 계획서 5절에 남겼다. **설계
  생략 — 트리거 0**(파일 2개 · 새 모듈 0 · 제품 `src/` 0줄 · 되돌리기 revert 하나).
  원격 `git ls-remote origin loop/passage-cost-band` = `1752ecc7b210…` 로 반복 365
  커밋과 동일 · `origin/main` 은 계획 56(`d1fe3e9`)까지 · PR 0. `docs/digest.md` 는
  200줄 정각을 지켰다(후보 `[6]` 과 회전 명부 줄 끝에 이어 붙이기만 했다). 러너
  리다이렉션·파이프 위반 0(누적 38 유지).
- 다음: **개발 1/1.** `tests/test_docs.py` 에서 ① `StepPatternTest` 의 줄 단언에
  리터럴 세 줄을 더하고 ② `IterationPatternTest.TABLE`·`StepPatternTest.TABLE` 에
  잡음 행을 하나씩 끼운다. `rules/dev.md` 0절대로 **RED 를 눈으로 먼저 본다**. 건드릴
  파일은 `tests/test_docs.py`·`README.md` 둘뿐이고 `StepGapTest.INDEX` 는 안 건드린다.
