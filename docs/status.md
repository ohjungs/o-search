---
signal: DONE
phase: e2e
step: 2/2
attempt: 0
iteration: 421
updated: 2026-09-07
ctx: 84
night_iterations: 7
night_red: 0
night_retries: 0
plan: digest-rotate-guard
---

## 현재 상태

**e2e 통과 — 계획 72 DONE.** 저장소 밖 사본에서 **5막**, 전부 기대대로다.
전수 **648 OK rc 0** · `ls e2e/*.py` **21** 그대로 · 결과는
`docs/e2e/digest-rotate-guard/result.md`.

| 막 | 편집 | 기대 | 실측 |
|---|---|---|---|
| ① | **마감 편집 리허설** (`index.md` 완료 + e2e 판정 + 후보 `[5]` 취소선) | OK | **648 OK rc 0** |
| ② | 후보 첫 절 머리 드리프트 | RED | **1건** `test_candidate_heads_still_found` |
| ④ | 완료로만 바꾸고 **취소선 안 달기** | RED | **1건** `test_closed_candidates_are_struck_through` |
| ③ | 지워진 26줄의 엄격 포인터 10개 원본 대조 | 10/10 | **`index.md` 10/10 · `plan_history_*` 10/10** |
| ⑤ | 회전된 후보 두 절 정적 실측 | 닫힌 항목 0 | **62줄 · 취소선 0 · 포인터 1(진행) · gap None** |

**①과 ④가 짝이라 이 phase 가 의미를 갖는다.** 같은 마감 편집을 취소선 유무만 갈라
두 번 했고 하나는 초록, 하나는 빨강이다 — 가드가 파이프라인에서 **실제로 도달한다**.
막 ②는 회전 전이라면 **조용한 초록**이었을 편집이다. 그것이 이 계획의 전부다.

## 아카이브가 할 일 (다음 반복 · 문안은 막 ①이 이미 씀)

1. `index.md` 행 → `완료` · e2e 칸에 판정. 2. `digest.md` 후보 `[5]` 에 취소선 +
닫힘 사유. 3. 계획·설계 문서를 `plan_history_<NNN>.md`·`design_history_<NNN>.md` 로.
4. `digest.md` `## 완료` 에 계획 72 요약 1줄.

**취소선의 뜻을 좁게 적는다** — 「상수(`STRIKE_POINTER_FLOOR`)가 사라졌다」이지
「문구 드리프트가 닫혔다」가 아니다. 살아남은 축은 후보 `[6]` 이 오늘의 말로 들고 있고,
`[5]` 의 닫힘 사유가 `[6]` 을 가리킨다. **열린 위험을 취소선 밑에 묻지 않는 것**이
이 계획이 마지막으로 지켜야 할 것이다.

## 사람 몫 — 야간이 못 넘는 자리

- **digest 회전 위임은 이 건 한 번이었다.** `rules/docs.md` 3절 문장은 안 바뀌었고
  다음 회전은 다시 사람에게 묻는다. 오늘 `digest.md` 는 **197줄**(상한 200)이라
  **여유가 세 줄**이다 — 다음 반복의 등재 한 줄이면 다시 넘는다.
- **후보 `[7]`**(문서 상한을 재는 자가 0개)의 여는 조건이 바로 그 결정이다 —
  「무인이 digest 를 회전해도 되는가」. 정해지면 못을 세울 수 있다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 648 tests in 15.9s · OK · rc 0
```

**안 잰 것을 「통과」로 적지 않았다**: 경량·성능·디자인은 **해당 없음**(제품 코드 0줄),
린트·타입체크는 저장소에 설정이 없어 **검증되지 않음**.
`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `plan_history_*` 무접촉 ·
`data/crawl.db` 무개봉 · 바깥 네트워크 0 · `main` 직접 커밋 0.
