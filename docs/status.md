---
signal: DONE
phase: 개발
step: 1
attempt: 0
iteration: 181
updated: 2026-08-31
ctx: 55
night_iterations: 54
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 36 `signal-budget-cover` DONE**(짧은 경로 — 계획서·설계·e2e 문서 없음).
브랜치 `loop/signal-budget-cover`(`loop/deadline-stop` `346884a` 에서 팠다) —
**`main` 병합은 사람이 정한다.** 계획 35 까지 전부 DONE·아카이브 완료. **열린 계획 0.**

## 이번 계획이 한 일

**예산 만료와 SIGINT 가 겹치는 자리를 못박았다.** 계획 35 가 rc 를 `signaled` 로 갈라
예산만 rc 0 · 신호만 rc 130 은 각각 단언이 있었는데 **둘이 겹치는 자리는 0건**이었다.
`tests/test_crawl.py` `TestCliTurnsSigintIntoTheSignal` 에 겹침 단언 한 건을 더했다
(`test_a_signal_wins_over_an_expired_budget_in_either_order` · 두 순서를 `subTest` 로).

**`src/` diff 0줄** — 코드는 옳았고 없던 것은 그것이 옳다는 증거뿐이다. 31
`port-zero-cover` 와 같은 모양이다.

## 완료 기준 대조 (2026-08-31)

- ① 단위 451 → **452건 OK**(3.425초, 문서에 적힌 명령 그대로).
- ② **변이 2종이 새 단언만 죽인다** — `.git` 없는 스크래치패드 사본에서 심었다.
  - M1 `signaled.set()` 을 `if not stop.is_set():` 로 감싸기 → **`[만료 먼저]` 한 갈래만
    FAIL**, 나머지 451건 통과. **순서를 하나만 쟀으면 이 변이가 살아남는다.**
  - M2 만료 갈래에 이른 `return 0` → **두 갈래 다 FAIL**, 나머지 451건 통과.
  - 둘 다 심기 전에 `count(old) == 1` 로 원문 존재를 먼저 단언했다(`digest [8]`).
- ③ `src/` diff **0줄**(`git diff --stat` — `tests/test_crawl.py` +31 · `README.md` ±1).

## 밖에서 다시 잰 것

제품이 0줄이라 e2e 전수는 안 돌리고 **이 계약을 직접 재는 둘만** 돌렸다:
`interrupt_e2e` **rc 0**(SIGINT 뒤 10.0초 rc 130 · 두 번째 Ctrl-C rc -2) ·
`deadline_e2e` **rc 0**(시나리오 3 서버 수신 **1건** · 10.1초 · rc 0 · DB 0행).
`data/crawl.db` **sha256 무변경**(`85c96744…`) — 탐침·e2e 는 임시 디렉터리에서만 돌았다.

## 밀린 집안일

**`digest.md` 가 상한 200 을 넘어 있다**(이번 반복 뒤 222줄). 룰의 처방은 "오래된 완료
항목부터 지운다" 인데 그 항목들을 `index.md` 와 `plan_history_*.md` 가 참조하고 있어
**지우기 전에 참조 확인이 먼저**다 — 이 반복은 그 확인을 안 했고, 새 줄은 완료 1줄과
후보 `[6]` 제자리 수정뿐이다. `history_current.md` 는 이 반복 기록을 더해 **286줄**
(상한 300 — 다음 회전이 가깝다. 밀려나는 대상은 계획 35 의 여섯 반복 → `history_013.md`).

## 한도 (넘으면 RED)

- 도메인당 요청 간격 1초 이상 · robots.txt `Crawl-delay` 준수. **예산 만료 중에도 그렇다.**
- `data/crawl.db` 실물·스키마를 안 건드린다. e2e·탐침은 임시 디렉터리에서만 —
  **서브프로세스는 `cwd` 까지 임시 디렉터리다.**
- 외부 네트워크 금지 — 로컬 테스트 서버만.
- 기존 단언을 낮추지 않는다. 시간 상한을 올려 초록을 만드는 것은 실패다.
- `docs/specs/` 는 사용자 소유(읽기만) · `--no-verify` 금지 · `main` 직접 커밋 금지.
