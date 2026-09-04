---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 306
updated: 2026-09-04
ctx: 55
night_iterations: 131
night_red: 2
night_retries: 0
plan: focus-ring-combinator
---

# 현재 상태

**계획 52 테스트 1/1 완료.** 갭 탐색이 **8점 하나**를 찾아 닫았다 —
`_top_level` 의 가드절 `max(0, depth-1)` 을 밟는 입력이 0개였다(그 가드를 지운
변이가 **593건을 전부 통과**했다). 표에 행 하나 추가 · 제품 `src/` **0줄** ·
파일 **1개** · 다음은 **리뷰 1/1**. 계획 51 `hidden-passage` 는 DONE 그대로다.

## 갭 탐색 — 6개 카테고리 중 걸린 것은 ①·⑥ 하나씩이고 같은 자리다

- **[8] 가드절이 안 밟혔다** (①부정 경로 + ⑥변경된 함수의 새 분기). `_top_level` 은
  안 열린 `)` 에서 깊이가 음수로 내려가지 않게 `max(0, …)` 로 막는데, 그 가드를
  `depth - 1` 로 지워도 **`Ran 593 tests · OK`** 였다 — 개발이 심은 변이 넷이 전부
  다른 줄을 겨눠 이 줄만 아무도 안 붙들고 있었다. 살아 있으면 깊이가 음수가 되어
  **그 뒤의 결합자·쉼표가 전부 «괄호 안»** 으로 보이고, 셀렉터가 한 덩어리가 되어
  이 계획이 닫으러 온 거짓 초록이 그대로 돌아온다.
- **행 하나로 닫았다** — 미탐 표에 `("안 열린 `)` 로 깊이가 음수", ":focus-visible",
  ":focus-visible) .hint", "포커스용이 아니다")`. 새 테스트 메서드 0 · 단위 건수
  **593 무변**(`subTest` 행이라 `README.md` 의 `단위 593건` 단언 그대로 · 문서 0줄).
- **RED 를 먼저 눈으로 봤다** — 가드를 지운 채 행을 넣고 `FAILED (failures=1)`,
  실패 출력이 링을 `.hint` 에 그려 놓고 `--focus 3.56:1` 을 그대로 찍는다. 가드를
  되돌리자 `Ran 593 tests · OK`.
- **나머지 다섯 카테고리는 0건이다** — ②경계값: 꼬리 쉼표·빈 조각은 실측 **거절**
  (측정 불능이 맞다) · ③격리: `_top_level` 은 순수 함수(전역·시계·네트워크 0) ·
  ④불안정: `sleep`·랜덤·순서 단언 0 · ⑤보안: 신뢰 경계 아님(제 저장소의 CSS 를
  읽는 검사기) · ⑦동시 실행: 공유 상태 0.
- **8점 미만 둘은 `digest` 에 등재했다** — [5] 안 **닫힌** `(` 는 아직 거짓 초록이다
  (실측 `a:focus-visible:not(.x .y` 통과 · 깨진 CSS 라 제품에 실재 불가 · 막으려면
  문법을 읽기 시작한다) · [4] 문자열 안 홀괄호가 안 무는 것은 `COMMENT_OR_STRING_RE`
  를 **먼저** 돌리는 순서에 기댄 성질인데 그 순서를 붙드는 단언이 0개다.

## 변이 다섯, 전부 죽는다 (`.mutation-lock` 아래 제자리 · 전부 원복 · `python3 -B`)

| 변이 | 되돌리는 것 | 판정 |
|---|---|---|
| ① 마지막 compound → 조각 전체 | `_top_level(part.strip(), …)[-1]` → `part.strip()` | **죽는다** `FAILED (failures=7)` — 개발 때 6, 새 행이 일곱째다 |
| ② 쉼표 가르기 제거 | `_top_level(selector, ",")` → `[selector]` | **죽는다** `FAILED (failures=1)` — `a:focus-visible,.x` |
| ③ 결합자 집합에서 `~` 를 뺀다 | `" \t\n>+~"` → `" \t\n>+"` | **죽는다** `FAILED (failures=1)` — `a:focus-visible~.hint` |
| ④ **깊이 세기 제거**(= 순진한 처방) | `_top_level` 두 호출 → `str.split`/`re.split` | **죽는다** `FAILED (failures=6)` — 설계서 ★ 여섯 행이 **전부 오탐**으로 뒤집힌다 |
| ⑤ **가드절 제거**(테스트 phase 가 새로 심었다) | `max(0, depth - 1)` → `depth - 1` | **심은 날엔 살아남았다**(`Ran 593 · OK`) → 새 행을 붙이고 **죽는다** `FAILED (failures=1)` |

⑤ 가 이번 phase 가 산 값이다 — 넷은 개발이 이미 죽였고 다섯째만 초록 아래 살아
있었다. 심기 전 `count(원문) == 1` 로 원문 존재를 먼저 단언했다(`digest [8]`).
원복은 `git checkout` 이 아니라 **스크래치패드 사본에서 `cp`**(개발 phase 의 교훈) ·
되돌린 뒤 `git diff -- e2e/design_check.py` **0줄** · `.mutation-lock` 삭제 확인.

## 재측 — 기준선 전부 무변

- 단위 **`Ran 593 tests · OK`**(13.488초, 맨몸·단독) — 건수 무변.
- `PYTHONPATH=src python3 e2e/design_check.py` **rc 0** · `[3]` 축 **16행** ·
  라이트 `--focus on --bg-page` **3.56:1** — 기준선 그대로다.
- `design_check.py` 를 서브프로세스로 부르는 **`e2e/pagination_ui_e2e.py` 도 rc 0**.
  e2e **전수 21종은 e2e phase 의 일**이다.
- **단언을 낮춘 곳 0** — 기존 표의 판정·문구는 한 글자도 안 고쳤고, 이번 변경은
  미탐 표에 **행 하나를 더한 것**뿐이다(`git diff --stat` `tests/…` +7줄, 그중 5줄이 주석).

## 러너 규율 — 이번 phase 위반 0회

- 러너에 파이프·리다이렉션 **0회**(변이 다섯 배터리 전부 맨몸·단독). 앞 두 phase 의
  누적 31회는 그대로고 회전은 없다. 방아쇠(«출력이 길어 줄이고 싶다»)는 이번에도
  왔지만 — 변이 ①·④ 의 실패 리포트가 화면을 채운다 — 자르지 않고 원문을 읽었다.

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
