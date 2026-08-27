---
signal: GREEN
plan: deadline
mode: night
phase: 개발
step: 0/4
attempt: 0
iteration: 124
night_iterations: 7
night_red: 0
night_retries: 0
updated: 2026-08-28 00:05 (반복 124 · 020 설계)
ctx: 80% / 200k
stopped: 컨텍스트 여유 부족 — 개발 스텝 한 벌(테스트 먼저 + 388건 회귀)을 못 돈다. RED 아님
rules: 1411a37
---

# 현재 상태

**계획 020 `deadline` — 계획·설계 끝. 개발 착수 전이다.**
브랜치 `loop/deadline` (기점 `aeb2eeb`). 계획서 `docs/plan_deadline.md` ·
설계 `docs/design_deadline.md`.

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

**스텝 1/4 개발** — `rules/dev.md` **0절대로 실패하는 테스트를 먼저 쓴다.**
쓸 테스트 5개가 `docs/design_deadline.md` 7절에 그대로 있다.
건드릴 파일은 `src/websearch/crawl.py` · `tests/test_crawl.py` **둘뿐**이다.

- **아직 아무 코드도 안 건드렸다.** `git diff aeb2eeb --stat` 은 `docs/` 만 낸다
- 검증: `PYTHONPATH=src python3 -m unittest discover tests` (착수 전 기준선 **388건 OK**)

## 설계

`docs/design_deadline.md` — **③ 메인 스레드만 예산을 본다** 를 골랐다.
`crawl(..., deadline=None)`, 주입된 `now()` 로 재고, 보는 자리는 셋뿐이다
(`while` 상단 · 제출 루프 · `time.sleep(seconds_until_ready())` 를 남은 예산으로 자르기).
CLI 는 `_number_flag(args, "--deadline", None)` 로 있는 헬퍼를 그대로 쓴다.

**버린 둘과 이유.**
- ① `timeout(1)` 로 감싸기 — 상한 정확도는 **이쪽이 이긴다**(SIGTERM 실측 대기 **0.00초**).
  그래도 버렸다: 함수에는 상한이 안 걸리고(`crawl()` 직접 호출이 e2e 14종 전부),
  stock macOS 에 없으며(`/opt/homebrew/bin/timeout`), rc 0 과 `수집 N 페이지` 가 안 나온다
- ② `threading.Event` 를 워커까지 — 예산 초과분 ≈0 에 **SIGINT 5.56초까지 닫는다**.
  그래도 미뤘다: `tests/test_crawl.py` 가 **9곳**에서
  `mock.patch("websearch.crawl.time.sleep")` 로 가짜 시계를 흘려보내는데
  `Event.wait` 가 그 이음매를 없앤다. **"stop 이 None 이면 time.sleep" 두 갈래는
  명시적으로 거부했다** — 테스트가 도는 경로와 제품이 도는 경로가 갈린다(digest `[6]`)

**이 설계가 안 닫는 것**(설계 5절에 그대로 있다): SIGINT 최악 대기 · 예산 초과분 최악 90초 ·
`fetcher` 재시도 구조. **digest 의 Ctrl-C 항목은 지우지 않는다.**

## 정지 사유

컨텍스트 여유 부족. 스텝 경계(설계 끝)에서 정상 종료했다. RED 아님 · 재시도 0.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘).
