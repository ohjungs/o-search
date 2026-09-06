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

## 2026-09-06 16:20 | anchor-net-cover | 개발 1/1 | 시도0

- 한 일: `tests/test_docs.py` **한 파일 15줄(+1 −1)**. ① `StepPatternTest.
  test_status_lines_need_the_whole_line` 에 앵커 리터럴 셋(`"x step: 1/1"`·
  `"step: 1/1x"`·`"x plan: a"` 가 전부 `None`) ② `IterationPatternTest.TABLE` 과
  `StepPatternTest.TABLE` 에 **줄 중간에서 시작하는 잡음 행**을 정확한 행 앞에 하나씩.
- 검증: `rules/dev.md` 0절 2번을 남의 관찰로 안 대신했다 — **편집 전에** 이 반복에서
  M0·M1a·M1b·M2·M3·M4 를 다시 돌려 `Ran 620 · OK · 죽은 단언 0` **6/6 생존**을 보고,
  다섯 줄을 넣고 같은 여섯을 다시 돌려 **M1a·M1b·M2·M3·M4 가 1건씩 사망**(빨강이
  정확히 새로 넣은 줄에서 났다) · **M0 은 여전히 0(오탐 0)**. 감지력 무회귀로 계획 62
  의 `ITER_LINE` 앵커 변이 둘이 각각 1건씩 그대로 죽이고, 양성 대조는 **6·6·5·4**.
  전수 맨몸 `Ran 620 tests · OK · rc 0`. 하네스는 저장소 밖 `mock.patch.object`.
- 계획서와 어긋난 것 하나: 완료 기준 6번이 「건수가 620 → 늘어난 수」라고 적었는데
  실제는 **620 그대로**다. 처방이 기존 시험에 단언을 더하는 것이라 메서드 수가 안
  변한 것이고, 계수기를 맞추려 시험을 쪼개지 않았다. `README.md:104` 의 「단위 620건」
  이 이미 맞아 **`README.md` 무접촉**. 나머지 기준 7개는 그대로 충족.
- 범위: `git diff --stat HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db`
  sha256 `85c96744…5bda18` 무변 · `ARCHIVE`·`StepGapTest.INDEX` 무접촉 ·
  `test_absent_slug_matches_nothing` 여전히 `None`. `status.step` 과 `index.md`
  63번 행이 함께 `1/1` 로 움직였다. 러너 리다이렉션·파이프 위반 0(누적 38 유지).
- 다음: **테스트 phase.** 남은 앵커 자리는 `ARCHIVE` 의 `^…$`(`.match()` 로만 불려
  앵커가 안 재진다 — 계획서 5절이 이름으로 미뤘다)와 `APPEND_TARGETS` 쪽이다.

## 2026-09-06 17:05 | anchor-net-cover | 테스트 1/1 | 시도0

- 한 일: **새 테스트 0줄.** 갭 탐색이 찾은 둘이 8점 선 아래(`[5]`·`[4]`)라
  `digest.md` 에 등재만 하고, 개발이 신고한 어긋남(완료 기준 6번의 「620 → 늘어난
  수」)을 **계획서 4절에 정정 문단으로 못박아 닫았다** — 기준의 뜻(전수 초록 +
  README 일치)은 그대로 두고 건수 증가 요구만 무효다.
- 검증: 하네스를 이 반복에서 새로 짜서(저장소 밖 `scratchpad/mutate.py` ·
  `mock.patch.object`) 다시 걸었고 개발의 보고가 그대로 맞았다 — M0 **0**(오탐 0) ·
  M1a(`^`)·M1b(`$`)·M2·M3·M4 **각 1건** · 계획 62 의 `ITER_LINE` 변이 둘도 **각 1건**
  (감지력 무회귀) · 양성 대조 **6·6·5·4**. 전수 맨몸
  `Ran 620 tests in 15.869s · OK · rc 0`. `git status --porcelain` 은 하네스를 도는
  내내 빈손이었다.
