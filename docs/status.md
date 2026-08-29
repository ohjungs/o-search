---
signal: GREEN
plan: null (집안일 + 짧은 경로 robots-read-cap 완료)
phase: 계획
step: -
attempt: 0
iteration: 131
night_iterations: 14
night_red: 0
night_retries: 0
updated: 2026-08-29 15:12 (반복 131 · robots.txt 512KB 상한)
ctx: 45% / 200k
stopped: -
rules: 1411a37
mode: night
---

# 현재 상태

**열린 계획 없음.** 020 `deadline` DONE(아카이브: `plan_history_018` ·
`design_history_018` · `index.md` 20번 · e2e `docs/e2e/deadline/`).
그 뒤 짧은 경로 2건 — `indexer-cli-guard`(21번) · `robots-read-cap`(22번).
단위 **399건 OK** · e2e **17종 전부 rc=0**.

## 승인 대기 (020 이 남긴 보류 2건)

- **`docs/patches/deadline-inflight-reap.patch`** (critical) — 예산 만료 `break` 가
  **떠 있는 요청의 결과를 버린다**. executor 는 나갈 때 어차피 기다리므로 시간은
  치르고 결과만 버리는 셈이고 다음 실행에서 같은 URL 을 또 때린다(workers=8 이면
  최대 7건). 설계 4절이 줍는지 버리는지를 **안 정해** 승인이 필요하다.
  **단위는 구조적으로 도달 못 한다** — 가짜 시계는 `sleep` 에서만 흐르고 `sleep` 은
  `inflight` 가 빌 때만 한다. e2e 가 `저장 N / 서버 응답 M` 으로 관측만 한다(0~1건).
- **`docs/patches/deadline-eq-form.patch`** — `--deadline=5` 가 조용히 무시되고 rc 0.
  근본 원인 `_number_flag` 가 `--max`·`--workers` 까지 걸려 설계 결정이다.

## 그 뒤 — 짧은 경로 1건 (반복 129)

**`indexer-cli-guard` 완료.** 브랜치 `loop/indexer-cli-guard`(기점 `9a47341`).
`pages` 없는 DB 가 트레이스백+rc=1 이던 것을 `NoCrawlDataError` → rc=2 로 닫았다.
**digest 의 처방("CLI 진입점마다 방어를 따로 쓴다")은 과했다** — 탐침하니
`serve.main`·`crawl.main` 은 이미 막고 있어 남은 구멍 한 곳만 고쳤다. `index.md` 21번.

## 그 뒤 — 짧은 경로 1건 (반복 131)

**`robots-read-cap` 완료.** `robots._fetch_robots` 의 `resp.read()` 가 무인자였다 —
`fetcher` 는 `MAX_BYTES` 로 막는데 여기만 크기를 남이 정하는 바이트가 통째로 들어왔다.
`MAX_ROBOTS_BYTES = 512_000`(RFC 9309 2.5). 근거는 `digest.md` 후보 `[5]`.
단위 **399건 OK** · e2e **17종 rc=0**. `index.md` 22번 · digest `[5]` 닫음.

**후보가 적어 둔 "한 줄이면 고쳐진다" 는 틀렸다** — 상한이 곧 파서 입력이라
**자르는 방향**이 계약이다. 반쪽 `Disallow: /sec` 는 원문 `/secret` 보다 덜 막는다.
그리고 **변이 M1(`read` 인자 삭제)이 처음엔 살아남았다**: 가짜 응답이 무인자 `read()`
에 전문을 돌려주는데 뒤의 잘라내기가 그것을 덮어, "읽고 나서 자르면 늦다" 는
이 변경의 존재 이유가 초록불에 가려져 있었다. `read` 에 준 수를 직접 단언해 닫았다.

**사람이 볼 것 — 이것을 보안·자원 건으로 보고 야간에 미뤄야 했나.**
`severity.md` 3절의 "보안 전반" 은 인증·XSS·주입을 가리키고 이건 자원 상한이다.
동작은 **좁아지는 쪽으로만** 바뀌고(덜 읽는다), 테스트 3건·변이 4종·e2e 17종이 덮고,
되돌리기는 `git revert eb6697e` 하나다. 그래서 패치가 아니라 커밋으로 넣었다.
판단이 다르면 그 커밋만 되돌리면 된다.

## 다음

**새 계획 탐색.** 1~4순위(실패 테스트·TODO·`candidates.md`)는 지금 전부 비어 있다 —
다음 탐색도 `digest.md` 후보 절에서 시작하게 된다. 5절 중복 방지는 `index.md`
**22개** 항목으로 돌린다.

무인 모드에서 열 수 있는 후보가 얇아지고 있다. `digest.md` 에 남은 큰 것들은
대부분 **승인 대기**(recrawl·마이그레이션·userinfo·`X-Robots-Tag`)라 야간 금지다.
이번 밤은 그 판단이 **결론이 아니라 단서**였음을 확인했다 — 후보 절을 다시 읽으니
승인 제약에 안 걸리는 자원 상한 건이 하나 남아 있었다. 다만 이제 정말 얇다.
다음 밤이 빈손으로 끝나면 그건 탐색 실패가 아니라 **사용자 판단이 밀린 것**이다.

## 집안일 — 회전 완료 (반복 130)

`docs/history_current.md` **722 → 259줄**. 반복 97~122(계획 015~019)를
`history_006.md` 로 밀어냈고 `digest.md ## 완료` 에 아카이브 한 줄을 더했다.
015·016·017 은 digest 완료 절에 항목이 없어 그 줄에 `index.md` 15~17번과
`## 판단 필요` 항목을 가리키는 포인터를 적었다 — 안 적으면 탐색이 못 찾는다.
잘린 자리의 "바로 위 두 항목" 참조는 `history_current.md` 헤더에 한 줄로 복구했다.
무손실 확인: 원본 722줄이 헤더 24 + 아카이브 466 + 잔류 232 로 `diff` 0.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘) ·
기존 `data/crawl.db` 재키잉/마이그레이션.
