---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 224
updated: 2026-09-01
ctx: 62
night_iterations: 84
night_red: 0
night_retries: 0
plan: focus-ring-presence
---

# 현재 상태

**계획 44 `focus-ring-presence` 개발 1/1 완료 — 다음 반복은 테스트 phase 다.**
설계서 `docs/design_focus-ring-presence.md` · 계획서 `docs/plan_focus-ring-presence.md` ·
브랜치 `loop/focus-ring-presence` · 기점 `bc40ea9`. 제품 코드 **0줄**(검사기와 단위만).

## 방금 것 (2026-09-01 · 개발 1/1)

**검사기가 이제 색을 재기 전에 링을 그리는 규칙을 읽는다.** `e2e/design_check.py` 에
`focus_rule(css)` + `RULE_RE`·`OUTLINE_RE`, `check_contrast` 는 그것을 부른 뒤 성공하면
요약 줄을 찍고 비텍스트 짝을 재고, **`ValueError` 면 사유만 담고 안 잰다.** 텍스트 7짝 ×
2맵은 어느 쪽이든 잰다. 제품 CSS 실행에 새 줄 하나가 늘었다:

```
포커스 링 규칙 1개 · outline var(--focus) · offset 2px
```

**TDD 로 갔고 RED 를 눈으로 봤다.** 단언 7건을 먼저 쓰고 돌리니 **여섯 변이가 전부
`unmeasurable` 0건**으로 통과했다 — 착수 탐침이 적어 둔 *"여섯이 다 산다"* 를 이 반복이
직접 다시 잰 것이다(`rules/dev.md` 0절이 요구하는 그 확인). 구현 뒤 여섯 다 잡힌다.

**계약 9항을 전부 이행했다.** 상수 `PAIRS`·`NONTEXT_PAIRS`·`NO_PAIR`·
`MIN_CONTRAST_NONTEXT` 와 커버리지 강제(`paired`)는 무변경 · `NONTEXT_PAIRS` 주석은
단언에서 포인터로 · `src/websearch/serve.py` **0줄** · `design_check.py` 는 계속 rc 0.
**`NO_PAIR["--line"]` 의 오기도 고쳤다** — `(다크도 1.08:1)` → **`(다크도 1.27:1)`**
(다크 `--line`/`--bg-input` 실측). 판단 보류 문장은 안 건드렸다.

**계약에 없던 둘을 정직하게 적는다.**

1. **`:focus` 셀렉터 조건에 다섯 번째 메시지를 만들었다.** 설계 첫 문단은 조건을 넷으로
   세는데(규칙 1개 · `:focus` · 재는 토큰 · offset > 0) `## 계약` 5항의 메시지는 네
   갈래이고 그 넷이 조건 1·3·3·4 를 덮는다 — **`:focus` 조건만 메시지가 없었다.**
   조건을 버리는 대신 메시지를 하나 더 만들었다(`outline 을 정하는 유일한 규칙이
   포커스용이 아니다: <셀렉터>`). 지금 변이 11종 중 여기 걸리는 것은 없다.
2. **`README.md ## 검증` 의 단위 수 473 → 475.** `tests/test_readme.py` 가 실제 수와
   대조하므로 안 고치면 그 자리가 RED 다. 계약이 안 적었지만 계약을 지키면 반드시 걸린다.

## 다음 반복이 할 것 — 테스트 phase

개발 스텝은 설계가 1개로 정했고 그 1개가 끝났다. **단위는 이미 7건이 붙어 있다**
(요약 줄 1 + 변이 6). 테스트 phase 는 그 7건이 **무엇을 못 붙드는지**를 보는 자리다 —
후보는 V8(뒤 규칙 `outline-width:0`)·V10(다크 블록 안 `outline:none`)이다. 설계가
"규칙 수 세기 하나에 셋 다 걸린다" 고 적었지만 **단위로는 V7 하나만 재 놓았다.**

## 기점 — 원격 갈라짐은 닫혀 있다 (2026-09-01 확인)

`origin/main` 은 `494313b`(PR #5 병합)이고 그 트리는 `bc40ea9` 의 부모와 같다.
**남은 것 (사람 결정)**: `bc40ea9`(반복 221 기록) 와 이 계획의 커밋들을 `main` 으로
보내는 PR. 무인 모드는 병합하지 않는다.
**웹 UI 의 *Update branch* 는 여전히 누르지 않는다** — `main` 이 rebase-merge 로 해시가
새로 쓰인 뒤의 그것은 머지가 아니라 복제다(PR #3 을 깨뜨린 원인).

## 사람이 정할 것 ② — 셋 중 둘이 열려 있다

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
   `NO_PAIR` 사유가 판단 보류를 적어 두고 있다 — 이 반복은 숫자 오기만 고쳤다.
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1). **이제 "가정" 이 아니라
   "검사기가 붙들고 있는 조건" 이다** — 그 배경은 `outline-offset` 이 0 일 때만 링의
   이웃이 되고, 이번 개발로 **검사기가 매 실행 offset > 0 을 확인한다**(제품 실측 2px,
   요약 줄에 찍힌다). 짝을 지금 늘리면 그 자리에서 rc 1 이고 색을 바꿔야 하므로 계획이
   커진다 — **안 늘린다.** offset 이 0 이 되는 날 검사기가 rc 2 로 멈추고, 짝을 정하는
   것은 그때 열릴 계획의 일이다.
3. **기록 3파일 불일치가 5회째 재발** — 처방은 `tests/test_docs.py` 에 검사 한 줄
   (`metrics.md` 의 누적 반복 수와 `status.md` 의 `iteration` 이 어긋나면 죽는다).
   **다음 계획의 1순위 후보로 남아 있다**(계획서 5절).

## 한도 (매 반복 확인)

- `main` 직접 커밋 금지 · `--no-verify` 금지 · 외부 네트워크 금지 ·
  `docs/specs/` 읽기만 · `data/crawl.db` 무변경 · 의존성 추가 금지(stdlib 만).
- **검증은 맨몸으로 — 이 반복이 그것을 깼다. 러너 파이프 1회, 연속 카운트는 0 이다.**
  README 의 단위 수를 고친 뒤 `... discover tests 2>&1 | tail -5` 를 돌렸고 **판정 줄과
  종료 코드가 잘려 출력이 통과처럼 보였다** — `project.md ## 명령` 이 경고한 그 모양이고
  방아쇠도 그 파일이 적어 둔 *"이미 초록일 것 같은 실행"* 이었다. 즉시 맨몸으로 다시
  돌려 475건 OK 를 확인했다. **네 반복 연속 0회가 끊겼으므로 `digest` 의 그 항목을
  안 접는다.** 다시 네 반복을 채워야 닫는 조건이 선다.
- 이번 반복 실측(전부 맨몸): `PYTHONPATH=src python3 -m unittest discover tests`
  **475건 OK 11.940초** · `PYTHONPATH=src python3 e2e/design_check.py` **4축 전부 통과**
  (요약 줄 `포커스 링 규칙 1개 · outline var(--focus) · offset 2px` · `--focus` 라이트
  3.56:1 · 다크 11.14:1) · `PYTHONPATH=src python3 e2e/pagination_ui_e2e.py` **통과**.
- `docs/digest.md` 200줄 상한 · 열린 항목 **49** · `history_current.md` 300줄 상한 —
  지금 **195줄**로 여유가 있다.
