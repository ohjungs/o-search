---
signal: GREEN
phase: 개발
step: 1/2
attempt: 0
iteration: 516
updated: 2026-09-09
ctx: 62
night_iterations: 2
night_red: 0
night_retries: 0
plan: live-plan-gap
---

## 계획 90 `live-plan-gap` — 버려진 계획을 아무도 안 물었다

`docs/plan_live-plan-gap.md`. 브랜치 `loop/live-plan-gap`.

**이 문서 자신이 근거였다.** 오늘 밤이 읽은 `status.md` 는 frontmatter 가
`plan: backoff-recovery · step 2/2` 인데 본문은 **계획 85 `iter-third-witness`** 를
설명하며 「## 다음 스텝 — 개발 2/2

변이 3종을 실제로 심어 각각 잡히는지 잰다 — ① `진행` 필터 삭제(모든 행을 본다)
② `status.plan` 비교 삭제 ③ 판정 통째 삭제(`return None`).
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다
(`project.md`). **변이가 실제로 심어졌는지 먼저 단언한다** — digest `[8]`, BSD sed 가
조용히 무시한 적이 있다. 그 뒤 `digest ## 반복 실패` 에 등재한다.

## 아침 할 일 — 어제와 같은 하나

**패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch` (382줄 ·
구현 + 단위 + e2e · `git apply --check` 통과). 밤이 안 댄 이유는 「보안 — 항상 보류」다.
적용하면 `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을 준다(018 의 「보존」을
뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.

## 한도

`digest.md` **216줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선).
`history_current.md` 190줄(상한 300).
