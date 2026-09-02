---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 278
updated: 2026-09-02
ctx: 60
night_iterations: 116
night_red: 1
night_retries: 0
plan: focus-rule-scope
---

# 현재 상태

**계획 49 `focus-rule-scope` 의 개발 2/2 — 조건 6(at-rule 위치)을 넣어 ⓐⓑ 를 죽였다.
개발 phase 는 이것으로 끝이다.**
`e2e/design_check.py` +21 −5 · `tests/test_design_check.py` +39 −0 · `README.md` +1 −1 ·
제품 `src/` **0줄**. 브랜치 `loop/focus-rule-scope`.

단위 **577건 OK**(맨몸 13.415초 실측 · 576 → 577) ·
`PYTHONPATH=src python3 e2e/design_check.py` **종료 0** ·
`e2e/pagination_ui_e2e.py`(design_check 를 프로세스로 부르는 유일한 e2e) **종료 0** ·
`data/crawl.db` 무변경 · `docs/specs/` 무변경.

## 무엇이 바뀌었나 — 5줄

```python
COMMENT_OR_STRING_RE = re.compile(r"/\*.*?\*/|\"[^\"\n]*\"|'[^'\n]*'", re.S)
css = COMMENT_OR_STRING_RE.sub("", css)        # focus_rule 첫 줄
before = css[:rules[0].start()]
if before.count("{") != before.count("}"):
    raise ValueError("… at-rule 안에 있다 — 라이트 화면에 늘 그려지지 않는다")
```

`RULE_RE.findall` → `finditer` 로 바꾼 것이 딸린 수정 2줄이다(규칙의 **위치**가 필요해졌다).
`focus_rule` 의 반환·예외 모양은 그대로 — 공개 인터페이스 변경 0.

**설계서는 3줄로 잡았는데 5줄이 됐다.** 늘어난 둘이 주석·문자열 지우기다. 설계 6절은 그것을
천장으로 적어 두고 *"그런 CSS 는 0곳이고 생기면 규칙 수가 틀려 종료 2 로 멈춘다"* 로 넘겼는데,
실측해 보니 **멈추는 쪽이 아니라 거짓 양성 쪽**이었다: `/* 여는 것 { 하나 */` 와
`content:"}"` 는 정상 CSS 인데도 세기를 어긋내 「at-rule 안」이라는 거짓 판정을 낸다.
2줄로 닫히고 검사기를 못 도는 것보다 도는 것이 낫다고 보고 닫았다. CSS Nesting 은 천장에
그대로 남는다(`RULE_RE` 옆 `ponytail:` 주석을 실제 동작에 맞춰 고쳤다).

## TDD — RED 를 눈으로 봤다

테스트를 먼저 쓰고 돌렸다. ⓐⓑ·F3·F4 넷이 전부 **`unmeasurable` 0건 · 종료 0** 으로
살아남으며 무효가 된 `라이트 --focus on --bg-page 3.56:1 / 기준 3.0 OK` 를 화면에 찍었다
(`FAILED (failures=4)`). 구현 뒤 `Ran 577 tests in 13.415s / OK`.

같은 반복에 **오탐 표도 먼저 썼다** — 그 표는 RED 때 이미 초록이었고, 그것이 이 표의 일이다.
순진한 중괄호 세기를 넣는 순간 빨개지는 자리를 미리 박아 둔 것이라, 아래 변이 M3 이 그걸 증명한다.

## 커밋된 검사 — 참 양성 넷 · 거짓 양성 다섯

기존 `test_ring_that_is_not_drawn_is_unmeasurable` 에 subTest 넷을 더했다(ⓐ 다크 `@media` ·
ⓑ `@media print` · F3 `@media (forced-colors:active)` · F4 `@layer`). **F3·F4 도 박은
이유**는 그 둘이 후보 C 를 고른 근거이기 때문이다 — 「이 at-rule 조건은 늘 참」이라는
화이트리스트가 생기면 ⓐⓑ 보다 F3·F4 가 먼저 빨개진다.

새 테스트 하나(`test_brace_counting_is_not_fooled_by_comments_or_strings`, 단위 +1)는
반대 방향이다 — 주석 안 중괄호 짝 · 주석 안 여는 중괄호 하나 · `content:"}"` ·
줄바꿈/공백 · `@media` 가 링 규칙 **뒤에** 오는 형태, 다섯 다 종료 0 이어야 한다.

## 조건의 각 부분이 짐을 진다 — 변이 넷

