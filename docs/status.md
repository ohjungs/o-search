---
signal: GREEN
phase: 설계
step: 0
attempt: 0
iteration: 303
updated: 2026-09-04
ctx: 45
night_iterations: 130
night_red: 2
night_retries: 0
plan: focus-ring-combinator
---

# 현재 상태

**계획 52 `focus-ring-combinator` 착수.** 계획서 `docs/plan_focus-ring-combinator.md` ·
`index.md` 52번 줄 신설(0/1) · 다음은 **설계**. 계획 51 `hidden-passage` 는 DONE 그대로다.

## 무엇을 열었나

`e2e/design_check.py` 의 `focus_rule()` 조건 5 는 셀렉터를 한 덩어리로 봐서
**링이 포커스받은 요소가 아니라 옆 상자에 그려져도 초록**이다. 제품 `src/` 0줄 계획이고
고치는 것은 **재는 자**다 — 제품 CSS 에 결합자 뒤 링은 0곳이라 오늘의 3.56:1 은 참이다.

## 탐색은 6순위에서 멈췄다 — 1~5순위 실측 0건

- 1 실패 테스트 **0**(맨몸 `Ran 593 tests · OK` 13.540초) · 2 린터·타입체커 **설정 0개** ·
  3 코드 `TODO`/`FIXME`/`HACK` **0**(유일한 hit 는 `tests/test_indexer.py:758` 의 fixture
  HTML 주석 문자열) · 4 `docs/candidates.md`·`scripts/` **없음** · 5 `digest ## 보류` **빈 절**.
- 6순위 후보를 **전수로 대조**했다. 나머지는 전부 여는 조건 미도래거나 이미 닫혔다 —
  특히 **[8] 「토크나이저가 못 잡는 세 가지」는 취소선만 안 그어진 완료 항목**이다
  (계획 11 `tokenizer` 가 5/40 중 넷을 닫았다). 다시 열면 중복 작업이라 버렸다.

## 계획 phase 가 오늘 직접 잰 셋

1. **거짓 초록 4/4 재현** — `a:focus-visible` 뒤 결합자 ` `·`>`·`+`·`~` 넷 다 통과.
2. **후보에 없던 다섯째 갈래** — `a:focus-visible,.x` 도 통과한다(조건 5 가 쉼표 목록을
   조각으로 안 가른다). `.x` 는 링이 **항상** 그려지는 상자다.
3. **물려받은 처방이 절반이었다** — 후보가 적어 둔 `re.split(r"[ >+~]", part)[-1]` 은
   `a:focus-visible:not(.x + .y)` 를 **거절**한다(오탐). 그대로 쓰면 계획 44·49 가 지킨
   「오탐 0」이 깨진다. 「기록된 처방은 실행 전에 다시 재라」가 41·44 에 이어 세 번째.

## 설계로 넘긴다 — 트리거 하나

「대안이 2개 이상 갈림」. A 순진한 split · B `INDIRECT_RE` 선지우기 · C 괄호 깊이 세기 —
셋 다 결합자 4종은 닫는데 **오탐/미탐 집합이 다르다.** 설계는 셋을 다 짜서 같은 표에
먹이고 **갈리는 행**으로 고른다(계획 49 교훈: 말로 고르면 갈림이 계획서 자리에 없다).

## 원격을 다시 읽은 값이다

- 브랜치 **`loop/focus-ring-combinator`**(기점 `20ee8d5` — `loop/hidden-passage` 의
  HEAD 이고 `ls-remote` 가 `20ee8d5dd307…` 로 같았다). 계획 커밋 뒤 푸시하고
  **원격을 다시 읽었다**: `HEAD` **`23fdb82`** = `ls-remote` **`23fdb82728c1…`**.
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