- 단언을 낮춘 것이 아님을 재서 보였다: `test_readme.UNIT_COUNT` 를 「못 뽑는 꼴」과
  「다른 수를 뽑는 꼴」로 각각 갈면 `test_verification_counts_match_reality` 가 각각
  1건씩 죽는다 — 「단위 620건 ↔ 실제 620건」은 살아 있는 단언이다(e2e 21종 무변).
- 갭 둘(8점 미만이라 안 세웠다): **`[5]`** `APPEND_TARGETS` 를 줄이는 변이가 죽은
  단언 0 — `history_current.md` 를 빼도 머리 검사가 안 운다. **`[4]`** `ARCHIVE` 를
  넓히는 변이 셋(`$`·`re.I`·`[0-9]*`)도 0. **기록 정정**: 계획 62·63 이 `^…$` 를
  한 덩어리로 「`.match()` 라 잉여」로 미뤘는데 **등가 변이는 `^` 뿐**이고, 진짜
  위험한 접두어 넓히기는 `DocCitationTest` 가 이미 1건으로 잡는다(그래서 [4] 다).
- 범위: `tests/`·`src/`·`e2e/`·`README.md` **무접촉** — 고친 것은 기록 문서 넷과
  계획서 하나다. `digest.md` 는 새 한 줄을 넣고 닫힌 완료 항목 하나(계획 40
  `exit-code-contract` · 원본 `plan_history_026.md`)를 지워 **200줄 정각** 유지.
  `status.step` 과 `index.md` 63번 행은 `1/1` 로 그대로다.
- 다음: **리뷰 phase.** 볼 것은 ① 다섯 줄이 실물 판정을 안 바꾸는가 ② 잡음 행의
  «대상 행 앞» 순서 의존이 주석에만 적혀 있는가 ③ 계획서의 정정이 「단언을 낮춘
  것」으로 읽히지 않는가.

## 2026-09-06 17:50 | anchor-net-cover | 리뷰 1/1 | 시도0

- 한 일: 백지 패스를 먼저 끝내고 대조 패스로 넘어갔다(`rules/review.md` 0절). 이슈
  **1건(informational · 자동 수정)** 을 잡아 그 자리에서 고쳤다 — `tests/test_docs.py`
  **6줄(+2 −1 · 값 하나)**.
- **이슈: 잡음 행의 `9/9` 가 ① 행의 `9/9` 와 겹쳐 두 범인이 한 값으로 보였다.**
  `StepPatternTest.TABLE` 의 ① `plan_endtag-cut-cover` 행도 `9/9` 라, 실패가 `9/9` 로
  났을 때 그것이 「슬러그를 안 보고 앞 행을 물었다」인지 「`^` 가 죽어 줄 중간 잡음
  행을 물었다」인지 값만으로 안 갈렸다. 서로 다른 변이 둘이 같은 관측을 낸다.
  게다가 실패 메시지의 원인 열거가 새 행을 안 담아 **틀린 범인을 지목**했다.
  고침: 잡음 행을 `8/8` 로 바꿔 표 안의 넷(`9/9`·`3/7`·`8/8`·`1/1`)을 전부 다르게
  하고, 두 시험의 메시지를 값→범인 대응으로 다시 적었다(`IterationPatternTest` 쪽도
  `999` 를 열거에 넣었다). 판정은 0줄 바뀌었다.
- 검증: 리뷰가 남의 관찰을 안 받았다 — 저장소 밖 하네스(`scratchpad/rev63.py`)로
  M1a·M1b·M2·M3·M4 를 **직접 다시 걸어 8/8 항목 전부 PASS**(변이는 `999`·`8/8` 를
  집고 실물은 `232`·`1/1` 그대로 · 없는 슬러그는 여전히 `None`). 고치기 전과 후로
  전수를 두 번 돌려 `Ran 620 tests · OK · rc 0` 무변.
