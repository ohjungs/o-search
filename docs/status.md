---
signal: GREEN
plan: deadline
mode: night
phase: 설계
step: 0/4
attempt: 0
iteration: 123
night_iterations: 6
night_red: 0
night_retries: 0
updated: 2026-08-27 23:55 (반복 123 · 020 계획)
ctx: 41% / 200k
rules: 1411a37
---

# 현재 상태

**계획 020 `deadline` 착수.** 브랜치 `loop/deadline` (기점 `aeb2eeb`).
계획서는 `docs/plan_deadline.md`.

크롤에 **총 시간 예산**이 없다. `MAX_DELAY = 30` 이 막는 것은 요청 하나당 대기뿐이라
페이지 수만큼 곱해진다 — digest `[4]` 가 "무인 크롤이 밤을 통째로 쓴다" 로 남긴 것.

**착수 전 실측 (`aeb2eeb`, 로컬 실서버).**
1. 한 도메인 `Crawl-delay: 2` · 5페이지 → 총 **8.05초**, 간격 2.01 · 2.01 · 2.01 · 2.00.
   `crawl()` 시그니처와 CLI 플래그(`--max`·`--workers`) 어디에도 시간 인자가 **0개**다.
   `--max 100` + `Crawl-delay: 30` 이면 99 × 30 = **2970초(약 50분)**.
2. 같은 뿌리의 둘째 증상 — SIGINT 를 **0.51초**에 보냈는데 종료는 **6.07초**
   (대기 **5.56초**). `before_send` 가 재시도 앞에서 3초씩 두 번 자고
   `with ThreadPoolExecutor` 가 그것을 기다린다. 상한 30 이면 같은 자리가 60초다.

## 다음 행동

**설계** — `rules/design.md` 로 `docs/design_deadline.md` 를 쓴다.
트리거 둘에 걸렸다: ① 공개 인터페이스 변경(`crawl()` 시그니처 + CLI 플래그)
② 대안이 갈린다.

**설계가 정할 것은 하나다.** A(메인 스레드만 예산을 본다)는 `time.sleep` 이음매를
안 건드리지만 위 실측 2(Ctrl-C 5.56초)를 **못 닫는다**. B(`threading.Event` 를
워커까지)는 둘 다 닫지만 `time.sleep` 을 `Event.wait` 로 바꿔야 하고,
`tests/test_crawl.py` 가 **9곳**에서 `mock.patch("websearch.crawl.time.sleep")` 으로
가짜 시계를 흘려보낸다 — 그 이음매가 사라지면 간격을 재는 테스트가 통째로 죽는다.
**깨진 테스트를 지우는 답은 없다.** 옮길 축이 있으면 B, 없으면 A 로 가고
그때는 문제 2 를 `digest.md` 에 닫지 않은 채로 남긴다.

## 설계

`docs/design_deadline.md` — **아직 없다.** 이번 phase 의 산출물이다.

## 정지 사유

없음.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘).
