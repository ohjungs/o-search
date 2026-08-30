---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 180
updated: 2026-08-30
ctx: 52
night_iterations: 53
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 36 `signal-budget-cover` — 짧은 경로**(계획서 없음 · 설계 없음 · e2e 문서 없음).
브랜치 `loop/signal-budget-cover`(`loop/deadline-stop` `346884a` 에서 팠다).
계획 35 까지 전부 DONE·아카이브 완료. **열린 계획 이것 하나.**

## 세 줄

- **근거**: `digest.md ## 다음 계획 후보` `[6]` — "`--deadline` 과 SIGINT 가 함께 올 때
  rc 130 인 것을 아무도 안 잰다". 계획 35 가 rc 를 `signaled` 로 갈랐고(`crawl.py:386`
  `return 130 if signaled.is_set() else 0`), **예산만(rc 0)·신호만(rc 130) 은 각각
  단언이 있는데 겹치는 자리는 0건**이다(`tests/test_crawl.py:1981`
  `test_an_expired_budget_is_not_an_interrupt` · `:1956` `test_the_original_handler_comes_back`).
- **할 일**: `tests/test_crawl.py` 의 `TestCliTurnsSigintIntoTheSignal` 에 겹침 단언
  **한 건**(두 순서를 `subTest` 로). `src` **0줄** — 착수 탐침이 오늘 동작이 옳다고 이미
  쟀다(아래). 31 `port-zero-cover` 와 같은 모양이다: 코드는 옳고 없는 것은 증거뿐이다.
- **완료 기준**: ① 단위 451 → **452건 OK** ② **변이 2종이 새 단언만 죽인다** —
  M1 `signaled.set()` 을 `if not stop.is_set(): signaled.set()` 으로 감싸기 ·
  M2 만료 갈래에 `return 0` 을 먼저 두기. 둘 다 **오늘의 451건은 전부 통과한다**(그것이
  이 단언이 없는 이유다) ③ `src/` diff 0줄.

## 착수 탐침 (2026-08-30, `--deadline 2` · 안 답하는 서버 · `Crawl-delay: 30`)

**계약은 이미 참이다 — 이 계획은 고치는 것이 아니라 못박는 것이다.**

| 갈래 | rc | stderr |
|---|---|---|
| 대조군(신호 없음) | **0** | `예산 2초 소진 — 0페이지에서 멈춘다` |
| SIGINT 를 만료 **전**(요청 수신 직후) | **130** | `중단 — 0페이지에서 멈춘다` |
| SIGINT 를 만료 **후**(수신 +3초, 드레인 중) | **130** | `예산 2초 소진 — 0페이지에서 멈춘다` |

**rc 는 신호만 본다(둘 다 130) · 문구는 먼저 온 쪽을 말한다.** 셋 다 10.1초로,
계획 35 가 낸 소켓 읽기 한 번이다. 이 표가 곧 새 단언의 기대값이다.

**탐침이 실물 DB 경로를 지나갔다** — `crawl.main` 은 db 인자를 안 받고
`crawl(db_path="data/crawl.db")` 가 **cwd 기준**이라, 서브프로세스 탐침은
`cwd=<임시 디렉터리>` 로 돌려야 한다(`e2e/interrupt_e2e.py:129` 가 이미 그렇게 적어 뒀다).
탐침은 `cwd=저장소` 로 돌았다. **실물은 무변경 확인**: `data/crawl.db` 크기·mtime 그대로
(12288B · 08-29 17:04) · `-wal` **0바이트**(수집 0페이지라 커밋이 없다) · `git status` 비었다.

## 이번 탐색이 고르지 않은 것

- `[5]` `_fetch_one` 위치 인자 6개 무단언 — **e2e 시나리오 3 이 밖에서 이미 덮는다**(서버 수신 1건).
- `[4]` `deadline=None` 의 `futures.wait(timeout=None)` 무측정 — 가드를 지우면 `TypeError` 즉사.
- `[4]` 중단 e2e 시간 여유 — 값이 곧 계약이라 올리면 목표가 흐려진다(digest 가 이미 답을 적었다).
- `[7]` `robots.allowed()`·`delay()` 비ASCII 예외 — **도달 불가**(URL 이 태어나는 자리에서 ASCII 가 된다).
  같이 열면 싸다던 짝(`_fetch_robots` 무상한 `read()`)은 22 가 닫아 그 이유도 없어졌다.
- `[7]` bm25 동점·OFFSET 드리프트 — 키셋 페이지네이션은 **공개 응답 계약 변경**이라 승인 항목.
- 3순위(사양 미구현)는 `recrawl` 하나뿐이고 스키마 변경이라 루프가 못 연다.

출처 1~4 는 실측 0건이다: 단위 **451건 OK**(3.586초) · 린터·타입체커 없음(`docs/project.md`) ·
코드 `TODO`/`FIXME`/`HACK` **0**(`ponytail:` 7건은 전부 천장 주석) · `docs/candidates.md` 없음 ·
`docs/patches/` 없음 · 활성 계획 0.

## 밀린 집안일

**`digest.md` 가 220줄로 상한 200 을 넘었다** (계획 35 e2e phase 가 넘긴 것 그대로).
룰의 처방은 "오래된 완료 항목부터 지운다" 인데 그 항목들을 `index.md` 와
`plan_history_*.md` 가 참조하고 있어 **지우기 전에 참조를 먼저 확인해야 한다**.
이 반복은 새 줄을 **하나도 안 늘렸다**(고른 후보 `[6]` 한 줄을 제자리에서 고쳤을 뿐이다).
`history_current.md` 는 이 반복 기록을 더해 **265줄**이다(상한 300 — 다음 회전이 가깝다).

## 한도 (넘으면 RED)

- 도메인당 요청 간격 1초 이상 · robots.txt `Crawl-delay` 준수. **예산 만료 중에도 그렇다.**
- `data/crawl.db` 실물·스키마를 안 건드린다. e2e·탐침은 임시 디렉터리에서만 —
  **서브프로세스는 `cwd` 까지 임시 디렉터리다**(위 탐침이 밟은 자리).
- 외부 네트워크 금지 — 로컬 테스트 서버만.
- 기존 단언을 낮추지 않는다. 시간 상한을 올려 초록을 만드는 것은 실패다.
- `docs/specs/` 는 사용자 소유(읽기만) · `--no-verify` 금지 · `main` 직접 커밋 금지.
