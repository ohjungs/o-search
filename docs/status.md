---
signal: GREEN
phase: 테스트
step: 0/1
attempt: 1
iteration: 346
updated: 2026-09-05
ctx: 50
night_iterations: 163
night_red: 2
night_retries: 1
plan: endtag-cut-cover 계획 59 (개발 1/1 완료 · 다음은 테스트 phase)
---

## 현재 상태

**계획 59 개발 1/1 을 끝냈다 — 고친 파일은 `tests/test_extract.py` 하나(+12줄), 제품
`src/` 0줄.** 이 반복은 **재시도 1회차**다: 앞 에이전트가 같은 스텝에서 10분간 변경 0건으로
죽어(커밋 0·작업 트리 깨끗) 처음부터 다시 돌았고, 이번엔 전수(14초)와 변이 측정을
**작은 단위로 쪼개** 돌렸다(변이는 `test_extract.py` 만, 메모리에서).

## 개발 1/1 — 자르기를 붙드는 단언을 표와 무관한 축으로 하나 더 세웠다

`_BlockParser.handle_endtag` 의 `del self._els[i:]`(닫는 태그가 **자손까지** 자른다)를
붙드는 단언은 subTest **한 칸**(`안 닫힌 li`)뿐이었고, 그 한 칸은 `_IMPLIED_END` 표의
`li` 줄에 얹혀 있었다 — 표가 바뀌면 자르기가 조용히 살아난다.

`tests/test_extract.py` 의 `test_an_unclosed_child_does_not_pin_a_hidden_region_open`
목록에 **`("안 닫힌 span", "<div hidden><span>숨은</div><p>보이는 김치찌개</p>")`** 를
더했다. `span` 은 `_IMPLIED_END` 에 **아예 없어** 뒤따르는 시작 태그가 대신 안 닫아 준다.
루프 뒤에는 **반대 방향** 한 줄(`<section><span>가</section><p>나</p>` → `["가", "나"]`)을
붙였다 — 「닫는 태그가 뒤를 다 버린다」가 위 단언들을 전부 통과하는 것을 막는다.

## 검증 (전부 실측 · 맨몸)

- **변이 측정은 메모리에서** — `mock.patch.object` 로 `handle_endtag`(M-a) 와
  `_IMPLIED_END`(li 줄 삭제)를 바꿔 끼웠다. 저장소 파일은 한 번도 안 건드렸다.
- 완료 기준 2 — M-a(`del self._els[i:i+1]`): **더하기 전 `failures=1`**(`안 닫힌 li`)
  → **더한 뒤 `failures=2`**, 늘어난 것이 `(shape='안 닫힌 span')` 이다(이름으로 확인).
- 완료 기준 3 — 원본에서 초록(오탐 0). 반대 방향 줄도 함께 돈다.
- 완료 기준 4 — `_IMPLIED_END` 에서 `li` 줄을 지우는 변이: 죽는 것은
  `test_an_optional_end_tag_does_not_hide_the_next_sibling` 의 `li`·`li 안의 안 닫힌 p`
  둘뿐이고 **새 subTest 는 초록**이다 → 새 단언은 표 축에 안 얹혀 있다.
- 완료 기준 1 — 전수 `PYTHONPATH=src python3 -m unittest discover -b tests`:
  **`Ran 605 tests in 13.819s` · `OK` · rc 0**. subTest 라 **건수 605 무변**,
  그래서 `README.md`(104줄 `단위 605건`) 무접촉.
- 완료 기준 5 — `git status --short` 가 `M tests/test_extract.py` 하나(+`docs/`).

## 다음 — 테스트 phase 0/1

남은 완료 기준은 6번(e2e 21종 전수 rc 0 · 기준선 회귀 0)뿐이고 그것은 e2e phase 몫이다.
테스트 phase 는 이 계획이 `src/` 0줄이라 **새 갭이 있는지만** 본다.

## 병합 · 규율

`loop/passage-cost-band` 위에 그대로 쌓는다(`origin/main` `d1fe3e9` 와 갈라진 채 · 열린 PR 0).
러너 규율 위반 이번 반복 **0회**(누적 37) — 판정 줄과 `rc` 를 매번 맨몸으로 봤다.
