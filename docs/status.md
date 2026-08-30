---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 166
updated: 2026-08-30
ctx: 42
night_iterations: 44
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt`(중단 신호) 개발 phase — 스텝 1/4 완료.**
계획서: `docs/plan_graceful-interrupt.md` · 설계서: `docs/design_graceful-interrupt.md`.
브랜치: `loop/graceful-interrupt` (`d31560a`). 작업 트리 깨끗 · 원격과 갈라짐 없음.
열린 계획 1. 직전 계획 33 `clock-injection` 은 DONE·아카이브 완료.
`main` 은 `f888518` 그대로, 병합은 사람 판단 항목이다.

기준선(반복 166 에서 재측정): 단위 **436건 OK**(스텝 1 에서 +3) · e2e **17종 rc=0**(약 135초) ·
recall@10 100%/95% · 오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.

## 스텝 1 에서 한 것 — 메인 루프가 신호를 본다

`crawl(stop=None)` 을 추가했다. 신호가 서면 **새 URL 을 제출하지 않고 예산 소진
가지로 빠진다**(떠 있는 결과는 줍고, 사유를 찍고, `break`) — 새 종료 경로 0개.
메인 잠(축3)은 `wait_fn = sleep if stop is None else stop.wait` 로 간다.
`fetcher.py` 0줄, 워커 쪽 0줄. `stop=None` 이면 오늘 동작 그대로다.

**배운 것 셋** (테스트·리뷰 스텝이 이어받을 것):

1. **약한 빨강을 탐침으로 뚫었다.** 첫 RED 는 `TypeError: unexpected keyword
   argument 'stop'` 뿐이었다. `stop=` 을 **받기만 하고 안 보는** 탐침으로 다시 돌리니
   오늘 실제 동작이 나왔다 — 신호 뒤에 `http://a.com/1` 이 **한 건 더 나가** 3건을
   수집했고, 메인은 `stop.waits == []` 로 주입된 `sleep` 에 잠들어 있었다.
2. **가짜 시계 위에서 선 `Event` 는 테스트를 멈춘다.** 변이 M1(꼭대기 검사 제거)이
   실패가 아니라 **무한 정지**로 나왔다 — 선 `Event.wait` 는 즉시 돌아오는데 가짜
   시계는 그때 안 흘러 쿨다운이 영영 안 찬다. 테스트 더블 `FakeStop`(잔 만큼 시계를
   흘리고 `is_set` 을 돌려준다)으로 바꿔 그 변이가 **0.004초에 죽는다**.
   스텝 2·3 의 중단 테스트도 같은 더블을 쓴다.
3. **`reset --soft` 는 푸시된 스냅샷을 못 되돌린다.** 05:37 자동 스냅샷(`06bc289`)이
   **변이 M1 이 심긴 트리**를 커밋하고 **원격까지 올려** 브랜치가 갈라져 있었다.
   `merge -s ours` 로 트리를 유지한 채 풀었다(`d31560a`, 강제 푸시 없음).
   스냅샷 훅이 끼어들었으면 **접기 전에 `git log origin/<브랜치>` 를 본다.**
   변이는 `.git` 없는 스크래치패드 사본에서만 심는다.

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

**개발 스텝 2** — 계획서 4절 스텝 2(워커가 중단을 본다). 설계서 **계약 절이 곧 명세**다.

- 시작 지점: `src/websearch/crawl.py:64~76` 의 `_fetch_one`(재시도 잠은 `:74`) ·
  `tests/test_crawl.py`
- 할 일: `_fetch_one(stop=None)` 을 받아 **깨우기와 취소를 한 변경으로** 넣는다.
  둘을 쪼개면 `Crawl-delay: 30` 서버에 10초 간격 3발이 나간다 — 그것이 RED 다.
- 놓치기 쉬운 계약: **3번**(`if remaining > 0 and wait(remaining):` — `time.sleep` 은
  `None`(거짓), `Event.wait` 는 선 경우 `True` 라 한 표현이 두 경우를 덮는다) ·
  **5번**(중단된 시도는 **upsert 하지 않는다** — `FetchResult(0,…)` 을 쓰면 안 받은
  페이지가 status 0 으로 박혀 다음 실행이 그 URL 을 영영 건너뛴다. `_store_result`
  에서 `result is None` 이면 `mark_sent`·`_apply_delay` **뒤에** 0 을 돌려준다) ·
  **4번**(발신 취소는 `_fetch_one` 진입 시와 `before_send` 진입 시 두 곳. 신호 뒤에
  새로 여는 소켓 0개). `fetcher.py` 는 **0줄**이다(계약 4).
- 안 깨져야 하는 것: `TestRetriesKeepTheInterval` · 가짜 시계 10곳 ·
  `test_injected_sleep_is_the_only_one_used`
- 변이로 확인할 것(계획서 4절): 취소를 지우고 잠 깨우기만 남기면 발신이 2회 나가
  예절 단언이 죽어야 한다
- 확인 방법: `PYTHONPATH=src python3 -m unittest discover tests` 436건 유지 + 신규
- **테스트 더블은 이미 있다** — `tests/test_crawl.py` 의 `FakeStop`. 선 `Event` 를
  가짜 시계와 섞지 마라(위 "배운 것" 2번).

## 한도 (안 넘는다)

도메인당 1초 이상 · robots.txt `Crawl-delay` 준수 — **중단 중에도 그렇다**(위반은 RED).
`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
탐침 스크립트는 스크래치패드에 두고 저장소에 안 넣는다.