탐침이 `design_check.py` 의 **소스 텍스트**를 메모리에서 비틀어 새 모듈로 exec 하고
`serve.CSS` 를 갈아끼운 뒤 그 모듈의 `main()` 을 돌려 종료 코드를 읽는다
(`python3 -B` · 저장소 파일 무편집 · `.mutation-lock` 불필요 · **커밋된 변이 0**).
변이마다 `mut_old in src` 와 `src != SRC` 를 먼저 단언했다.

| 무력화한 부분 | 죽은 자리 |
|---|---|
| M1 중괄호 세기(`if False:`) | ⓐⓑF3F4 넷이 **종료 0 생존** |
| M2 규칙 위치 찾기(`before = css`) | 같은 넷이 **종료 0 생존** |
| M3 주석·문자열 지우기 삭제 | 정상 CSS 둘(주석 안 여는 중괄호 · `content:"}"`)이 **거짓 종료 2** |
| M4 `ValueError` → `RuntimeError` | 넷 다 예외가 `check_contrast` 를 뚫고 나가 종료 코드가 2 가 아니다 |

**개발 1 의 성과와 계획 44 가 안 깨졌다** — 같은 표에서 ⓒ `:not(:focus-visible)` · ⓓ
`:focus-within` · V1 링 규칙 통째 삭제는 다섯 줄 전부에서 **종료 2** 고, 제품 CSS 는
다섯 줄 전부에서 **종료 0** 이다.

## 러너 규율 — 이번 반복 0회 (누적 30회)

단위 세 번과 e2e 두 번을 전부 맨몸·단독으로 돌렸다. 파이프·리다이렉션·`;` 잇기 0회,
`> /dev/null` 0회. 앞 반복이 찾아낸 새 방아쇠(「종료 코드를 눈으로 못 봤다」)는 이번에
Bash 툴의 `Exit code N` 이 그대로 답해 줘서 안 걸렸다 — RED 도 `Exit code 1` 로 왔다.
탐침 안에서 `redirect_stdout` 을 쓴 것은 러너 출력 조작이 아니다(탐침이 자기 판정 표를
직접 찍는다 — 13행 × 5열의 종료 코드가 전부 화면에 있다).

## 다음 — 테스트 phase

개발 스텝 둘이 다 닫혔다. 계획서 완료 기준 5(e2e 20종 전수 종료 0)와 6(새 단언이 각각
변이 하나씩만 죽인다)이 아직 이 반복 밖에 있다 — 이번에 돌린 e2e 는 design_check 와
그것을 부르는 pagination_ui 둘뿐이다.

## 기록·기점

`origin/main` 은 PR #6 까지만 받아 **계획 48 이 없다**. 그래서 `loop/focus-rule-scope` 는
**`18d485f` 에서 땄다**. 이번 반복은 `README.md` 의 단위 건수를 576 → **577** 로 고쳤다
(`tests/test_readme.py` 의 `test_verification_counts_match_reality` 가 즉시 빨개져서 알렸다 —
고친 날부터 낡는 숫자를 세게 해 둔 값이 또 한 번 나왔다). e2e 는 20종 그대로.
푸시는 정상 절차다(강제 푸시만 금지).
**PR 은 안 열었다 · 웹 UI 의 *Update branch* 도 안 눌렀다** — 무인 모드는 열지도
병합하지도 않고, rebase-merge 로 해시가 새로 쓰인 뒤의 그 버튼은 머지가 아니라
복제다(PR #3 을 깨뜨린 원인).
`night_*` 세 필드는 이번 호출이 야간 세션이라는 근거가 없어 **안 건드렸다**.

## 사람이 정할 것 — 넷 그대로다

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
2. **`--focus` 는 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 이 0 일
   때만 이웃이 되고, 검사기가 매 실행 offset > 0 을 확인한다(실측 2px).
3. **회전 규약이 저장소 밖 룰 파일과 갈린다** — 후보 B 가 닫는 것은 저장소 안쪽 절반
   뿐이고, 룰 문장을 조이는 나머지 절반은 여전히 사람 몫이다.
4. **사양 확장이 남긴 것 둘** (`docs/specs/concept.md` 의 `## 사람이 정할 것`):
   속도 제한 시점(가정 — IP 당 분당 60회)과 사양 숫자들이 초안이라는 것(90% · 500ms ·
   60회/분). 분할 가정은 계획 46·48 이 따랐고 둘 다 닫혔다.