- 테스트 phase 가 남긴 세 물음에 답한다: ① 다섯 줄은 실물 판정을 안 바꾼다(`232`·
  `1/1`·`None` 실측). ② 순서 의존은 여전히 주석에만 산다 — 안에서 재려면 저장소
  안에 변이 하네스를 들여야 해서 그대로 뒀고, 대신 이번 수정이 **값 넷을 전부 다르게**
  만들어 순서가 깨졌을 때 실패 메시지가 범인을 집게 했다. ③ 정정은 단언을 안 낮췄다
  — `README.md:104` 「단위 620건」 ↔ 실제 620 이 그대로 맞고 대조도 살아 있다.
- 범위: `git diff --stat 1752ecc HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
  `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 고친 파일은 `tests/test_docs.py`
  하나와 기록 문서 셋. `README.md` 무접촉(건수 620 무변). `status.step` 과 `index.md`
  63번 행이 `1/1` 로 일치. 러너 리다이렉션·파이프 위반 0(누적 38 유지).
- 다음: **e2e phase.** 21종 실물 명령이 rc 0 인지와 완료 기준 8개를 끝까지 대조한다.

## 2026-09-06 18:40 | anchor-net-cover | e2e 1/1 | 시도0

- 한 일: e2e 21종을 맨몸으로 하나씩 돌리고(**전부 rc 0**), 전수 `Ran 620 tests in
  15.874s · OK · rc 0`, 완료 기준 여덟을 저장소 밖 메모리 하네스로 다시 쟀다 —
  **M1a·M1b·M2·M3·M4 각 1건씩 사망하고 의도한 이름만** 죽으며 M0 대조군은 오탐 0,
  계획 62 의 `ITER_LINE` 변이 둘도 여전히 1건씩(감지력 무회귀). **8/8 충족.**
  새 e2e 파일 **0개** — 근거 셋을 오늘 쟀다(범위 diff 빈손 · `src/` 에 `tests` import
  0건 · 새로 만들면 전수 명령과 겹쳐 「1회만」이 깨진다).
- 사용자 관점 검증(실물 `docs/` 를 `mktemp -d` 로 복사, 저장소 무접촉): 사람이 낼 편집
  여덟 중 **넷은 `StepSyncTest` 가 문장으로 울고**(양방향 스텝 어긋냄·들여쓰기·꼬리
  메모·슬러그 `-2` 접미), **표에 메모 행을 끼운 둘은 오판 0 으로 조용**하다 — 앵커가
  죽으면 그 자리에서 `9/9`·`999` 를 집는다. 계획이 산 자리가 그 「조용함」이다.
- 계획 62 e2e 의 교훈을 적용해 diff 의 주석·실패 메시지 리터럴 여섯 주장을 실물과
  대조했다 — **어긋난 곳 0**(`^` 제거 → `8/8`·`999` 실측 · 값→범인 대응 셋 성립 ·
  표의 수 넷 겹침 0). 완료 기준 6번의 정정도 재측: `UNIT_COUNT`·`E2E_COUNT` 를 세
  갈래로 갈면 `test_verification_counts_match_reality` 가 각각 1건씩 죽어 **단언이
  안 낮아졌다**. 기준선 8축 회귀 0 이라 `docs/project.md` 무갱신.
- 범위: `src/`·`e2e/`·`docs/specs/`·`data/` diff **빈손** · `data/crawl.db` sha256 무변 ·
  `README.md` 무접촉. 고친 것은 기록 문서와 `docs/e2e/anchor-net-cover/result.md` 뿐이고
  계획서는 `plan_history_049.md` 로 아카이브했다. `digest.md` 는 완료 한 줄을 더하며 가장
  오래된 완료 항목(계획 57)을 지워 **200줄 정각**. 러너 위반 0(누적 38 유지).
