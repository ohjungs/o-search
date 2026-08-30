---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 171
updated: 2026-08-30
ctx: 62
night_iterations: 48
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 34 `graceful-interrupt` 테스트 phase 1스텝 DONE — 제품 코드 0줄, 테스트 +2·강화 1.**
계획서: `docs/plan_graceful-interrupt.md` · 설계서: `docs/design_graceful-interrupt.md`.
브랜치: `loop/graceful-interrupt`. 작업 트리 깨끗 · 원격과 갈라짐 없음.
열린 계획 1. `main` 은 `f888518` 그대로, 병합은 사람 판단 항목이다.

기준선: 단위 **447건 OK**(445 → +2) · e2e **18종 전수 rc=0** · recall@10 100%/95% ·
오탐 평균 14.0 · p95 9.33ms · JS 0 B · 최저 명암비 4.87:1.
README 의 단위 건수도 447 로 맞췄다(`test_readme.py` 가 강제한다).

## 갭을 어떻게 찾았나 — 변이 17종을 직접 다시 돌렸다

**앞 세션(API 502 로 사망)이 남긴 결론을 물려받지 않고 처음부터 다시 쟀다.**
그 세션은 "살아남은 둘은 진짜 계약 구멍이고 서로를 가려주고 있다" 는 한 줄만 남겼고
**어느 변이인지는 기록이 없었다.** 스크래치패드 사본(`.git` 없음)에 계약 1~9 변이
14종을 심어 재판정한 결과가 **12종 사망 · 2종 생존**이고, 생존 둘은 아래다.
심기 전 `count(old) == 1` 을 단언했다(BSD `sed -i ''` 거짓 초록 대응).

| 변이 | 1차 | 무엇이 안 재지고 있었나 |
|---|---|---|
| C3 깬 이유를 안 구별 | **생존** | 계약 3 — 잠자는 **동안** 선 신호 |
| C4b `before_send` 진입 검사 제거 | **생존** | 계약 4 — 간격이 **이미 지난** 재시도 |

**둘이 서로를 가려주고 있었다.** 옛 테스트는 신호를 잠들기 **전에** 세워 두므로
C3 을 지우면 진입 검사(C4b)가 잡고, C4b 를 지우면 `wait` 반환값(C3)이 잡는다 —
한쪽씩 지우면 늘 초록이고, **둘을 같이 지워야 구멍이 보인다.** 그래서 새 테스트는
각각 **상대가 못 걸리는 상황**을 만든다: 잠든 사이에 서는 신호(`WokenStop`) ·
간격이 이미 지나 잠이 아예 없는 재시도.

## 셋째 구멍 — 이름이 약속한 것을 안 재던 테스트

변이 14종이 다 죽은 뒤 순서·회수 축으로 3종을 더 심었고 거기서 하나가 더 나왔다.

**`test_the_handler_disarms_itself_before_setting_the_signal` 이 순서를 안 쟀다.**
이름과 독스트링은 "SIG_DFL 먼저, `stop.set()` 그다음"(계약 7)을 고정한다고 적어
뒀는데, 실제로 보는 것은 **핸들러가 돌아온 뒤의 상태**였다 — 두 순서 다 끝나고 보면
`SIG_DFL` 이고 신호도 서 있다. 순서를 뒤집는 변이(C7d)가 **447건을 전부 통과했다.**
`stop.set()` 이 불리는 **그 순간**의 `signal.getsignal(SIGINT)` 를 보도록 고쳤다.
막는 것은 실사용 고장이다: 순서가 반대면 첫 Ctrl-C 와 둘째 사이에 **탈출구 없는 창**이
생긴다(둘째 신호가 이미 선 이벤트를 다시 세울 뿐이다).

**일반화 — 테스트 이름이 재겠다고 말한 것과 단언이 실제로 재는 것을 따로 확인한다.**
여기서는 변이가 그 차이를 드러냈다. 이름만 읽으면 덮인 줄 안다.

## 검증 (전부 실행함)

- `PYTHONPATH=src python3 -m unittest discover -s tests` → **447건 OK** (3.2초)
- e2e 18종 각각 `timeout 120 PYTHONPATH=src python3 e2e/<f>.py` → **전수 rc=0**
- 변이 **17/17 사망** — 새 테스트 셋이 각각 제 변이만 물었다:
  C3 → `test_a_signal_during_the_wait_cancels_the_retry` ·
  C4b → `test_a_retry_past_its_interval_is_still_cancelled` ·
  C7d → `test_the_handler_disarms_itself_before_setting_the_signal`
- 한도 확인: **간격 기대값·`DOMAIN_INTERVAL`·1초 하한·robots·`Crawl-delay` 를 안 건드렸다.**
  대조군 `test_no_signal_keeps_the_retry_interval` 과 변이 `Cx`(하한 제거)가 그것을 지킨다.
  **단언을 낮춘 곳 0** — 고친 한 건은 단언을 **더 세게** 만든 것이다(제품 코드 아님).

## 다음 — 리뷰 phase

- 볼 곳: 이번 diff 는 `tests/test_crawl.py` 하나(+`README.md` 숫자 한 줄)다.
  `WokenStop` 이 `FakeStop` 을 상속만 하고 계약을 안 어기는지, 새 두 테스트가
  제품의 실제 갈래를 재는지(가짜끼리만 맞물리는 것이 아닌지)를 본다.
- 그다음: e2e phase. `digest.md` `[5]`(91만 회 공회전)이 스텝 1 의 `:179` 변경으로
  저절로 사라졌는지 확인만 하고 결과를 적는다.

## 한도 (넘으면 RED)

- 도메인당 요청 간격 1초 이상 · robots.txt `Crawl-delay` 준수. **중단 중에도 그렇다.**
- `data/crawl.db` 실물·스키마를 안 건드린다. e2e·탐침은 임시 디렉터리에서만.
- 외부 네트워크 금지 — 로컬 테스트 서버만.
- `docs/specs/` 는 사용자 소유(읽기만) · `--no-verify` 금지 · `main` 직접 커밋 금지.
