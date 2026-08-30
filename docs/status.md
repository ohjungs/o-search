---
signal: GREEN
phase: 개발
step: 3
attempt: 0
iteration: 168
updated: 2026-08-30
ctx: 48
night_iterations: 45
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt`(중단 신호) 개발 phase — 스텝 2/4 완료.**
계획서: `docs/plan_graceful-interrupt.md` · 설계서: `docs/design_graceful-interrupt.md`.
브랜치: `loop/graceful-interrupt`. 작업 트리 깨끗 · 원격과 갈라짐 없음.
열린 계획 1. 직전 계획 33 `clock-injection` 은 DONE·아카이브 완료.
`main` 은 `f888518` 그대로, 병합은 사람 판단 항목이다.

기준선(반복 168 재측정): 단위 **441건 OK**(스텝 2 에서 +5) · e2e **17종 rc=0** ·
recall@10 100%/95% · 오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.
README 의 검증 숫자도 441 로 맞췄다(`test_verification_counts_match_reality`).

## 스텝 2 에서 한 것 — 워커가 중단을 본다

`_fetch_one(stop=None)` 에 **깨우기와 취소를 한 변경으로** 넣었다. 제품 코드는
`crawl.py` 만, `fetcher.py` 0줄(계약 4):

- `_fetch_one` **진입 검사** — 그 바로 뒤가 `robots.txt` 왕복이다. `(True, None, None, None)`.
- `before_send` **진입 검사** + `if remaining > 0 and wait(remaining): raise _Interrupted`
  — 한 표현이 "간격이 찼다"(`sleep` → `None`)와 "중단으로 깼다"(`Event.wait` → `True`)를
  다 덮는다(계약 3). 모듈 사설 예외는 `_fetch_one` 이 잡아 **`result = None`**.
- `_store_result` 는 `mark_sent`·`_apply_delay` **를 지난 뒤** `result is None` 이면 0 —
  나간 발신의 쿨다운은 걸고, 안 받은 페이지는 안 박는다(계약 5).
- `pool.submit(..., sleep, stop)` 배선.

**계획이 예상한 신규 2건이 5건이 됐다.** 늘어난 셋은 전부 실제로 살아남는 변이가 있어서다:
진입 검사(M2) · 중단된 시도를 안 박는다(M3·M4) · **`submit` 배선(M6)**. 특히 M6 은
`_fetch_one` 단위 4건이 **전부 통과하는데 실제 크롤은 오늘 그대로 재시도하는** 자리였다 —
단위 테스트가 워커 함수를 직접 부르면 배선은 아무도 안 본다.

**변이 판정 6/6 — 전부 죽었다** (441건 기준선 OK 인 `.git` 없는 사본 위에서):

| 변이 | rc | 죽인 테스트 |
|---|---|---|
| M1 취소를 지우고 잠 깨우기만 남긴다 | 1 | `test_signal_before_a_retry_sends_nothing` + 배선 테스트 |
| M2 `_fetch_one` 진입 검사 삭제 | 1 | `test_a_signal_already_up_opens_no_socket` |
| M3 `_store_result` 의 중단 가지 삭제 | 1 | `test_an_interrupted_attempt_is_not_stored` + 배선 테스트 |
| M4 중단을 `FetchResult(0,…)` 로 돌려준다 | 1 | `test_signal_before_a_retry_sends_nothing` |
| M5 깨우기 제거(`wait = sleep` 고정) | 1 | `test_no_signal_keeps_the_retry_interval` |
| M6 `submit` 이 `stop` 을 안 넘긴다 | 1 | `test_a_running_crawl_hands_the_signal_to_its_workers` |

**배운 것: 진입 검사가 스텝 1 의 테스트를 간헐적으로 깼다.** `test_signal_stops_new_
submissions_and_reaps_inflight` 는 "떠 있던 요청의 결과를 줍는다" 를 재는데, 아직 발신
안 한 워커가 신호를 보면 **정당하게 접어서** 그 결과가 아예 안 생긴다(전체 스위트 부하에서
1/4 확률로 재현). b.com 의 발신을 `threading.Event` 로 기다린 뒤 신호를 세우도록 고쳤다 —
제품 코드는 안 건드렸다. **정상 동작이 옛 테스트의 타이밍 가정을 깬 경우**라, 단언을
느슨하게 하지 않고 시나리오를 결정적으로 만드는 쪽으로 풀었다.

스텝 1 의 교훈 셋(약한 빨강 탐침 · `FakeStop` 이 아니면 변이가 무한 정지 ·
`reset --soft` 는 푸시된 스냅샷을 못 되돌린다)은 `docs/history_current.md` 에 있다.

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

**개발 스텝 3** — 계획서 4절 스텝 3(CLI 가 SIGINT 를 신호로 바꾼다). 설계서 **계약 7 이 명세**다.

- 시작 지점: `src/websearch/crawl.py` 의 `main()`(끝부분, `crawl(...)` 호출 자리) ·
  `tests/test_crawl.py`
- 할 일: `stop = threading.Event()` 를 만들고 `signal.signal(SIGINT, handler)` 로 걸어
  `crawl(..., stop=stop)` 에 넘긴다. **워커·메인 쪽은 스텝 1·2 로 이미 끝났다** —
  이 스텝은 배선과 종료 코드뿐이다.
- 놓치기 쉬운 계약(7번): 핸들러는 **`signal.signal(SIGINT, SIG_DFL)` 을 먼저,
  `stop.set()` 을 그다음** — 두 번째 Ctrl-C 가 즉사라야 사용자가 탈출구를 안 잃는다 ·
  `finally` 에서 **원래 핸들러를 복원**한다(`signal.getsignal(SIGINT)` 로 떠 둔다.
  안 하면 같은 프로세스의 다음 테스트가 오염된다) · **반환값은 중단이면 130**
  (오늘 관측값과 같은 값이라 `crawl && indexer` 가 중단 뒤에 다음 단계를 안 돈다) ·
  `수집 N 페이지` 는 중단이어도 찍는다.
- 안 깨져야 하는 것: `main()` 의 플래그 파싱 테스트 전부 · 스텝 1·2 의 신규 8건
- 변이로 확인할 것: 핸들러 복원 삭제 · 130 을 0 으로 · `SIG_DFL` 을 `stop.set()`
  뒤로 옮기기(두 번째 Ctrl-C 가 안 먹는다)
- 확인 방법: `PYTHONPATH=src python3 -m unittest discover -s tests` 441건 유지 + 신규
- **미결(계약 9)**: `crawl()` 독스트링의 "최악 90초" 는 계획 탐침이 오답으로 판정한
  숫자다(실측 69.57초). 어느 스텝에도 안 배정돼 있으니 스텝 3 에서 같이 고친다.

## 한도 (안 넘는다)

도메인당 1초 이상 · robots.txt `Crawl-delay` 준수 — **중단 중에도 그렇다**(위반은 RED).
`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
탐침 스크립트는 스크래치패드에 두고 저장소에 안 넣는다.
