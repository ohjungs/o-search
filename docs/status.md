---
signal: GREEN
phase: 리뷰
step: 0/1
attempt: 0
iteration: 347
updated: 2026-09-05
ctx: 55
night_iterations: 164
night_red: 2
night_retries: 1
plan: endtag-cut-cover 계획 59 (테스트 1/1 완료 · 8점 이상 갭 0건 · 다음은 리뷰 phase)
---

## 현재 상태

**계획 59 테스트 1/1 을 끝냈다 — 새 갭 1건을 찾았고 점수가 4점이라 이번 스텝에서는 안
고친다.** 이 계획은 `src/` 0줄이라 테스트 phase 가 볼 것은 「빠뜨린 것이 있나」 하나였다.
고친 파일 **0개**(문서만). 남은 완료 기준은 6번(e2e)뿐이다.

## 테스트 1/1 — 파서의 두 스택을 메모리 변이 6종으로 훑었다

`handle_endtag`·`handle_starttag` 의 줄마다 변이를 하나씩 걸고 **전수 605건**을 돌려
「죽이는 단언이 몇 건인가」를 셌다. 변이는 전부 `mock.patch.object` 로 메모리에서만
걸었고 저장소 파일은 안 건드렸다.

| 변이 | 죽는 테스트 | 판정 |
|---|---|---|
| 무변이 대조군 | `Ran 605` · **failures 0 · errors 0** | — |
| G1 `if tag in self._open` 가드 삭제 | **45건**(실패 6 + 에러 39) | 여유 충분 |
| G2 `_open` 을 꼭대기만 버린다 | 2건 | 여유 충분 |
| G3 `_open` 자르기 off-by-one | 3건 | 여유 충분 |
| G4 `_open` 을 **앞에서부터** 찾는다 | **1건** | **얇다 — 새 갭** |
| G5 암묵적 닫기 `while` → `if` | 8건 | 여유 충분 |
| G6 암묵적 닫기에서 `_open` 안 걷는다 | **1건** | **얇다 — 같은 갭** |

## 새 갭 1건 — 4점이라 `digest.md` 로 보냈다

G4·G6 은 계획 59 가 오늘 닫은 `_els` 쪽과 **정확히 같은 「한 칸」 모양**이다. 그런데
점수가 낮다: `extract_blocks()` 가 내는 `(태그, 본문)` 의 **태그를 읽는 곳이 저장소에
0곳**이다 — 제품 `src/websearch/indexer.py:334` 과 `e2e/passage_eval.py:93` 이 둘 다
`_tag` 로 버리고, 읽는 것은 `tests/test_extract.py` 뿐이다. 이름표가 틀려도 색인·검색·
문단 어디에도 안 보이므로 **사용자에게 보이는 오류를 못 낸다**(룰 4절 7-8점 밖).
여는 조건은 「태그를 처음 읽는 소비자가 생길 때」이고, 그때 볼 것은 단언을 더하는 쪽이
아니라 `_open` 을 **지울 수 있는지**다. `digest.md` `## 다음 계획 후보 (테스트 phase 갭,
8점 미만)` 에 `[4]` 로 등재했다.

## 검증 (전부 실측 · 맨몸)

- 전수 `PYTHONPATH=src python3 -m unittest discover -b tests`:
  **`Ran 605 tests in 13.765s` · `OK` · rc 0**.
- 완료 기준 3 재확인 — 어제 더한 `안 닫힌 span` subTest 와 반대 방향 한 줄이 원본에서
  초록이다(위 무변이 대조군 failures 0).
- **단언을 낮춘 곳 0** — 개발 diff 가 `+12줄` 순수 추가라 지운 단언도 느슨해진 단언도 없다.
- 고친 파일 **0개**(`git status --short` 가 `docs/` 셋뿐) · 제품 `src/` 0줄.

## 다음 — 리뷰 phase 0/1

## 병합 · 규율

`loop/passage-cost-band` 위에 그대로 쌓는다(`origin/main` `d1fe3e9` 와 갈라진 채 · 열린 PR 0).
러너 규율 위반 이번 반복 **0회**(누적 37) — 판정 줄과 `rc` 를 매번 맨몸으로 봤다.