- 다음: **계획 63 DONE · 활성 계획 0.** 다음 반복은 계획 phase — 후보 탐색은 이 반복에서
  하지 않았다.

## 2026-09-06 19:30 | archive-scope-cover | 계획 0/1 | 시도0
- 한 일: 계획 64 `archive-scope-cover` 를 탐색·등재했다. 산출물은 계획서
  `docs/plan_archive-scope-cover.md` · `docs/index.md` 64번 행 · `docs/status.md`
  (GREEN · 개발 · 0/1 · 반복 371) · `docs/metrics.md`(반복 371 · 진행 1) ·
  `docs/digest.md` 의 `[5]` 항목 정정(줄 수 200 정각 유지 — 새 줄 없이 덧붙였다).
- 결과: **1~5순위 실측 0건** — 전수 맨몸 `Ran 620 tests in 15.877s` · `OK` · rc 0 ·
  린터/타입체커 설정 파일 0개 · 코드 `TODO` 0(1건은 `tests/test_indexer.py:759` 의 파서
  입력 문자열 안) · `docs/candidates.md`·`docs/patches/` 없음 · `digest ## 보류` 0건 ·
  `gh issue list --state open` 0건 rc 0 · 활성 계획 0. **6순위 `[5]`** 를 열었고 더 높은
  점수는 전부 여는 조건 미도래다.
- 결과: **착수 탐침이 기록을 뒤집었다**(`digest [7]` 열다섯 번째 적용). 저장소 밖
  `mock.patch.object` 하네스로 전수를 변이마다 다시 돌렸다 — `ARCHIVE` 축은
  M3(`$` 제거)·M4(`re.I`)·M5(`[0-9]*`)에 더해 **기록에 없던 M11(`design_history` 이름
  빼기)까지 넷이 `Ran 620 · 죽은 단언 0`** 으로 살고, 양성 대조(`^ZZZ_[0-9]+\.md$`)가
  `DocCitationTest` 1건을 죽여 배선을 증명했다. M11 은 `design_history_*.md` 가 오늘
  `docs/` 에 **33개** 실재해 도달성이 항목의 서술보다 훨씬 높다.
- 결과: 반대로 항목이 값을 뒀던 **①(`APPEND_TARGETS`)은 하네스 인공물**이었다 —
  `CITATION` 이 임포트 시점에 그 상수에서 파생되므로 소스 편집과 같게 둘을 함께 갈면
  M1 **1건** · M2 **2건** · M8(이름 오타) **3건**이 죽는다. 살아남는 M7(넓히기)은 검사를
  더 조일 뿐이고 그 처방은 거울 단언이라 행동을 안 잰다. **축 하나를 버리고 `ARCHIVE`
  에만 서기로 계획서 5절에 못박았고, 다음 탐색이 다시 열지 않도록 digest 에 적었다.**
- 결과: 처방 리터럴 아홉이 갈래를 실제로 가르는 것도 미리 쟀다 — 실물은 `CAUGHT` 3/3
  통과 · `NOT_CAUGHT` 6/6 거절(**오탐 0**)이고 M3·M4·M5·M10·M11 이 각각 다른 이름에서
  물린다. **설계 생략 — 트리거 0**(새 모듈 0 · 제품 인터페이스 무변 · 파일 2개 ·
  되돌리기가 커밋 하나 revert · 대안은 저장소가 네 번 고른 관용구라 안 갈린다).
- 결과: 범위 무접촉 — `src/`·`e2e/`·`docs/specs/`·`data/` 무변경 · `data/crawl.db`
  sha256 `85c96744…5bda18` 무변 · `README.md` 무접촉(건수는 개발 커밋에서 움직인다).
  변이는 전부 메모리라 워킹트리가 열두 판 내내 `git status --porcelain` 빈손이었다.
  러너 위반 0(누적 38 유지) · `night_iterations` 는 대화형이라 187 그대로 뒀다.
