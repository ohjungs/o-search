---
signal: GREEN
phase: 개발
step: 4
attempt: 0
iteration: 169
updated: 2026-08-30
ctx: 40
night_iterations: 46
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt`(중단 신호) 개발 phase — 스텝 3/4 완료.**
계획서: `docs/plan_graceful-interrupt.md` · 설계서: `docs/design_graceful-interrupt.md`.
브랜치: `loop/graceful-interrupt`. 작업 트리 깨끗 · 원격과 갈라짐 없음.
열린 계획 1. 직전 계획 33 `clock-injection` 은 DONE·아카이브 완료.
`main` 은 `f888518` 그대로, 병합은 사람 판단 항목이다.

기준선(반복 169 재측정): 단위 **445건 OK**(스텝 3 에서 +4) · e2e **17종 rc=0** ·
recall@10 100%/95% · 오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.
README 의 검증 숫자도 445 로 맞췄다(`test_verification_counts_match_reality` 가 잡았다).

**Ctrl-C 가 이제 실제로 먹는다.** 실물 탐침(로컬 서버 `Crawl-delay: 30` · CLI 를
서브프로세스로 띄워 진짜 SIGINT): **rc 130 · 신호 뒤 0.01초 · 받아 둔 1페이지 유지 ·
중단 중 새 요청 0**. 목표(12초)에 크게 남는다. 이것을 e2e 로 굳히는 것이 스텝 4 다.

## 스텝 3 에서 한 것 — CLI 가 SIGINT 를 신호로 바꾼다

`main()` 끝부분만 바뀌었다(제품 25줄). 루프·워커는 스텝 1·2 로 이미 끝나 있었다.

- `stop = threading.Event()` → `crawl(..., stop=stop)`.
- 핸들러: **`signal.signal(SIGINT, SIG_DFL)` 먼저 → `stop.set()` 그다음.**
  두 번째 Ctrl-C 는 기본 동작으로 즉사한다 — 사용자가 탈출구를 잃는 창이 없다.
- `previous = signal.signal(SIGINT, interrupt)` / `finally` 로 복원. **설계서가 적은
  `getsignal` 대신 `signal.signal` 의 반환값**을 썼다 — 같은 객체인데 호출이 하나 줄고
  등록과 저장이 한 줄로 붙어 순서를 틀릴 자리가 없다.
- 반환값 **중단이면 130**(오늘 관측값과 같아 `crawl && indexer` 판정이 안 바뀐다),
  아니면 0. `수집 N 페이지` 는 중단이어도 찍는다.
- **계약 9 를 같이 닫았다** — `crawl()` 독스트링의 "최악 90초" 를 실측 69.57초와
  분해(간격 대기가 이미 흘러간 타임아웃을 뺀다)로 고쳤다.

**변이 판정 4/4 — 전부 죽었다** (445건 기준선 위, 스크래치패드에서 심고 복원):

| 변이 | rc | 죽인 테스트 |
|---|---|---|
| M1 중단 종료 코드를 0 으로 | 1 | `test_the_handler_disarms_itself…` + 복원 테스트 |
| M2 핸들러가 자기를 안 내린다(`SIG_DFL` 삭제) | 1 | `test_the_handler_disarms_itself_before_setting_the_signal` |
| M3 원래 핸들러를 복원하지 않는다 | 1 | `test_the_original_handler_comes_back` (세 갈래 전부) |
| M4 `crawl` 에 `stop` 을 안 넘긴다 | 1 | `test_main_hands_a_stop_event_to_the_crawl` |

**배운 것: 신호 테스트에 진짜 신호를 쓰면 안 된다.** `os.kill(getpid(), SIGINT)` 는
핸들러가 제 손으로 `SIG_DFL` 로 내려간 **뒤라 테스트 프로세스를 죽인다.** 설치된
핸들러를 직접 부르고, 각 테스트는 센티널 핸들러를 깔았다 되돌리는 컨텍스트 매니저
안에서 돈다 — **복원 계약을 재는 테스트가 곧 다른 테스트의 오염 방지**다.

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

**개발 스텝 4** — 계획서 4절 스텝 4(중단 e2e). 시나리오는 계획서 **5절이 확정해 뒀다**.

- 만들 것: `e2e/interrupt_e2e.py` 신규. `e2e/deadline_e2e.py` 가 서버·임시 DB·`--control`
  관용구의 본이다(종료 0 통과 / 1 위반 / 2 측정 불능).
- **뼈대는 이미 있다** — 스텝 3 의 실물 탐침(스크래치패드 `sigint_probe.py`)이
  로컬 서버 + `Crawl-delay: 30` + 서브프로세스 SIGINT 로 rc 130 · 0.01초를 이미 쟀다.
  e2e 는 여기에 **DB 유실 0** 과 **중단 중 새 요청 0**(서버 접근 로그)을 더한 것이다.
- `crawl()` 직접 호출이 아니라 **CLI 서브프로세스**로 잰다 — 신호는 프로세스 경계의
  물건이고, 계획 020 의 M6(CLI 가 안 넘기는 변이)이 단위에 안 잡힌 전례가 있다.
- 완료 기준: `PYTHONPATH=src python3 e2e/interrupt_e2e.py` rc=0 + **변이 3종에서 전부
  실패**(① 스텝 1 루프 검사 제거 ② 스텝 2 재시도 취소 제거 ③ 스텝 3 핸들러 등록 제거).
  e2e 전체 **18종** rc=0 · `docs/project.md` 와 README 숫자도 같이 올린다.
- 그다음: 개발 4/4 가 닫히면 테스트 → 리뷰 → e2e phase.
- **미결(문서 위생)**: `docs/history_current.md` 가 322줄로 상한 300 을 넘었다.
  스텝 3 전에 이미 302줄이었다 — 회전(오래된 것 → `history_011.md` + digest 압축)이
  한 반복 밀려 있다.

## 한도 (안 넘는다)

도메인당 1초 이상 · robots.txt `Crawl-delay` 준수 — **중단 중에도 그렇다**(위반은 RED).
`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
탐침 스크립트는 스크래치패드에 두고 저장소에 안 넣는다.
