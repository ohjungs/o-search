---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 361
updated: 2026-09-06
ctx: 47
night_iterations: 178
night_red: 2
night_retries: 4
plan: head-anchor-cover 계획 62 (계획 완료 · 설계 생략 · 다음은 개발 1/1)
---

## 현재 상태

**계획 61 이 반복 360 에 DONE 으로 닫혀 활성 계획이 0 이었다 — 탐색을 돌려 계획 62
`head-anchor-cover` 를 등재했다.** 계획서 `docs/plan_head-anchor-cover.md` ·
`index.md` 62번 행 `0/1` · 설계 생략(트리거 0) · 다음 반복은 **개발 1/1** 이다.

## 무엇을 여는가

`tests/test_docs.py` 의 **문서 가드 둘이 자기 판정을 못 잰다.** 실물 문서가 늘
「맞는 모양」이라 판정을 무력화해도 아무 데도 안 걸린다.

- ① **`ITER_LINE`(`tests/test_docs.py:48`)의 앵커 `^`·`$` 를 지워도 죽는 단언 0.**
  앵커를 재는 줄처럼 보이던 `assertIsNone(ITER_LINE.search("night_iterations: 90"))`
  이 실제로 막는 것은 **복수형 `s`**(`iterations: ` ≠ `iteration: `)다.
- ② **`DocHeadTest`(`tests/test_docs.py:142`)의 판정 `^# \S` 를 `^` 로 넓혀도 죽는
  단언 0.** `APPEND_TARGETS` 세 문서가 늘 H1 으로 시작해서다. **이 파일이 존재하는
  이유가 `digest.md` 의 H1 이 리스트 항목에 빨려 들어간 사고**인데, 그 사고를 잡는
  판정이 지금 자기를 못 잰다.

## 1~5순위 실측 0건 — 「없다」가 아니라 재고 적었다

전수 `Ran 618 tests in 15.892s` · `OK` · **rc 0 맨몸** · 린터/타입체커 설정 파일 0개
(`project.md` 「린트/타입체크: 없음」) · `TODO`/`FIXME`/`HACK` 이 `src/`·`tests/`·
`e2e/`·`scripts/` 에 **1건**인데 그것은 `tests/test_indexer.py:759` 의 **파서 입력
문자열 안**(`"<p>김치찌개 <!-- TODO: <a href=x> 옛 링크"`)이라 코드 부채가 아니다 ·
`docs/candidates.md` 없음 · `docs/patches/` 없음 · `digest ## 보류 (승인 대기)` 절이
비어 **0건** · `gh issue list --state open` **0건 rc 0**(조회만, PR 무접촉).

**6순위의 더 높은 점수는 전부 「여는 조건 미도래」다** — `[9]` `/search` 몫 · `[8]`
숨은 텍스트 뒷절반 · `[8]` 토크나이저는 실물 코퍼스/재색인, `[7]` macOS pycache 는
처방이 이미 들어갔고, `[7]` 재파싱 몫 배정과 `[7]` 키셋 페이지네이션은 사람 결정,
`[6]` 캡 하향 · `[6]` `_IMPLIED_END` 표 · `[6]` `extract_blocks` 이름표는 각각
「캡을 내리는 날」·「표를 손으로 고치는 날」·「실물 코퍼스」다. **여는 조건이 실제로
온 항목은 `[6]` 하나이고, 그것을 오게 만든 것이 어제 닫힌 계획 61 이다.**

## 착수 탐침 — 기록된 답을 다시 쟀고 이번엔 맞았다

`digest [7]` 의 **열세 번째 적용**. 저장소 파일은 한 바이트도 안 고치고 모듈 속성과
메서드를 **메모리에서** 갈아 끼워 전수를 돌렸다(하네스는 저장소 밖 · 이 phase 내내
`git status --short` 는 문서 편집 전까지 빈손).

| 변이 | 결과 |
|---|---|
| **M0** 무변이 대조군 | `Ran 618 · 실패 0` — 죽은 단언 0 |
| **M1** `ITER_LINE` 앵커 제거 | `Ran 618` — **생존**(죽은 단언 0) |
| **M2** `DocHeadTest` 판정 `^# \S` → `^` | `Ran 618` — **생존**(죽은 단언 0) |
| **M3** 양성 대조, 같은 판정을 `^ZZZ` 로 | **실패 3**(subTest 셋) |

**M3 이 붙든 것**: 패치가 실제로 그 메서드에 꽂혔다는 증거다 — M2 가 안 죽는 것은
배선 탓이 아니라 판정이 정말 안 재지고 있기 때문이다(`digest [6]`「탐침의 배선을
먼저 의심한다」). 제안 리터럴이 갈래를 가르는 것도 미리 쟀다: `"x iteration: 1"`·
`"iteration: 1x"` 는 앵커가 있으면 매치 없음이고 M1 이면 둘 다 매치 · `"## 완료"`·
`"#제목"`·`"# "`·`""`·`"- [6] **항목**"`·`"  # 들여쓴 머리"` 여섯은 `^# \S` 가 전부
거절하는데 M2 면 여섯 다 통과한다.

## 설계 생략 — 트리거 0

새 모듈·파일 0 · 제품 인터페이스 무변(`src/` 0줄) · 데이터 구조 무변 · 파일 2개 ·
되돌리기는 커밋 하나 revert. **대안이 갈리는 자리 하나**(상수+리터럴 vs 순수 함수
`head_gap`)는 저장소의 **선례**가 닫았다 — 정규식 축은 `CITATION` +
`CitationPatternTest`·`ITER_ROW` 가, 두 문서를 대조하는 판정 축은 `step_gap`·
`iter_gap` 이 각각 관용구를 정해 두었다. 여기는 정규식 축이라 뺄 몸통이 없다
(껍데기만 는다 — ponytail 사다리 1번).

## 다음

**개발 1/1.** `tests/test_docs.py` 에서 ① `IterationPatternTest` 에 리터럴 두 줄을
더하고 ② `r"^# \S"` 를 모듈 상수 `DOC_HEAD` 로 올려 `DocHeadPatternTest`(CAUGHT 3 ·
NOT_CAUGHT 6)를 세운다. `rules/dev.md` 0절대로 **RED 를 눈으로 먼저 본다**.
건드릴 파일은 `tests/test_docs.py`·`README.md`(단위 건수 줄) 둘뿐이고, 여기 없는
파일을 고쳐야 하면 YELLOW 다. 완료 기준 7개는 계획서 4절에 있다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61 의 커밋이 `loop/passage-cost-band` 에 쌓여
  있고 `origin/main`(`d1fe3e9`) 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 반복 360 커밋(`d763317`)은 원격에 정상 반영돼 있다(`git ls-remote origin
  loop/passage-cost-band` = `d763317c9d2f…`). 이번 커밋도 같은 브랜치에 그대로 쌓는다
  — `--force`·`--amend`·`rebase` 없음.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `docs/digest.md` 는 실측 **200줄**(상한 200 정각)이다 — 후보 `[6]` 에 줄을 더하지
  않고 **같은 줄 끝에** 연 사실만 이어 붙였다. 다음에 한 줄이라도 더해야 하면
  `rules/docs.md` 3절대로 **완료 항목부터** 지운다.
- 회전은 없다 — `history_current.md` 는 **177줄**(상한 300), 다음 회전 번호는
  `history_064.md` 다.
