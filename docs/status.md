---
signal: GREEN
plan: deadline
mode: night
phase: 리뷰
step: 2/4
attempt: 0
iteration: 126
night_iterations: 9
night_red: 0
night_retries: 0
updated: 2026-08-28 00:28 (반복 126 · 020 테스트 2/4)
ctx: 52% / 200k
stopped: null
rules: 1411a37
---

# 현재 상태

**계획 020 `deadline` — 개발·테스트 끝. 리뷰 차례다.**
브랜치 `loop/deadline` (기점 `aeb2eeb`). 계획서 `docs/plan_deadline.md` ·
설계 `docs/design_deadline.md`. 단위 **393건 OK** (기준선 388 + 5).

`crawl(..., deadline=None)` — 메인 스레드만 예산을 본다. 보는 자리는 **둘**이다
(`while` 상단 소진 검사 · 대기 잠을 남은 예산으로 자르기).
**설계 4절의 셋째 자리(제출 루프)는 안 넣었다** — 못 죽이는 줄은 안 쓴다.
CLI 는 `"--deadline" in args` 로 있었는지를 따로 본다(없는 것이 정상값이라
`_number_flag` 의 오류값과 겹친다).

**변이 7건을 돌렸다** (기준선 393 OK 먼저 확인). 표는
`docs/history_current.md` 의 `테스트 2/4` 항목에 있다. 남은 것 셋:

1. **M6 이 살아남았다** — CLI 배선(`--deadline` 값이 `crawl()` 까지 가는가)을
   단위 테스트가 안 덮는다. **스텝 4/4 e2e 가 반드시 덮어야 한다.**
2. **M2 는 매달렸다**(무한 루프) — 소진 검사와 잠 자르기가 서로를 붙들고 있다.
   도달 불가라 `max(0, ...)` 가드는 안 넣었다.
3. **테스트 1번과 3번의 죽는 집합이 같다** {M1, M4, M7}. 합치지 않은 이유를
   기록에 적었다 — 3번은 **덧붙일 줄**을 잡는 대조군이다.

## 다음 행동

**스텝 3/4 리뷰** — `rules/review.md`. **백지 세션에서 한다**:
`docs/` 와 `git log` 를 보지 않고 코드만 읽는다. 읽을 것은
`src/websearch/crawl.py` 의 `crawl()`·`main()` 과 `tests/test_crawl.py` 의
`TestDeadline` **둘뿐**이다.

- 리뷰가 먼저 볼 자리로 위 1~3 을 그대로 준다(숨기지 않는다)
- 80점 임계는 `metrics.md` 에 반례가 쌓여 있다 — 점수 밑이어도 몇 줄이면 고친다
- 검증: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover tests`

## 설계

`docs/design_deadline.md` — **③ 메인 스레드만 예산을 본다**.
버린 둘: ① `timeout(1)`(상한 정확도는 이겼지만 함수엔 못 걸고 stock macOS 에 없다) ·
② `threading.Event`(테스트 9곳의 가짜 시계 이음매를 부순다. **두 갈래 도피는 거부**).

**이 설계가 안 닫는 것**: SIGINT 최악 대기 5.56초 · 예산 초과분 최악 90초 ·
`fetcher` 재시도 구조. **digest 의 Ctrl-C 항목은 지우지 않는다.**

## 밀린 집안일

`docs/history_current.md` 가 **596줄**이다(상한 300 / 20회, 항목은 14개).
줄 수로 회전이 밀렸다 — 오래된 것부터 `history_006.md` 로 밀어내고 `digest.md` 에
1~2줄로 압축한다. **스텝이 아니라 밤 마무리 때 한다**(직교 편집).

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘).
