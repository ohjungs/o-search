---
signal: GREEN
phase: 개발
step: 2/3
attempt: 0
iteration: 527
updated: 2026-09-10
ctx: 65
night_iterations: 1
night_red: 0
night_retries: 0
plan: iter-third-witness
---

## 계획 85 `iter-third-witness` — 버려진 스텝 3/3 을 재개한다

계획서 `docs/plan_iter-third-witness.md`(살아 있다). 브랜치 `loop/iter-third-witness`
는 다섯 계획 뒤처져 있어 **`main` 에서 다시 땄다**(옛 위치는 `main` 의 조상이라 잃은
것이 없다 — `git merge-base --is-ancestor` 로 확인했다).

**남은 것은 스텝 3 하나다.** 스텝 1(`iter_gap` 셋째 증인 + `IterGapTest`)과 스텝
2(기록 정정)는 `aca4be4`·`937dd21` 로 들어가 **지금 살아 있다** — 실측으로 확인했다:
`iter_gap(status, metrics, history)` 가 셋째 인자를 받고 `HIST_ITER` 의 **최댓값**을
문다(`tests/test_docs.py:147`), `IterGapTest` 갈래 6개가 그것을 밟는다.

안 한 것은 **그 자에 이빨이 있는지 재는 일과 등재**뿐이다.

## 이번 반복 — 계획 탐색 · 1~4순위가 비었고 5순위에 미완이 있었다

`discover.md` 1절 순서대로 실측했다:

```
1 실패 테스트   PYTHONPATH=src python3 -m unittest discover -b tests → 749 OK rc 0
2 린트·타입     없음 (project.md — stdlib 만 쓰는 소규모)
3 src/ TODO     grep -rn 'TODO|FIXME|HACK' src/ → 0건
4 candidates.md 파일 없음
5 digest 보류   2건 → 하나는 보안 패치(밤 금지) · 하나가 이 계획이다
```

**보류 2건이 같은 무게가 아니다.** `plan_userinfo-leak` 은 사람의 승인을 기다리는
보안 건이라 밤이 못 댄다(`SKILL.md` 「보안 — 항상 보류」). `plan_iter-third-witness`
는 **승인 대기가 아니라 그냥 안 끝난 것**이다 — 계획 90 이 발견해 `index.md` 를
`진행`→`보류(미완)` 으로 정정했을 뿐, 사람이 정할 것은 처음부터 없었다. 남은 일은
변이 3종과 digest 한 줄이라 `src/` 를 안 건드리고 야간 금지 목록에도 안 걸린다.

**앞 반복(521)이 YELLOW 였던 이유는 오늘 그대로다** — `perf_crawl` 기준선 건은 여전히
사람이 정할 것이고, 나는 그 자리로 돌아가지 않고 **비어 있던 5순위를 다시 읽어** 갔다.

## 실측으로 하나 더 발견 — `status.md` 본문이 다섯 반복 뒤처져 있었다

이 파일을 열었을 때 frontmatter 는 `iteration: 526 · plan: rejection-visible` 인데
**본문은 계획 90 `live-plan-gap` 과 반복 515~521 을 설명**하고 있었다. 실측:

```
b671982 (계획 90 rejection-visible)  docs/status.md | 6 +++---   ← frontmatter 3줄만
c70bf5b (짧은 경로 mock-blindspot)   같은 모양
본문 마지막 실질 변경  ed56005 (계획 탐색 521)
전수 749 OK rc 0                                                 ← 아무도 안 문다
```

**계획 90 이 지은 `live_gap` 은 이것을 구조적으로 못 잡는다** — 그 자는 표의 칸을
읽고 **산문을 안 읽기로 한 결정**이 docstring 에 적혀 있다(거짓 RED 의 원천이라서다).
옳은 결정이지만, 그래서 「frontmatter 는 갔는데 본문이 안 갔다」는 축은 여덟 벌 중
아무도 안 문다. **자를 세우자는 말이 아니다** — 오늘은 이 파일을 통째로 다시 써서
닫았고, 재는 자를 세울지는 `digest.md` 후보로 등재해 사람에게 넘긴다(산문 매칭이라
`verdict_gap`·`live_gap` 이 두 번 피한 방향이다).

## 다음 스텝 — 개발 3/3

변이 3종을 심어 `iter_gap` 이 각각 무는지 재고, digest `## 반복 실패` 39행에
「셋째 증인은 **최댓값**이지 마지막 항목이 아니다」를 등재한다.

```
① 셋째 증인 통째 삭제 (history 대조 제거)
② max(...) → 마지막 항목 (heads[-1])
③ HIST_ITER 의 범위 `?:` 제거
```

변이는 `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 매 판 새로
주고(`project.md`), 심은 뒤 **실제로 심겼는지 먼저 단언**하며(digest `[8]` — BSD sed
가 조용히 무시한 적이 있다), 매 판 뒤 원복을 파일 비교로 확인한다.

## 한도

**statusLine 이 꺼져 있다** — `.context-state.json` 의 `updated_unix` 가 시작 시점에
이미 618초 지났다(상한 600). 컨텍스트 게이지를 못 믿으니 **반복 상한에만 의존한다**
(`SKILL.md` 3절). 마지막으로 읽힌 값은 ctx 65 · 5h 9 · 7d 61 이다.

`digest.md` **206줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선,
`digest-cap-verdict` 가 「못을 세우지 않는다」로 닫았다). `history_current.md` 193줄.

## 아침 할 일 — 어제 셋 그대로 + 하나

**1~3 은 반복 521 이 남긴 것과 같다**(`perf_crawl` 기준선 · `deadline_e2e` 1초 하한 ·
`userinfo-leak` 패치 적용 판단). 밤이 그 자리로 돌아가지 않았을 뿐 아무것도 안 정해졌다.

**4. `status.md` 본문 드리프트를 잴 것인가** — 위 절의 실측이 근거다. 자를 세우면
산문을 읽어야 하고, 그 방향은 이 저장소가 두 번 일부러 피했다. digest 후보에 올렸다.
