---
signal: GREEN
plan: null (사용자 승인 보류 패치 2건 소진 — deadline-patches)
phase: 계획
step: -
attempt: 0
iteration: 133
night_iterations: 16
night_red: 0
night_retries: 0
updated: 2026-08-29 16:50 (반복 133 · 보류 패치 2건 적용)
ctx: 51% / 200k
stopped: -
rules: 1411a37
mode: night (지시 실행 — 준 것만 하고 정지)
---

# 현재 상태

**열린 계획 없음. 보류 패치 0건 — `docs/patches/` 는 비었다.**
단위 **403건 OK** · e2e **17종 전부 rc=0**.

## 이번 세션 (반복 132~133) — `loop/deadline-patches` (기점 `e57f7bc` = main)

사용자가 승인한 보류 패치 2건을 열었다. 둘 다 020 `deadline` 리뷰 3/4 가 남긴 것이다.

**132 · `deadline-inflight-reap`(critical).** 예산 만료 `break` 가 떠 있는 요청의
결과를 통째로 버렸다. executor 는 `with` 를 나갈 때 어차피 그것들을 기다리므로
**시간은 치르고 결과만 버리는** 셈이고, 다음 실행이 같은 URL 을 또 때린다.
승인이 필요했던 이유는 설계 4절이 **줍는지 버리는지를 안 정했기** 때문이고,
**줍는 쪽으로 정했다** — 추가 대기 0, 크롤 윤리로도 이득, 새 요청은 안 나간다
(`_store_result` 는 네트워크를 안 한다). 결정과 근거는 `crawl()` 문서열에 있다.
`design_history_018.md` 는 아카이브라 안 건드렸다.

**패치가 "단위 테스트 없음" 이라고 적었지만 쓸 수 있었다.** 시간을 흘리는 손잡이가
`sleep` 말고 하나 더 있다 — **저장이다**(`store.upsert` 훅). 상세는 `history_current.md`.

**133 · `deadline-eq-form`.** 패치보다 **넓게** 적용했다. 패치는 `main()` 의 `given`
한 줄만 고쳐 `--deadline` 만 막았지만 근본 원인은 `_number_flag` 가 `--name=값` 을
모르는 것이고 `--max`·`--workers` 가 같은 파서다. 세 형태를 파서 한 자리에서 안다.
e2e 시나리오 1이 `--deadline=2 --workers=8` 붙임 형태로 **진짜 argv** 를 준다 —
단위는 `main()` 을 직접 부르므로 argv 형태를 보는 자리는 거기뿐이다.
시나리오 2의 **버려진 응답 수도 단언(0)이 됐다**(줍기를 빼면 3회 모두 1건 — 눈멀지 않았다).

## 다음

**집안일 하나가 밀려 있다** — `history_current.md` 가 **328줄**로 상한 300 을 넘었다
(`docs.md`). 이번 세션은 지시 실행이라 범위 밖으로 두고 적어만 둔다.
그 다음은 새 계획 탐색이다(`digest.md ## 다음 계획 후보` · `index.md`).

## 열지 않는 것 (사용자 판단 대기)

`data/crawl.db` 재키잉/옛 열쇠 행 통합(마이그레이션) · URL userinfo 가 `pages.url` PK
이자 검색 결과에 렌더되는 것(보안 경계) · `recrawl`(`fetched_at` 스키마) ·
`X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합 · 의존성 추가·업그레이드 ·
`docs/specs/` 쓰기.
