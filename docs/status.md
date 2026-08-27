---
signal: GREEN
plan: domain-key
mode: night
phase: 테스트
step: 3/5
attempt: 0
iteration: 109
night_iterations: 20
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 109 · 017 테스트 phase 끝)
ctx: 71% / 200k
rules: 1411a37
---

# 현재 상태

**계획 017 `domain-key` 스텝 3(테스트) 끝.** 계획 `docs/plan_domain-key.md`.
브랜치 `loop/domain-key` (기점 `677ed3e`). 다음은 스텝 4(백지 리뷰).

**열쇠를 만드는 자리를 하나로 모았다.** `urls.domain_key(url)` — userinfo 를 떼고
호스트를 소문자로, 스킴의 **기본** 포트만 지운다. 세 호출부(`frontier.add` ·
`crawl` 제출 직전 · `robots._base`)가 그것만 쓴다. RED 는 먼저 봤다: 날 `netloc`
으로 되돌리면 단언 **10건**이 죽는다.

**문자열로만 가른다.** `urlsplit(...).port` 는 `:abc`·`:99999` 에 ValueError 를
던지고 `urlsplit` 자체도 닫히지 않은 IPv6 에 던진다 — 둘 다 감쌌다. 읽을 수 없는
URL 은 **자기 칸에 그대로** 둔다. 열쇠를 만들다 크롤 루프를 죽이는 쪽이 더 나쁘다.

**가짜를 진짜와 같은 열쇠 위에 다시 세웠다** (016 이 남긴 교훈 · digest `[6]`).
`FakeRobots._host` 와 테스트의 도메인 비교들이 전부 날 `netloc` 이었다 — 그대로면
대문자 호스트가 가짜 안에서는 여전히 두 서버라 이번 수정을 검증하지 못한다.

**변이 9종 중 M5(`"]" in port` 가드)만 살아남았었다.** 가드가 없어도 `[::1]` 은
다시 붙지만 **마지막 그룹이 소문자화를 못 받아** `[FE80::AB]` 가 칸 둘이 된다 —
대소문자 버그가 IPv6 로 옮겨간 것뿐이다. 단언 하나로 죽였다. 나머지 8종은 전부 죽는다.

**갭 ⑥ 둘을 메웠다:** `robots` 는 **서버당 `robots.txt` 한 번**(기대 5)을,
`crawl` 은 대소문자만 다른 씨앗 둘로 **루프 전체**의 간격 5초를 잰다. 양쪽 다
대조군(다른 스킴·기본이 아닌 포트)을 붙였다 — 안 붙이면 "전부 한 칸" 으로도 통과한다.

**348건 OK** · `perf_crawl` [차단] **10.34/s** · `crawl_politeness`·`crawl_delay`·
`retry_interval` 전부 0.

**남은 것:** 스텝 4 백지 리뷰(diff + 소스만, `docs/` 차단) → 스텝 5 e2e.

**하지 않을 것:** URL 정규화(digest `[5]`). `http://A.com/` 과 `http://a.com/` 은 이
계획 뒤에도 두 번 수집되고 두 행으로 저장된다 — 고치는 것은 **예의 계약이 세는 단위**
하나뿐이다.

## 직전 계획 (016 `retry-interval`) — DONE

재시도가 프런티어가 아는 간격을 바닥으로 쓴다. e2e 실측 **5.01초**(고치기 전 1.0).
계획서 `docs/plan_history_014.md` · e2e `docs/e2e/retry-interval/result.md` ·
색인 `docs/index.md` 16번 · 남긴 교훈 셋은 `docs/history_current.md` 반복 106.

## 다음 계획 (후보)

1. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기
2. `Ctrl-C` 최악 대기(digest `[4]`·`[6]`) — 진짜 답은 `--deadline` 이거나 워커가
   주기적으로 보는 중단 플래그다. 016 이 최악값을 키웠다

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
