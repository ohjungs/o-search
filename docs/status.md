---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 164
updated: 2026-08-30
ctx: 63
night_iterations: 44
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt`(중단 신호) 설계 완료 → 개발 phase.**
계획서: `docs/plan_graceful-interrupt.md` · 설계서: `docs/design_graceful-interrupt.md`.
브랜치: 아직 `loop/clock-injection` (개발 착수 시 `loop/graceful-interrupt` 를 판다).
열린 계획 1. 직전 계획 33 `clock-injection` 은 DONE·아카이브 완료.
`main` 은 `f888518` 그대로, 병합은 사람 판단 항목이다.

기준선(계획 33 e2e 시점, 안 움직였다): 단위 **433건 OK** · e2e **17종 rc=0** ·
recall@10 100%/95% · 오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.

## 설계가 정한 것 — 네 자리를 **두 자리로** 줄였다

**`stop` 이벤트 하나**를 `now`·`sleep` 옆 인자로 받아 **깨우고**(`stop.wait`)
**접는다**(`stop.is_set`). 대안 3갈래 중 B(정공법). 전문은 설계서.

| 축 | 자리 | 무엇으로 | 근거 |
|---|---|---|---|
| 1 | 소켓 `fetcher.py:39` | **0줄** | 재시도를 접으면 30초 → **10초 1회**. 목표 12초 안이다 |
| 2 | 재시도 잠 `:74` | `stop.wait` + `is_set` | 깨우기와 취소는 **한 변경**(따로 하면 10초 간격 3발 → RED) |
| 3 | 메인 잠 `:179` | `stop.wait` | 깨워 줄 워커가 없는 **유일한** 자리 |
| 4 | `futures.wait` `:184` | **0줄** | 축1·2를 덮으면 워커 완료가 `FIRST_COMPLETED` 로 메인을 깨운다 |

**가장 위험한 가정을 탐침으로 깼다**(`design.md` 3-2, 스크래치패드 `gi_probe3.py`):
타임아웃 30초를 준 `futures.wait` 가 **[A] 잠든 워커 0.51초 · [B] 소켓에 갇힌 워커
3.01초 · [C] 대조군(신호 없음) 2.01초**에 복귀했다. 계획 탐침의 "20.01초 다 잔다" 는
**워커가 계속 도는 경우**였다 — 워커를 끝내면 같은 자리가 저절로 깬다.

## 다음 스텝

**개발 스텝 1** — 계획서 4절 스텝 1(메인 루프에 중단 가지). 설계서 **계약 절이 곧 명세**다.

- 시작 지점: `src/websearch/crawl.py:145~191`(메인 루프) · `tests/test_crawl.py`
- 먼저 할 것: 브랜치 `loop/graceful-interrupt` 를 판다
- 놓치기 쉬운 계약: 2번(`wait = sleep if stop is None else stop.wait` — 가짜 시계
  10곳과 `test_injected_sleep_is_the_only_one_used` 가 안 깨져야 한다) ·
  5번(중단된 시도는 **upsert 하지 않는다** — `FetchResult(0,…)` 을 쓰면 안 받은
  페이지가 status 0 으로 박혀 다음 실행이 그 URL 을 영영 건너뛴다)
- 확인 방법: `PYTHONPATH=src python3 -m unittest discover tests` 433건 유지 + 신규
- 이미 한 것: 계획서 · 설계서 · `digest.md` `[4]`/`[6]` 정정 · 탐침 3종. 코드 0줄.

## 한도 (안 넘는다)

도메인당 1초 이상 · robots.txt `Crawl-delay` 준수 — **중단 중에도 그렇다**(위반은 RED).
`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
탐침 스크립트는 스크래치패드에 두고 저장소에 안 넣는다.
