---
signal: GREEN
phase: 설계
step: 0
attempt: 0
iteration: 163
updated: 2026-08-30
ctx: 60
night_iterations: 43
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt`(중단 신호) 계획서 작성 완료 → 설계 phase.**
계획서: `docs/plan_graceful-interrupt.md`. 브랜치: 아직 `loop/clock-injection`
(개발 착수 시 `loop/graceful-interrupt` 를 판다). 열린 계획 1.
직전 계획 33 `clock-injection` 은 DONE·아카이브 완료 — `index.md` 33번 ·
`plan_history_020.md` · `design_history_020.md`. `main` 은 `f888518` 그대로,
병합은 사람 판단 항목이다.

기준선(계획 33 e2e 시점, 안 움직였다): 단위 **433건 OK** · e2e **17종 rc=0** ·
recall@10 100%/95% · 오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.

## 이번 계획이 서 있는 실측

`Crawl-delay: 30` + 응답 없는 로컬 서버에 `--workers 1` 로 크롤을 걸고 0.5초 뒤 SIGINT:
**종료까지 69.57초.** 서버 수신 `t=0.05 / 30.07 / 60.07`(발신 간격 30.01초).

| 구간 | 자리 | 실측 | `Event.wait` 로 지워지나 |
|---|---|---|---|
| 소켓 읽기 × 3 | `fetcher.py:39` `urlopen(timeout=10)` | **30초** | **아니오** |
| 재시도 앞 잠 × 2 | `crawl.py:74` `sleep(remaining)` | **40초** | 예 |

**`digest.md` 의 "최악 90초" 는 틀렸다 — 70초다.** `before_send` 의
`remaining = interval - (now() - sends[-1])` 이 흘러간 타임아웃 10초를 이미 뺀다.
그리고 손이 가장 많이 가는 상황(느린 서버·재시도 없음)은 **7.56초가 전부 소켓 읽기**라
`Event.wait` 가 **0초** 줄인다. 잠만 깨우면 `Crawl-delay: 30` 서버에 10초 간격 3발이
나가 예절이 깨진다 — **잠 깨우기와 재시도 취소는 하나의 변경이다.**

**넷째 자리를 아무도 안 세고 있었다.** 플래그만 세우는 SIGINT 핸들러는
`crawl.py:184` 의 `concurrent.futures.wait(timeout=20)` 을 **못 깨운다**(실측 20.01초 다
잔다 · `time.sleep(5)` 도 5.01초 · `Event.wait(20)` 만 0.51초). PEP 475 로 락 획득이
남은 시간으로 재시도되기 때문이고, 오늘 Ctrl-C 가 그나마 먹는 이유는 기본 핸들러가
**예외를 던져서**다. 정정 전문은 `digest.md` `[4]`.

## 다음 스텝

**설계 phase 1스텝** — `docs/design_graceful-interrupt.md`.
설계가 답할 것은 **네 자리(소켓 · `:74` 재시도 앞 잠 · `:179` 메인 루프 잠 ·
`:184` `futures.wait`)를 몇 개의 기제로 덮는가**이고, 특히 `futures.wait` 를 어떻게
깨울지다. 워커가 재시도를 포기하는 방법이 셋으로 갈린다(계획서 3절 ①②③).

- 시작 지점: `src/websearch/crawl.py:64~76`(`before_send`)·`:145~191`(메인 루프)
- 이미 참인 것: `crawl()`·`_fetch_one()` 이 `sleep=` 을 받는다(계획 33). 위 실측 4종.
- 확인 방법: 설계서가 계획서 5절 e2e 시나리오 5개를 전부 판정 가능하게 만드는가
- 이미 한 것: 계획서 · `digest.md` `[4]`/`[6]` 정정. 코드 0줄.

## 한도 (안 넘는다)

도메인당 1초 이상 · robots.txt `Crawl-delay` 준수 — **중단 중에도 그렇다**(위반은 RED).
`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
탐침 스크립트는 스크래치패드에 두고 저장소에 안 넣는다.
