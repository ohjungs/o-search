---
signal: GREEN
phase: 개발
step: 2/2
attempt: 0
iteration: 517
updated: 2026-09-09
ctx: 62
night_iterations: 3
night_red: 0
night_retries: 0
plan: live-plan-gap
---

## 계획 90 `live-plan-gap` — 버려진 계획을 아무도 안 물었다

`docs/plan_live-plan-gap.md`. 브랜치 `loop/live-plan-gap`.

**이 문서 자신이 근거였다.** 오늘 밤이 읽은 `status.md` 는 frontmatter 가
`plan: backoff-recovery · step 2/2` 인데 본문은 **계획 85 `iter-third-witness`** 를
설명하며 넉 계획 전에 끝난 스텝을 시켰다. 실측:

```
index.md   | plan_iter-third-witness | 진행 | … | 2/3 |   ← 계획 행 68개 중 유일한 「진행」
본문 마지막 변경  f2e8e37 (계획 85)  · 86·87·88·89 는 frontmatter 세 줄만 고쳤다
전수 737 OK rc 0                                          ← 아무도 안 문다
```

`iter-third-witness` 는 개발 2/3 에서 **버려졌다.** 그 뒤 `f2e8e37` 이 **같은 번호 85
를 다시 써서** 다른 계획을 마감했고 네 계획이 그 위를 지났다. 문서 가드 여덟 벌은
전부 `status.plan` 이 가리키는 행만 봐서 **뒤에 남겨진 행은 시야 밖**이다.

## 이번 반복 — 개발 2/2 · 변이 3종이 각각 죽는다

```
① `진행` 필터 삭제 (모든 행을 본다)         → 5건 죽음
② 대조를 자기비교로 (`slug != slug`)         → 3건 죽음   ← 조용한 초록 방향
③ 판정 통째 삭제 (`return None`)             → 4건 죽음
```

**변이가 실제로 심어졌는지를 먼저 단언했다**(digest `[8]` — BSD sed 가 조용히 무시한
적이 있다). 앵커가 유일한지도 단언하는데 **③ 이 거기서 걸렸다** — `p =
PLAN_SLUG.search(status_text)` 가 `step_gap` 과 겹쳐 두 자리라 docstring 끝줄까지
붙여 좁혔다. 자리를 안 세었으면 `step_gap` 을 변이시키고 `live_gap` 을 쟀다고 적을
뻔했다. `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 매 판 새로
줬고(`project.md`) 매 판 뒤 원복을 파일 비교로 확인했다.

`digest ## 반복 실패` 에 등재했다 — 일반화는 **「지금 도는 것」만 재는 자는 «도는 것이
바뀌는 순간» 뒤에 남은 것을 구조적으로 못 본다**이고, 문서 가드 여덟 벌이 전부 그
모양이었다.

## 이번 반복이 앞 반복의 사고를 되돌렸다 — 본문 세 절이 커밋에서 사라져 있었다

반복 516 이 이 파일을 `t.index("## 다음 스텝")` 으로 잘라 편집했는데, **그 머리 문구가
바로 위 산문에 인용돼 있어**(「…`## 다음 스텝 — 개발 3/3`」을 시켰다) 슬라이스가
거기서 시작해 `## 이번 반복`·`## 계획 89`·진짜 `## 다음 스텝` **세 절을 통째로
삼켰다.** 전수 745 OK 였다 — 문서 가드는 이 파일의 절 구성을 안 본다. 아래 두 절이
그때 잃은 것이고, **머리 문구를 산문에 인용하는 습관은 이 저장소에 있다**(계획 76 의
`HISTORY_ENTRY_HEAD` 앵커가 같은 자리에서 나왔다). 이 파일은 짧으니 앞으로 통째로
다시 쓴다.

## 앞 반복 — 개발 1/2 · 자를 세우고 이빨을 실물 다섯 트리로 쟀다

`live_gap` + `LivePlanSyncTest`(실물) + `LiveGapTest`(갈래 7). `PLAN_ROW` 에 슬러그
자리만 열어 재사용했다(`LIVE_ROW`) — 표의 열 모양이 바뀌는 날 둘이 함께 움직인다.

**이빨의 증거는 합성 픽스처가 아니라 정정 전 실물 다섯 트리다**: `f2e8e37`(버려진 그
커밋)·`ba83bc2`(86)·`6ea7f10`(87)·`78f323c`(88)·`1b79a74`(89) 가 전부
`iter-third-witness` 를 이름으로 신고하고 지금 트리는 `None` 이다.
**거짓 RED 도 과거 전체로 쟀다** — 슬러그 관례가 선 뒤(`3f7d1f8`, 계획 60) 137커밋 중
빨강 5건이고 5건 전부 그 결함이라 오탐 0이다. 그 앞이 빨간 것은 `plan:` 이 슬러그가
아니라 갈래 이름(`docs`)이던 시절이라서고, `step_gap` 도 같은 트리에서 같은 이유로
빨갛다. `README.md` 의 단위 건수 737 → **745** 도 같이 고쳤다(`ReadmeCommandsTest` 강제).

## 앞 반복 — 계획 phase · 계획서와 실물 정정

- 계획서 작성. 스텝 2개. 설계 없음(트리거 대조는 6절).
- **실물을 손으로 맞췄다** — `index.md` 의 `iter-third-witness` 행을 `진행` →
  **`보류(미완)`** 로. 완료라 안 적는다(스텝 3/3 은 실제로 안 했다). 재개 근거는
  `digest ## 보류`. 본문도 다시 썼다 — 계획 85 이후 넉 계획이 frontmatter 만 고쳤다.
- 가드 둘이 그 커밋을 물었다 — `StepSyncTest`(새 계획 index 등재 누락) ·
  `DocCitationTest`(기록이 계획 행 개수를 「행」으로 적은 것을 append 문서의 줄번호
  인용으로 읽었다 — 개수로 바꿔 적었다).

## 계획 89 `backoff-recovery` 가 한 것 (병합 `be0ddd5`)

429 벌점을 `_penalty` 로 분리해 백오프가 되돌아오게 했다. `_delays` 는 robots 값이라
단조 증가, `_penalty` 는 우리가 매긴 값이라 오르내리고 `interval()` 이 `max` 로 읽어
**회복이 예의를 깎을 수 없다.** 실물이 누출을 잡았다 — `set_delay` 가 `interval()`
을 읽어 벌점이 robots 칸에 새어 굳었고, **단위 5건은 전부 초록**이었다(둘이 만나는
자리를 아무도 안 봤다). 고친 뒤 2.0→4.0→8.0 → 4.0→2.0→1.0. 전수 737 OK.

## 다음 반복 — 테스트 phase

스텝 둘이 끝났다. `rules/test.md` 의 갭 여섯을 `live_gap` 과 새 테스트 아홉에 대고
읽는다. 지금 보이는 자리: **열이 줄어 `LIVE_ROW` 가 행을 통째로 건너뛰는 쪽**을
`live_gap` 은 안 물고 `verdict_gap` 에 기대는데, **그 기댐을 재는 자가 0개다.**

## 아침 할 일 — 어제와 같은 하나

**패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch` (382줄 ·
구현 + 단위 + e2e · `git apply --check` 통과). 밤이 안 댄 이유는 「보안 — 항상 보류」다.
적용하면 `urls.normalize` 가 netloc 에 `@` 를 든 URL 에 `None` 을 준다(018 의 「보존」을
뒤집는다). 되돌리려면 `normalize` 안의 조건 한 줄을 지운다.

## 한도

`digest.md` **218줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선).
`history_current.md` 209줄(상한 300).
