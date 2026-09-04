---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 305
updated: 2026-09-04
ctx: 62
night_iterations: 131
night_red: 2
night_retries: 0
plan: focus-ring-combinator
---

# 현재 상태

**계획 52 개발 1/1 완료.** `e2e/design_check.py` 조건 5 가 **쉼표 조각마다 마지막
compound** 를 읽는다 · 제품 `src/` **0줄** · 파일 **2개** · 다음은 **테스트 1/1**.
계획 51 `hidden-passage` 는 DONE 그대로다.

## 개발이 한 일 — 설계 계약 그대로, 한 글자도 안 늘렸다

- `_top_level(text, seps)` 헬퍼 하나(`INDIRECT_RE` 정의 아래)와 234행 `if` 를
  `for part in _top_level(selector, ",")` 루프로. 메시지 문자열 무변(변이 표 6행이
  그 문구를 붙든다) · `focus_rule` 시그니처와 rc 계약 무변 · 새 파일 0 · 의존성 0.
- **RED 를 먼저 눈으로 봤다**: 미탐 7행을 심고 `FAILED (failures=7)`.
  구현 뒤 같은 러너가 `Ran 8 tests · OK`. 새 오탐 8행은 심는 날부터 초록이었고
  (오늘의 조건 5 도 통과시키던 행이라) **변이 ④ 가 그 여섯을 죽여** 값을 증명한다.

## 변이 넷, 전부 죽는다 (`.mutation-lock` 아래 제자리 · 전부 원복 · `python3 -B`)

| 변이 | 되돌리는 것 | 판정 |
|---|---|---|
| ① 마지막 compound → 조각 전체 | `_top_level(part.strip(), …)[-1]` → `part.strip()` | **죽는다** `FAILED (failures=6)` — 결합자 4종 + 공백 낀 `>` + `:is(…)` 뒤 결합자 |
| ② 쉼표 가르기 제거 | `_top_level(selector, ",")` → `[selector]` | **죽는다** `FAILED (failures=1)` — `a:focus-visible,.x` |
| ③ 결합자 집합에서 `~` 를 뺀다 | `" \t\n>+~"` → `" \t\n>+"` | **죽는다** `FAILED (failures=1)` — `a:focus-visible~.hint` |
| ④ **깊이 세기 제거**(= 순진한 처방) | `_top_level` 본문 → `re.split` | **죽는다** `FAILED (failures=6)` — 설계서 ★ 여섯 행이 **전부 오탐**으로 뒤집힌다 |

넷째가 A·C 를 B 와 가르는 자리고, 그것이 죽는 것으로 «깊이를 센다» 가 장식이 아님이
증명된다. 심기 전 `count(원문) == 1` 로 원문 존재를 먼저 단언했다(`digest [8]`).

## 재측 — 설계서 표를 구현된 코드에 다시 먹였다

- **24행 · 틀린 행 0.** 설계서가 「25행」으로 셌지만 표에서 실제로 세어지는 입력은
  24개다(`(4행)`·`(3행)` 묶음을 풀어 세면 24) — **수치가 아니라 계수의 차이**라
  적어만 둔다. 통과/거절 집합은 설계서 B 열과 한 행도 안 갈렸다.
- 단위 **`Ran 593 tests · OK`**(13.386초, 맨몸·단독) — **건수 무변**이라 `README.md`
  의 `단위 593건`·`e2e 21종` 단언 그대로다(문서 0줄).
- `PYTHONPATH=src python3 e2e/design_check.py` **rc 0** · `[3]` 축 **16행** ·
  라이트 `--focus on --bg-page` **3.56:1** — 기준선 그대로다.
- `design_check.py` 를 서브프로세스로 부르는 **`e2e/pagination_ui_e2e.py` 도 rc 0**
  (검사기를 고쳤으므로 그 호출처를 함께 봤다). e2e **전수 21종은 e2e phase 의 일**이다.

## 러너 규율을 두 번 어겼다 — 적는다

- 변이 ② 판정에서 `2>/tmp/nul`, 그 뒤 한 번 더 `> /dev/null` 을 러너에 붙였다
  (**리다이렉션 2회**). 둘 다 **맨몸으로 즉시 재실행해** 판정은 원문에서 읽었고
  수치 조작은 0회지만, 규율은 「러너에 파이프·리다이렉션을 안 붙인다」라 0회가 아니다.
  방아쇠는 둘 다 «출력이 길어 줄이고 싶다» 였다 — `digest ## 반복 실패` 의 그 방아쇠다.
  ⑳ 에 계획 phase 의 1회(`| tail -4`)와 합쳐 **28 → 31회**로 적었다. 거기서 새로 보이는
  것 하나: **계획 50 의 `-b` 는 이 자리를 못 막는다** — `-b` 가 삼키는 것은 통과한
  테스트의 stdout 이라 변이 배터리의 긴 실패 리포트도, `unittest` 가 아닌 e2e
  스크립트의 출력도 그대로다.
- **`git checkout -- e2e/design_check.py` 로 변이를 되돌리다 미커밋 구현을 통째로
  날렸다**(재작성해 복구 · 잃은 시간만 손해 · 테스트는 무사). 커밋 전 단계의 원복은
  `git checkout` 이 아니라 **스크래치패드 사본**이어야 한다. 이후 셋은 사본으로 되돌렸다.

## 원격을 다시 읽은 값이다

- 브랜치 **`loop/focus-ring-combinator`**(기점 `20ee8d5`). 개발 커밋 뒤 푸시하고
  **원격을 다시 읽었다**: `HEAD` **`5f86d08e9a2f…`** = `ls-remote` **`5f86d08e9a2f…`**.
- 기점을 `main` 으로 안 잡았다 — `origin/main` 은 `687a159`(계획 47)이라
  `README.md` 의 `단위 593건`·`e2e 21종` 단언이 거기서는 RED 다.
- **PR #7**(`loop/merge-48-50` → `main`) **OPEN·미병합.** 병합은 사용자가 처리한다 —
  이 반복은 PR 을 열지도 닫지도, 그 브랜치를 건드리지도 않았다.
- `--no-verify`·`--force` 0회 · 훅 우회 0 · `data/crawl.db`·`docs/specs/` 무변경.

## 승인 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 누구도 그 화면을 못 그린다.
4. **회전 규약·러너 규율의 저장소 밖 절반**과 **사양이 남긴 둘**(`specs/concept.md` 의
   `## 사람이 정할 것`).
5. **PR #7 병합** · `loop/hidden-passage`·`loop/focus-ring-combinator` 의 PR 생성 여부.
