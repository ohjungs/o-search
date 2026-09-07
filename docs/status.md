---
signal: GREEN
phase: 테스트
step: 2/2
attempt: 0
iteration: 419
updated: 2026-09-07
ctx: 79
night_iterations: 5
night_red: 0
night_retries: 0
plan: digest-rotate-guard
---

## 현재 상태

**테스트 phase 완료 — 갭 탐색 6종 + 변이 탐침 1판. 전수 648 OK rc 0.**
새로 쓴 테스트는 없다. 이 phase 가 물어야 할 것은 **「못을 옮긴 것이 단언을 낮춘 것은
아닌가」**(`test.md` 6절)였고, 그것을 말이 아니라 변이로 쟀다.

## 변이 탐침 — 옛 못을 지운 자리가 비어 있지 않다

`STRIKE_POINTER_FLOOR`(9)를 지웠으므로, 그 못이 혼자 지키던 축이 있었다면 지금은
구멍이다. 그 축은 **「`STRIKE_POINTER` 정규식이 무력화되면 운다」**였다. 정규식을
`열었다` → `개봉했다` 로 바꿔 실물 포인터를 0 으로 만들었다:

| 결과 | **3건 RED** — `StrikeGapTest` 셋 |
|---|---|
| | `test_only_candidate_list_lines_are_counted` |
| | `test_pointer_to_an_unlisted_plan_is_a_gap` |
| | `test_unstruck_closed_candidate_is_a_gap` |

**합성 셋이 그 축을 이미 물고 있다.** 옛 못이 유일한 파수꾼이 아니었으므로 제거는
단언을 낮춘 것이 아니다 — 설계가 「옮겼다」고 적은 것이 실측으로 맞다. (탐침은 커밋
안 함 · 원복 확인)

## 갭 탐색 결과 — 8점 이상 0건, 등재 2건

| # | 갭 | 점수 | 처리 |
|---|---|---|---|
| 1 | `rules/docs.md` 3절 문서 상한(200·300)을 재는 자가 **0개** | **7** | digest 등재 |
| 2 | `candidate_heads` 접두 일치가 「후보…」 절 추가에 가려진다 | **4** | digest 등재 |

**1번이 오늘 사고 자신이다.** digest 가 216줄까지 자라는 동안 전수 647건이 조용했고
넘긴 것을 발견한 것은 사람의 눈이었다. **8점이 아닌 이유는 처방이 무인 루프를
교착시켜서다** — 상한 초과를 RED 로 만들면 야간이 그 RED 를 스스로 못 푼다(digest
회전은 **삭제**라 위임이 필요했다). history 회전은 **아카이브로 밀어내는** 것이라
성질이 다르고, 그쪽만 먼저 못 박는 답이 있을 수 있다 — 여는 조건에 적었다.

## 같은 반복에 `history_current.md` 를 회전했다 (별도 커밋)

갭 1 을 재다가 **352줄**(상한 300)을 발견했다. 계획 72 는 「이 계획의 대상이 아니다」로
적어 뒀지만 **회전은 계획이 아니라 매 반복의 기록 의무**(`rules/docs.md` 3절)이고,
오늘 루프가 이미 두 번 한 일이다. 반복 404~413 을 `history_072.md` 로 밀어냈다 —
**352 → 121줄**. 계획서가 미루라고 한 것과 갈리므로 커밋을 나눴다.

- 옮긴 것은 원본 그대로다(수정 0). 남긴 것은 반복 414 부터.
- `digest.md` 에 회전 기록 1줄 + 아카이브 명부에 `history_072.md` 등재
  (`ArchiveIndexTest` 가 이 등재를 붙든다).
- `digest.md` 는 **196줄** — 갭 등재 2줄과 회전 기록 1줄을 더하고도 상한 아래다.

## 다음 — 리뷰 phase

볼 자리 셋을 미리 적어 둔다:
① **회전이 지운 25줄이 정말 닫힌 기록뿐이었나** — `index.md`·`plan_history_*` 대조.
② **위임 범위 문장이 문서 넷에서 같은 말을 하는가**(status·history·계획서·커밋 메시지).
③ **설계 6절과 구현의 의도적 이탈**(`candidate_lines` 분리를 안 만든 것)이 설계 문서
   쪽에도 적혀 있는가 — 지금은 계획서와 status 에만 있다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 648 tests in 15.923s · OK · rc 0
```

`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `index.md`·`plan_history_*` 무접촉 ·
`data/crawl.db` 무개봉 · 바깥 네트워크 0 · `main` 직접 커밋 0 · 브랜치 `loop/digest-rotate-guard`.