- 다음: **개발 phase 1/1** — `ArchivePatternTest` 를 `ArchiveMatchTest` 옆에 세운다
  (리터럴 표 한 벌 + 메서드 둘 · 제품 `src/` 0줄 · `README.md` 건수 줄 동반 수정).

## 2026-09-06 17:35 | archive-scope-cover | 개발 1/1 | 시도0

- 한 일: `tests/test_docs.py` **한 파일 39줄 추가**(`README.md` +1 −1). `ArchivePatternTest`
  를 `ArchiveMatchTest` 바로 위에 세웠다 — `CAUGHT` 셋(`history_001.md`·
  `plan_history_049.md`·`design_history_046.md`) · `NOT_CAUGHT` 여섯
  (`history_current.md`·`history_001.md.bak.md`·`history_.md`·`HISTORY_001.MD`·
  `digest.md`·`index.md`) · `subTest` 로 도는 메서드 둘. 실물 파일 목록이 아니라 **모양**을
  고정해서 실물 아카이브가 늘거나 줄어도 아홉은 안 움직인다.
- 검증: `rules/dev.md` 0절대로 **RED 를 이 반복에서 직접 봤다** — 테스트를 먼저 넣고 돌리니
  `AssertionError: Tuples differ: (620, 21) != (622, 21)` 로 `test_readme` 가 즉시 울었고,
  같은 커밋에서 `README.md:104` 를 620 → **622** 로 고쳤다. **계획 63 이 무접촉이라 못 본
  가드가 이번엔 설계대로 울었다.**
- 검증: 완료 기준 **9/9**. 저장소 밖 `mock.patch.object` 하네스로 변이마다 전수를 다시 돌려
  ① M3(`$` 제거) → `history_001.md.bak.md` 1건 ② M4(`re.I`) → `HISTORY_001.MD` 1건
  ③ M5(`[0-9]*`) → `history_.md` 1건 ④ M11(`design_history` 제거) → `design_history_046.md`
  1건. **어제 넷 다 생존하던 자리가 넷 다 죽는다.**
- 검증: 감지력 무회귀(기준 5)를 **추정하지 않고 쟀다** — M10(접두 확대)은 `DocCitationTest`
  1건을 그대로 죽이고 새 단언 셋을 더 죽여 **4**, M1·M2·M8(`APPEND_TARGETS`+`CITATION` 을
  함께 간 소스 편향 변이)은 어제와 같은 **1·2·3**, 계획 63 이 세운 앵커 변이 다섯
  (A1a·A1b `STEP_LINE` · A2 `PLAN_SLUG` · A3 `ITER_ROW` · A4 `STEP_ROW`)도 **각 1건** 그대로.
  M0 무변이 대조군 **0**(오탐 0) · 양성 대조 `^ZZZ_[0-9]+\.md$` 는 `CAUGHT` 셋 +
  `DocCitationTest` 로 **4**.
- 검증: 전수 맨몸 `Ran 622 tests in 15.461s` · `OK` · **rc 0**. 범위 무접촉 —
  `git diff --stat ba53783 HEAD -- src/ e2e/ docs/specs/ data/` 빈손 · `data/crawl.db`
  sha256 `85c96744…5bda18` 무변 · 재색인 0 · 제품 `src/` **0줄**. 러너 리다이렉션·파이프
  위반 0(누적 38 유지) · `night_iterations` 는 대화형이라 187 그대로.
- 다음: **테스트 phase 1/1.** 남은 자리 둘을 status 에 이름으로 적어 뒀다 — ① `ARCHIVE` 는
  `.match()` 로만 불려 `^` 가 잉여라 **M6 은 여전히 등가 변이**(재는 쪽이 아니라 지우는 쪽이
  답이고 계획 밖) ② `APPEND_TARGETS` 축은 계획서 5절이 이유를 적어 닫아 뒀다 — 다시 안 연다.
