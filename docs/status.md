---
signal: GREEN
plan: deadline
mode: night
phase: 테스트
step: 1/4
attempt: 0
iteration: 125
night_iterations: 8
night_red: 0
night_retries: 0
updated: 2026-08-28 00:12 (반복 125 · 020 개발 1/4)
ctx: 40% / 200k
stopped: null
rules: 1411a37
---

# 현재 상태

**계획 020 `deadline` — 개발 1/4 끝. 테스트 스텝 차례다.**
브랜치 `loop/deadline` (기점 `aeb2eeb`). 계획서 `docs/plan_deadline.md` ·
설계 `docs/design_deadline.md`.

`crawl(..., deadline=None)` 이 들어갔다. **테스트 5개를 먼저 쓰고 실패를 봤다**
(TypeError 4건 + rc `0 != 2` 1건). 단위 **393건 OK** (기준선 388 + 5).

- 보는 자리는 **둘**이다: `while` 상단 소진 검사 · 대기 잠을 남은 예산으로 자르기
- **설계 4절이 든 셋째 자리(제출 루프)는 안 넣었다** — 바로 위 `while` 상단
  검사와 마이크로초 차이라 어떤 테스트로도 못 죽인다. 죽일 수 없는 줄은 안 쓴다
- CLI 는 `"--deadline" in args` 로 **있었는지를 따로** 본다 — 이 플래그는
  없는 것이 정상값(`None`)이라 `_number_flag` 의 오류값과 겹친다
- 간격은 안 깎는다. 자르는 것은 **잠**뿐이다

## 다음 행동

**스텝 2/4 테스트** — 변이로 새 테스트 5개가 무엇을 고정하는지 잰다.

1. **변이 없는 기준선을 먼저 세운다** — 393건 OK 를 눈으로 확인하고 그 수를 적는다
2. 변이는 **"이 줄을 안 썼다면 무엇이 되는가"** 로 고른다 (digest `[7]`).
   최소 넷: ① `deadline=None` 인자 자체를 지운다 ② `while` 상단 소진 검사를 지운다
   ③ `min(wait, left)` 를 `wait` 로 되돌린다 ④ CLI 의 `given` 검사를 지운다
3. **죽는 테스트 집합이 서로 달라야 한다.** 같으면 그 테스트들은 한 개다
4. `deadline` 은 **기본값이 있는 인자**라 특히 위험하다 — ① 이
   `test_no_deadline_fills_max_pages`(대조군) 때문에 통과하면 아무것도 못 고정한 것이다

건드릴 파일: 없다(변이는 되돌린다). 결과만 `docs/history_current.md` 에 남긴다.

- 검증: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover tests`
- **`PYTHONDONTWRITEBYTECODE=1` 을 뺴먹지 않는다** — 같은 길이의 변이는 `.pyc` 가 안 바뀐다

## 설계

`docs/design_deadline.md` — **③ 메인 스레드만 예산을 본다**.
버린 둘: ① `timeout(1)`(상한 정확도는 이겼지만 함수엔 못 걸고 stock macOS 에 없다) ·
② `threading.Event`(테스트 9곳의 가짜 시계 이음매를 부순다. **두 갈래 도피는 거부**).

**이 설계가 안 닫는 것**: SIGINT 최악 대기 5.56초 · 예산 초과분 최악 90초 ·
`fetcher` 재시도 구조. **digest 의 Ctrl-C 항목은 지우지 않는다.**

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘).
