---
signal: DONE
mode: night
plan: null
phase: 완료
step: 1/1
attempt: 0
iteration: 89
night_iterations: 13
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 89 · 야간 종료)
ctx: 42% / 200k
rules: rules/docs.md
---

# 현재 상태

**야간 실행 종료 — 계획 없음(`plan: null`). 정지 사유는 한도가 아니라 "할 일을 마쳤다" 다**
(ctx 42% · 5h 3% · 7d 68%, 셋 다 85 아래). 새로 시작하면 `rules/discover.md` 로 탐색한다.

| 반복 | 커밋 | 무엇 |
|---|---|---|
| 83~88 | `5a66070`…`46b9854` | `cooldown-burn`(011) 설계→e2e **DONE** · 아카이브 완료 |
| 89 | `8860600` | **짧은 경로** — 크롤러가 UA 를 실제로 보내는지 단언 3건 |

브랜치 `loop/cooldown-burn` (기점 `9bd3771`). **병합은 사람 몫이다.**
계획 `docs/plan_history_011.md` · 설계 `docs/design_history_011.md` ·
e2e `docs/e2e/cooldown-burn/result.md` · 야간 보고서 `docs/reports/night_2026-08-27.md`.

## 최종 값

| | 착수 전 | 지금 |
|---|---|---|
| 차단 사이트 처리량 | **4.48/s** (컨셉 목표 5.0 미달) | **10.29/s** (목표 9.0) |
| 요청 없이 태운 쿨다운 | 120회 팝 중 **72회** | **0회** |
| 페이지 최소 간격 | 1.003s | **1.004s** — 안 깎였다 |

**269건 통과** · `crawl_delay_e2e.py` 종료 0 · `design_check.py` 종료 0 · 검색 p95 9.26ms.
간격 시계는 팝이 아니라 **`mark_sent()` 하나**에 걸린다(설계 A). 변이 2종으로
e2e 가 실제로 잡는 것을 반복 88 에서 재확인했다 — **검사 하나가 초록이라고 구멍이 없는 것이 아니다.**

## 다음 세션이 볼 것

`digest.md ## 판단 필요` 에 **설계 결정 2건**. 둘 다 크롤 윤리 축이고
**야간 자동 적용 대상이 아니다.** `cooldown-burn` 이 연 것이 아니라 원래 있던 구멍이고,
착수 전 커밋과 대조 실측으로 확인했다. 같은 파일(`fetcher.py`·`robots.py`)이라 **함께 열면 싸다**:

1. `Crawl-delay` 도메인의 첫 요청이 예외면 그 뒤가 1.0초로 나간다 (선언값 5.0초 위반)
2. `fetcher` 재시도가 연결 실패 시 **3회를 0.4ms 안에** 보낸다 (반복 87 실측)

## 열지 않는 것 (승인 대기 — 야간 금지)

`recrawl`(`fetched_at` 스키마) · `X-Robots-Tag`(스키마) · `loop/*` 브랜치 병합.
`store.has` 상태 불문 스킵은 **recrawl 계획 소관**(반복 82 탐침).
