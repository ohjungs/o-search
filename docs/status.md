---
signal: GREEN
phase: 리뷰
step: 2/2
attempt: 0
iteration: 420
updated: 2026-09-07
ctx: 82
night_iterations: 6
night_red: 0
night_retries: 0
plan: digest-rotate-guard
---

## 현재 상태

**리뷰 2/2 완료 — 6건 발견, 5건 확증(전부 자동 수정), 1건 기각. 승인 필요 0.**
전수 **648 OK rc 0**. 백지 패스(패스 A)를 **별도 세션**에 넘겼고 넷을 받았다.

## 백지 패스가 준 넷 — 셋 확증, 하나 기각

| # | 준 것 | 판정 |
|---|---|---|
| 1 | 못을 옮기며 **실물 포인터 모집단을 재는 자가 0**이 됐는데 등재가 없다 | **확증** |
| 2 | 후보 `[5]` 표제가 **삭제된 상수**(`STRIKE_POINTER_FLOOR`)를 가리킨다 | **확증** |
| 3 | `STRIKE_POINTER` 주석의 실측(11자리/9포인터)이 회전으로 낡았다 | **확증** |
| 4 | diff 단독으로는 README 건수 대조가 RED | **기각** |

**4 는 필터된 diff 만 본 탓의 오탐이다** — README 의 `647 → 648` 은 같은 커밋(반복 417)에
들어 있다. 배경을 안 준 대가이고, 규율대로 확인하고 버렸다.

**1 과 2 는 같은 자리다.** 별도 세션이 `candidate_pointers` 를 `return []` 로 죽여
`StrikeSyncTest` 2건이 그대로 통과하는 것을 실측했다. 계획 72 가 닫은 것은 「하한이
회전에 밟힌다」이고, **「문서 문구가 드리프트하면 조용하다」는 축은 살아 있다.**
옛 `[5]` 는 이제 없는 상수를 표제로 들고 있어 그 축을 대신 지고 있을 수 없다 —
**오늘의 말로 새 후보 `[6]` 을 열었다**(여는 조건: 후보 줄 규약을 새로 쓰는 계획, 또는
같은 오염이 두 번째로 나는 날). 옛 `[5]` 는 계획 72 가 `완료` 가 되는 e2e 스텝에서
취소선을 받는다 — **그때 열린 위험이 함께 묻히지 않게 하는 것이 `[6]` 이다.**

## 패스 B 가 더한 둘 (렌즈 1 — 약속 준수)

- **설계 6절과 구현의 이탈이 설계 문서에 없었다.** `candidate_lines` 분리를 안 만든
  사유가 계획서와 status 에만 있었다. 룰은 「계약을 바꿨으면 설계 문서도 함께 고친다」다.
  → 설계 6절에 인용 블록으로 적었다. **문단을 지우지 않았다** — 설계가 무엇을 예상했고
  어디서 틀렸는지가 기록이다.
- **계획서의 「`index.md` 무접촉」이 문자 그대로는 거짓이었다.** 이 계획 자신의 행은
  등재했고 스텝 칸도 반복마다 갱신했다(`StepSyncTest` 가 status 와 대조하므로 필수다).
  지키고 있는 것은 **「남의 행을 안 건드린다」**이고 실측도 그렇다 — 이 브랜치의
  `index.md` diff 는 **자기 행 한 줄뿐**이다. 계획서 문장을 그렇게 정정했다.

## 고친 것 (전부 자동 수정 · 승인 필요 0)

- `tests/test_docs.py` `STRIKE_POINTER` 주석 — 회전 뒤 실측(2자리 중 1포인터)으로 갱신하고
  **이 수는 회전이 흔든다**는 사실을 적었다. 못을 여기 세우면 안 되는 이유 자체다.
- `docs/digest.md` — 후보 `[6]` 신설(살아남은 축). **197줄**, 상한 아래.
- `docs/design_digest-rotate-guard.md` 6절 — 의도적 이탈 명시.
- `docs/plan_digest-rotate-guard.md` 「하지 않을 것」 — 무접촉 문장 정정.

## 다음 — e2e phase (마지막 스텝)

`docs/e2e/digest-rotate-guard/result.md` 에 시나리오 셋을 실측한다. 그중 하나는
**옛 후보 `[5]` 에 취소선을 다는 편집**이고, 그 편집이 `strike_gap` 을 초록으로
유지하는지(계획 72 가 `완료` 로 바뀐 뒤에도) 확인하는 것이 이 계획의 마지막 못이다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 648 tests in 15.904s · OK · rc 0
```

`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `index.md` 남의 행 무접촉 ·
`plan_history_*` 무접촉 · `data/crawl.db` 무개봉 · 바깥 네트워크 0 ·
`main` 직접 커밋 0 · 브랜치 `loop/digest-rotate-guard`.
