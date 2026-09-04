---
signal: GREEN
phase: 계획
step: 0/0
attempt: 0
iteration: 308
updated: 2026-09-04
ctx: 46
night_iterations: 133
night_red: 2
night_retries: 0
plan: null # 계획 52 focus-ring-combinator DONE
---

# 현재 상태

**계획 52 `focus-ring-combinator` DONE.** e2e 1/1 이 완료 기준 **1~8 전부 통과**로 닫았다.
계획서·설계서는 `plan_history_038.md`·`design_history_038.md` 로 아카이브했고
결과는 `docs/e2e/focus-ring-combinator/result.md` 에 있다. **새 e2e 파일 0 · 제품 `src/` 0줄.**

## e2e 가 더한 것 — 제품 파일을 실제로 망가뜨렸다

개발·테스트는 `check_contrast()` 를 프로세스 **안에서** 불러 비틀린 CSS 문자열을 먹였다.
거짓 초록은 «단언이 아니라 **종료 코드**가 초록» 이던 고장이라 그 자리에서 재야 한다.
`src/websearch/serve.py` 의 링 셀렉터 꼬리만 바꿔 검사기를 프로세스로 돌렸다.

- **망가뜨렸을 때**: 결합자 4종(` `·`>`·`+`·`~`) + 쉼표 목록 → **5/5 rc 2.**
  종료 코드보다 강한 증거는 `[3]` 축이 **16행 → 14행**으로 줄고
  `--focus on --bg-page 3.56:1` 두 줄이 **사라지는 것**이다 — 이 계획이 겨눈
  「아무도 못 보는 링 위에서 3.56:1 을 찍는 것」이 실제로 안 찍힌다.
- **정상일 때**: rc **0** · `[3]` **16행** · 라이트 `--focus` **3.56:1** · `4축 전부 통과.`
- **오탐 쪽도 제품 파일에서 쟀다**: `a:focus-visible:not(.x + .y)` · `a:focus-visible[class~=btn]`
  둘 다 **rc 0 · 16행 · 3.56:1**. 순진한 `re.split` 이었다면 e2e 전수 RED 였다.

**값이 하나 더 나왔다 — `_top_level` 의 두 호출처를 서로 다른 행이 붙든다.**
변이 ④ 를 **안쪽만** 되돌리면 `failures=4` 고, 남는 둘(`:is(.x, .y):focus-visible` ·
`:is(.x, .y > .z):focus-visible`)은 **바깥 쉼표 가르기**가 붙든다 — 둘 다 되돌려야
설계서가 셈한 **6**(테스트 phase 기록과 일치)이다. 한쪽만 무르면 절반이 조용히 열린다.

## 실측

- 단위 **`Ran 593 tests in 13.470s` OK**(맨몸·단독) · 원복 뒤 재실행 13.500초 OK · **593 무변**
- **e2e 21종 전수 rc 0** · 새 e2e 파일 0 · `README.md` 의 `단위 593건`·`e2e 21종` 무변
- 품질 4축 무변: ko **20/20** · en **19/20** · 문단 정확도 **100.0%** p95 **1.47ms** ·
  `perf_search` p95 **8.85ms** · 크롤 **10.22/10.24** 문서집합 sha1 무변
- 범위: `git diff --stat 20ee8d5..HEAD` 에 `src/` **0줄** · `data/crawl.db` sha256 무변 ·
  `docs/specs/` 무변
- `.mutation-lock` **두 번** 사용 · 원복은 전부 스크래치패드 사본(`git checkout` **0회**) ·
  되붙인 뒤 `git status --short`·`git diff --stat` **빈 출력** 확인
- 러너 규율 **위반 0회** — 파이프·리다이렉션·명령 잇기 0(`git push`·`ls-remote` 포함)

## 다음 행동

계획 탐색 — `rules/discover.md` 1~7순위. 오늘 기준 1~5순위는 계획 52 착수 때
실측 0건이었고, 6순위 후보는 `digest ## 다음 계획 후보` 에 있다(대부분 여는 조건 미도래).

## 설계

해당 없음 (활성 계획 없음). 계획 52 의 설계서는 `design_history_038.md`.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` 가 그 뒤에 쌓여 있다. 병합은 사용자가 처리한다 —
   이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
