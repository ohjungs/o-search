---
signal: DONE
plan: null
phase: 계획
step: -
attempt: 0
iteration: 128
night_iterations: 11
night_red: 0
night_retries: 0
updated: 2026-08-29 13:55 (반복 128 · 020 e2e 4/4 · DONE)
ctx: 45% / 200k
stopped: null
rules: 1411a37
mode: night
---

# 현재 상태

**계획 020 `deadline` DONE.** 4스텝 전부 끝났고 아카이브했다.
브랜치 `loop/deadline` (기점 `aeb2eeb`). 아카이브: `plan_history_018` ·
`design_history_018` · `index.md` 20번 · e2e 증거 `docs/e2e/deadline/`.
단위 **393건 OK** · e2e **15종 전부 rc=0**.

## 020 이 남긴 것

크롤에 **총 크롤 시간 예산**이 생겼다. `crawl(..., deadline=D)` 와 CLI
`--deadline N`. 예산이 다하면 새 요청을 안 던지고 지금까지 저장한 것을 **정상
반환**한다. 기본값 `None` 은 무제한 — 예산을 안 주면 오늘과 안 다르다.
**예산은 간격을 깎지 않고 자른다** (e2e 시나리오 3, 간격 최소 1.00s).

**e2e 4/4 의 값**: 단위 393건이 전부 OK 인 채로 CLI 배선이 끊기는 변이(M6)를
e2e 만 잡는다 — `tests/test_crawl.py` 가 `crawl` 을 목으로 갈아끼우고 CLI 를
보기 때문이다. 이번 스텝에서 **같은 트리 실측으로 재확인**했다.

이전 세션이 `scenario_0_control` 과 `--control` 을 **정의만 하고 `main()` 에서
안 부른 채** 끊긴 것을 배선했다. 그 배선이 팝 게이트 변이(M-E)를 잡은 유일한
자리다. 잣대가 없으면 "덜 모았다" 가 아무것도 못 모으는 세계에서도 참이 된다.

## 승인 대기 (020 이 남긴 보류 2건)

- **`docs/patches/deadline-inflight-reap.patch`** (critical) — 예산 만료 `break` 가
  **떠 있는 요청의 결과를 버린다**. executor 는 나갈 때 어차피 기다리므로 시간은
  치르고 결과만 버리는 셈이고 다음 실행에서 같은 URL 을 또 때린다(workers=8 이면
  최대 7건). 설계 4절이 줍는지 버리는지를 **안 정해** 승인이 필요하다.
  **단위는 구조적으로 도달 못 한다** — 가짜 시계는 `sleep` 에서만 흐르고 `sleep` 은
  `inflight` 가 빌 때만 한다. e2e 가 `저장 N / 서버 응답 M` 으로 관측만 한다(0~1건).
- **`docs/patches/deadline-eq-form.patch`** — `--deadline=5` 가 조용히 무시되고 rc 0.
  근본 원인 `_number_flag` 가 `--max`·`--workers` 까지 걸려 설계 결정이다.

## 다음

**새 계획 탐색** — `rules/discover.md`, 5절 중복 방지(`index.md` 20개 항목 ·
`digest.md` · `plan_history_*`)를 먼저 돌린다.

## 밀린 집안일

`docs/history_current.md` 가 **689줄**이다(상한 300 / 20회). 줄 수로 회전이
밀렸다 — 오래된 것부터 `history_006.md` 로 밀어내고 `digest.md` 에 1~2줄로
압축한다. **스텝이 아니라 밤 마무리 때 한다**(직교 편집).

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘) ·
기존 `data/crawl.db` 재키잉/마이그레이션.
