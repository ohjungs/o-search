---
signal: GREEN
plan: deadline
phase: e2e
step: 4/4
attempt: 0
iteration: 127
night_iterations: 10
night_red: 0
night_retries: 0
updated: 2026-08-29 10:45 (반복 127 · 020 리뷰 3/4)
ctx: 30% / 200k
stopped: null
rules: 1411a37
mode: night
---

# 현재 상태

**계획 020 `deadline` — 리뷰 끝. e2e 차례다.**
브랜치 `loop/deadline` (기점 `aeb2eeb`). 계획서 `docs/plan_deadline.md` ·
설계 `docs/design_deadline.md`. 단위 **393건 OK**.

**34시간 공백이 있었다** — 마지막 커밋이 08-28 00:23(테스트 2/4)이고 이 세션이
08-29 10:20 에 이어받았다. 작업 트리는 깨끗했고 잃은 것은 없다. 두 세션이 같은
자리(리뷰 3/4)에서 끊긴 뒤 세 번째에 통과했다.

## 리뷰 3/4 에서 나온 것

**백지 패스를 지켰다** — 리뷰 세션에 `docs/` 와 `git log` 를 막고 코드만 줬다.
(지난 status 는 "위 1~3 을 그대로 준다" 고 했지만 `rules/review.md` 0절이
배경 제공을 금지한다. 룰을 따랐고, 1~3 은 패스 B 에서 내가 대조했다.)

4건이 나왔다. **자동 2건은 적용했고, 승인 2건은 패치로 남겼다.**

**적용:**
- usage 가 `--deadline SECONDS` 인데 파서가 `int()` 다 → `--deadline N` 으로 맞췄다
- `test_deadline_flag_errors...` 가 가드 회귀 시 **실네트워크로 나간다** →
  `mock.patch("websearch.crawl.crawl")` 로 감싸고 `assert_not_called()` 를 걸었다.
  형제 테스트 `test_max_flag_errors...`(:96)도 같은 성질이지만 이번 diff 밖이라 안 건드렸다

**보류 → `docs/patches/`** (둘 다 `git apply --check` 통과):
1. `deadline-inflight-reap.patch` **(critical)** — 예산 만료 `break` 가 **떠 있는
   요청의 결과를 통째로 버린다.** executor 는 `with` 를 나갈 때 그것들을 어차피
   기다리므로 **시간은 치르고 결과만 버리는** 셈이고, 다음 실행에서 같은 URL 을
   다시 때린다(크롤 윤리로도 손해). workers=8 이면 최대 7건.
   승인 필요인 이유: 설계 4절이 "떠 있는 요청은 그대로 끝까지 간다" 고만 적어
   결과를 줍는지 버리는지를 **정하지 않았다**. 어느 쪽이든 `crawl.py:82` 문구를 고쳐야 한다.
2. `deadline-eq-form.patch` — `--deadline=5` 형태가 **조용히 무시되고 rc 0** 이다.
   사용자가 건 안전 예산이 사라지는데 성공으로 끝난다. 근본 원인은 `_number_flag` 가
   `--name=값` 을 모르는 것이고 `--max`·`--workers` 도 같다 — 셋 다 고칠지가 설계 결정이라
   패치는 `--deadline` 만 막는다.

## e2e 4/4 가 반드시 덮을 것

**M6 을 이 세션에서 직접 재현했다** (사본에 변이, `data/` 의존 `test_quality_*` 3건은
사본 탓의 무관한 오류). CLI 배선을 끊어도 **단위는 안 죽는다** — e2e 몫이 확정됐다.

1. **CLI 배선** — `--deadline` 값이 `crawl()` 까지 가는가 (M6)
2. **실시계에서만 나오는 자리** — 리뷰 중에 안 것: 가짜 시계는 `sleep` 에서만 흐르고
   `sleep` 은 `inflight` 가 빌 때만 한다. 그래서 **"떠 있는 요청을 둔 채 예산 만료"**
   상태에 단위 테스트는 **구조적으로 도달할 수 없다.** 패치 1이 고치는 자리가 정확히
   거기다 — e2e 가 아니면 아무도 못 본다

**e2e 를 몇 분씩 걸리게 만들지 않는다.** 도메인당 1초·선언된 `Crawl-delay`·robots 는
그대로다 — 끝을 당기려고 간격을 깎지 않는다. 기존 `e2e/crawl_delay_e2e.py` 와
`docs/e2e/crawl-delay/` 가 본보기다.

## 설계

`docs/design_deadline.md` — **③ 메인 스레드만 예산을 본다**.
버린 둘: ① `timeout(1)`(상한 정확도는 이겼지만 함수엔 못 걸고 stock macOS 에 없다) ·
② `threading.Event`(테스트 9곳의 가짜 시계 이음매를 부순다. **두 갈래 도피는 거부**).

**이 설계가 안 닫는 것**: SIGINT 최악 대기 5.56초 · 예산 초과분 최악 90초 ·
`fetcher` 재시도 구조. **digest 의 Ctrl-C 항목은 지우지 않는다.**

## 밀린 집안일

`docs/history_current.md` 가 **600줄이 넘는다**(상한 300 / 20회, 항목은 15개).
줄 수로 회전이 밀렸다 — 오래된 것부터 `history_006.md` 로 밀어내고 `digest.md` 에
1~2줄로 압축한다. **스텝이 아니라 밤 마무리 때 한다**(직교 편집).

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` ·
`fetcher` 재시도 구조 변경(digest `[high]` — 옳지만 크다) · `loop/*` 병합 ·
옛 열쇠 행 통합과 URL userinfo(승인 대기 `[high]` 둘) ·
기존 `data/crawl.db` 재키잉/마이그레이션.
