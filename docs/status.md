---
signal: GREEN
phase: 계획
step: 0/2
attempt: 0
iteration: 515
updated: 2026-09-09
ctx: 62
night_iterations: 1
night_red: 0
night_retries: 0
plan: live-plan-gap
---

## 계획 90 `live-plan-gap` — 버려진 계획을 아무도 안 물었다

`docs/plan_live-plan-gap.md`. 브랜치 `loop/live-plan-gap`.

**이 문서 자신이 근거였다.** 오늘 밤이 읽은 `status.md` 는 frontmatter 가
`plan: backoff-recovery · step 2/2` 인데 본문은 **계획 85 `iter-third-witness`** 를
설명하며 「## 다음 스텝 — 개발 3/3」을 시켰다. 실측:

```
index.md   | plan_iter-third-witness | 진행 | … | 2/3 |   ← 68행 중 유일한 「진행」
본문 마지막 변경  f2e8e37 (계획 85)  · 86·87·88·89 는 frontmatter 세 줄만 고쳤다
전수 737 OK rc 0                                          ← 아무도 안 문다
```

`iter-third-witness` 는 개발 2/3 에서 **버려졌다.** 그 뒤 `f2e8e37` 이 **같은 번호 85
를 다시 써서** 다른 계획을 마감했고 네 계획이 그 위를 지났다. 문서 가드 여덟 벌은
전부 `status.plan` 이 가리키는 행만 봐서 **뒤에 남겨진 행은 시야 밖**이다.

## 이번 반복 — 계획 phase · 계획서와 실물 정정

- 계획서 작성. 스텝 2개(자 세우기 → 변이·등재). 설계 없음(트리거 대조는 6절).
- **실물을 손으로 맞췄다** — `index.md` 의 그 행을 `진행` → **`보류(미완)`** 로 고치고
  왜 그런지 비고에 적었다. **완료라고 적지 않는다** — 스텝 3/3 은 실제로 안 했다.
  재개 근거는 `digest ## 보류` 에 올렸다(남은 일은 변이 3종과 39행 등재뿐이고, 자와
  기록 정정은 `aca4be4`·`937dd21` 로 이미 살아 있다).
- **이 본문을 다시 썼다.** 계획 85 이후 넉 계획 동안 frontmatter 만 갱신됐다.
- 자가 서는 순간 실물이 빨간 것과 **자에 이빨이 있는 것은 다른 명제**라, 후자는
  스텝 1 이 정정 **전** 트리(`git show`)를 먹여 증명한다 — 계획 85 가 반복 번호에
  쓴 순서 그대로다.

## 계획 89 `backoff-recovery` 가 한 것 (병합 `be0ddd5`)

429 벌점을 `_penalty` 로 분리해 백오프가 되돌아오게 했다. `_delays` 는 robots 값이라
단조 증가, `_penalty` 는 우리가 매긴 값이라 오르내리고 `interval()` 이 `max` 로 읽어
**회복이 예의를 깎을 수 없다.** 실물이 누출을 잡았다 — `set_delay` 가 `interval()`
을 읽어 벌점이 robots 칸에 새어 굳었고, **단위 5건은 전부 초록**이었다(둘이 만나는
자리를 아무도 안 봤다). 고친 뒤 2.0→4.0→8.0 → 4.0→2.0→1.0. 전수 737 OK.

## 다음 스텝 — 개발 1/2

`live_gap(status_text, index_text)` 를 `tests/test_docs.py` 에 세운다. `index.md` 의
상태 칸이 `진행` 인 계획 행 슬러그를 모아 `status.plan` 과 다른 것이 있으면 그 이름을
붙여 신고한다. `진행` 0개는 조용하다. 실물은 `LivePlanSyncTest`, 갈래는 `LiveGapTest`
가 부른다(`iter_gap`·`step_gap` 이 몸통을 함수로 뺀 이유와 같다).
**이빨 측정**: `git show <이 커밋>:docs/{status,index}.md` 를 먹여 `iter-third-witness`
를 이름으로 신고하는 것을 본다.

## 아침 할 일 — 어제와 같은 하나

**패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch` (382줄 ·
구현 + 단위 + e2e · `git apply --check` 통과). 밤이 안 댄 이유는 「보안 — 항상 보류」다.
적용하면 `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을 준다(018 의 「보존」을
뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.

## 한도

`digest.md` **216줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선).
`history_current.md` 190줄(상한 300).
