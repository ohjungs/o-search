---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 357
updated: 2026-09-06
ctx: 45
night_iterations: 174
night_red: 2
night_retries: 2
plan: iter-gap-cover 계획 61 (개발 1/1 완료 — 반복 축 판정을 iter_gap 으로 뺐다 · 다음은 테스트 phase)
---

## 현재 상태

**계획 61 개발 1/1 을 끝냈다.** 반복 축 판정이 `IterationSyncTest` 메서드 안에 박혀
실물 문서 위에서만 돌던 것을 순수 함수 `iter_gap(status_text, metrics_text)` 로 뺐고,
갈래 넷을 합성 문자열로 밟는 `IterGapTest` 를 세웠다. 만진 파일은 계획서 5절이 그은
대로 `tests/test_docs.py` 와 `README.md`(건수 줄) **둘뿐**이고
`src/`·`e2e/`·`docs/specs/`·`data/crawl.db` 는 무접촉이다.

`step_gap`(계획 60)과 **같은 모양으로 맞췄다** — 인자 순서(`status` 가 먼저) · 어긋난
자리를 한 줄 문자열로 돌려주고 없으면 `None` · 호출부는 `assertIsNone(gap, gap)` 세 줄.
새 추상화는 만들지 않았다(`step_gap` 과 합치는 일반화는 계획서 5절이 거부한 그대로다).

## TDD — RED 를 눈으로 먼저 봤다

함수 없이 `IterGapTest` 만 넣고 전수를 돌려 **`NameError: name 'iter_gap' is not
defined` ×4** 와 `README` 건수 실패 `(614, 21) != (618, 21)` 를 확인한 뒤 구현했다.
구현 후 전수 `Ran 618 tests in 15.891s · OK · rc 0`(맨몸).

## 갈래 넷과 변이 재측 — 4/4 사망

| 변이(메모리) | 죽은 단언 | 판정 |
|---|---|---|
| 대조군 | 0 | 기준선 618 OK |
| M1 대조를 자기비교로 | `test_iteration_mismatch_is_reported` | **의도한 하나만** |
| M2 `metrics` 가드 삭제 | `test_missing_metrics_row_is_reported` | **의도한 하나만** |
| M3 `status` 가드 삭제 | `test_missing_status_line_is_reported` | **의도한 하나만** |
| M4 판정 통째 삭제(양성 대조) | 3건 | 계획서 기준 「셋 이상」 충족 |

착수 탐침에서 **넷 다 살아 있던 것이 넷 다 죽는다.** 변이가 전부를 한꺼번에 죽이지
않는다는 것이 갈래를 실제로 갈랐다는 증거다(완료 기준 1의 「이름으로 확인」).

## 다음

**테스트 1/1.** 새 `iter_gap`·`IterGapTest` 위에서 갭을 탐색한다. 완료 기준 여섯 개 중
1~5 는 오늘 실측으로 충족했고, 6(`status`↔`index` 스텝 축 · `StepSyncTest`)은 이 커밋이
`index.md` 행을 `1/1` 로 함께 올려 닫는다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60·61 의 커밋이 `loop/passage-cost-band` 에 쌓여
  있고 `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- 변이는 **저장소 밖에서** 건다 — 스크래치패드 하네스가 `mock.patch.object` 로
  `test_docs.iter_gap` 을 갈아 끼웠고 저장소 파일은 무접촉이다.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- `history_current.md` 가 **300줄로 상한에 닿았다** — 다음 append 가 넘기므로 그때
  `history_063.md` 로 회전한다.
