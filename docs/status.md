---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 159
updated: 2026-08-30
ctx: 33
night_iterations: 39
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 33 `clock-injection` 개발 스텝 5 완료 — 변이 3종이 전부 죽었다. 개발 phase 끝.**
단위 **433건 전부 OK** (3.14초). 열린 계획 **1** · 보류 패치 0 · RED 0.
작업 트리 깨끗. 스텝 4 는 `1c3fc85` 로 커밋됐다.

## 스텝 5 — 변이 검사 정식 판정 (3종 전부 죽음)

스크래치패드 사본에서 쟀다. 같은 사본의 기준선이 **433건 OK** 임을 먼저 확인했다.

| 변이 | rc | 실패 |
|---|---|---|
| M1 — `before_send` 의 대기 블록(`:71~74`) 통째 삭제 | **1** | 9건 |
| M2 — `:179` 를 전역 `time.sleep` 으로 되돌리기 | **124** (90초 타임아웃) | 행 |
| M3 — `crawl.py:61` 의 `max` → `min` | **1** | 11건 |

**M2 가 이 계획의 판정이다.** 스텝 3 에서는 rc=0 으로 살아남았다 — 몽키패치 10곳이
그 전역을 잡아 주고 있었기 때문이다. 그것이 사라지자 가짜 시계가 안 흐르고 메인
루프가 무한히 잔다. 계획서가 "여기서 안 죽으면 테스트가 여전히 전역에 붙어 있는
것" 이라고 적어 둔 판정이 **이제 통과한다.**

M1·M3 는 공통으로 `TestRetriesKeepTheInterval`·`TestRetryUsesWhatTheFrontierKnows`·
`TestSleepIsInjected` 를 죽인다. M1 은 `sleep(remaining)` **한 줄이 아니라 `if sends:`
블록 4줄**을 지웠다 — 한 줄만 지우면 빈 `if` 라 문법 오류이고, `digest.md:154` `[7]` 의
**"이 줄을 안 썼다면 무엇이 되는가"** 기준에 맞춘 되돌리기가 블록 삭제다.

**사고는 재발하지 않았다.** 사본(`scratchpad/mut/`, `.git` 없음)에서만 변이시켰고
작업 트리는 내내 깨끗했다. 각 실행에 `timeout 90` 과 `PYTHONDONTWRITEBYTECODE=1` 을
걸었다 — M2 가 rc=124 로 끝난 것이 그 타임아웃이다.

## 스텝 4 (앞 반복, `1c3fc85`)

`grep -c 'crawl\.time\.sleep' tests/test_crawl.py` → **0** (스텝 3 에서 11).
`mock.patch("websearch.crawl.time.sleep") as ms` 10줄을 지우고, 뒤따르던
`ms.side_effect = lambda s: ...` 를 `ms = mock.Mock(side_effect=lambda s: ...)` 로
바꿨다. 10곳이 한 글자도 안 다른 같은 모양이라 스크립트로 한 번에 돌렸다.
스텝 2·3 이 임시 발판으로 붙여 둔 `sleep=ms` 가 이미 전부 자리에 있어서
**그 외에는 붙일 것이 없었다.** `src` diff **0줄**, `tests` diff **+16/-26**.

`ms` 를 평범한 함수가 아니라 `mock.Mock` 으로 둔 이유는 `TestDeadline._elapsed` 가
`ms.call_args_list` 로 흘러간 시간을 재기 때문이다(`test_crawl.py:1237`).

**기대값·시나리오는 한 글자도 안 고쳤다** — diff 에서 치환 4종과 독스트링 한 문단을
빼면 남는 줄이 없다(grep 으로 확인). 실행 시간이 3초대 그대로라는 것 자체가
**진짜 `time.sleep` 이 안 불렸다**는 증거다.

`src/websearch/crawl.py` 는 스텝 3 이후 그대로다 — `time.sleep` **호출은 0곳**,
시그니처 기본값 2곳만 남고 두 대기 자리가 **같은 하나**를 쓴다:

```python
def _fetch_one(url, robots, now, floor, sleep=time.sleep):   # crawl.py:33
    ...  sleep(remaining)                                     # crawl.py:74  워커
def crawl(..., deadline=None, sleep=time.sleep):              # crawl.py:88
    pool.submit(_fetch_one, ..., frontier.interval(domain), sleep)           # :170
    ...  sleep(wait if left is None else min(wait, left))     # crawl.py:179 메인 ← 이번
```

스텝 3 의 `src` diff 는 **1줄**. 계약 6개 전부 지켰다: 인자는 맨 뒤 · 두 대기 자리가
같은 하나 · 규약은 `time.sleep` 과 동일 · `DOMAIN_INTERVAL` 하한 무변경 ·
**간격 기대값(`[1.0]`·`[5.0]`·`[1.0, 1.0]`) 한 글자도 안 고쳤다.**

**스텝 2 가 미룬 e2e 를 여기서 갚았다.** 겉보기 동작이 안 바뀌는 계획이라 e2e 가
유일한 실제 증거인데 스텝 2 는 안 돌리고 넘어갔다. 17종 전부 rc=0 —
직접 표적인 `crawl_delay_e2e`·`perf_crawl`·`deadline_e2e` 포함.

브랜치 `loop/clock-injection`, 기점 **`de28dfb`**(`loop/readme-perf-audit`).
`main` 은 `f888518` 그대로 — 건드리지 않았다.

## 같은 함정을 스텝 3 에서 다시 밟았다 — 이번엔 빨강이 아니라 **행**

아래 스텝 2 의 실측(기본 인자는 `def` 시점에 박혀 `mock.patch` 가 못 닿는다)이
`crawl.py:179` 에도 똑같이 적용된다. 다른 점은 **증상**이다. 워커 쪽은 간격이
`[0.0, 0.0]` 으로 찍혀 **빨개졌지만**, 메인 루프는 가짜 시계가 안 흐르면
`frontier.seconds_until_ready()` 가 영원히 1.0 이라 **무한 루프**가 된다 —
첫 테스트에서 120초 타임아웃으로 끊었다. **타임아웃이 없으면 야간 루프가
여기서 멈춰 섰을 자리다.**

닫는 법은 스텝 2 와 같다: 남은 `crawl.crawl()` 호출 **7곳에 `sleep=ms`** 를 넘긴다.
`tests` diff 는 전부 그 한 인자 추가고, 기대값·시나리오는 안 건드렸다.
`mock.patch` 줄 10곳은 스텝 4 의 일이라 그대로 뒀다.

## M2 가 이번엔 죽는다 — 계획이 노린 전환이 실제로 일어났다

| 변이 | 스텝 3 (몽키패치 10곳 남음) | 스텝 4 (걷어낸 뒤) |
|---|---|---|
| M1 — 메인 쪽 대기를 통째로 삭제 | **죽는다** (rc=124) | 스텝 5 에서 정식 판정 |
| M2 — `:179` 를 전역 `time.sleep` 으로 되돌리기 | **안 죽는다** (rc=0) | **죽는다** (rc=124) |

이때의 M1 은 **메인 쪽**을 지운 예비 측정이었다. 계획서가 정한 M1 은 **워커 쪽**(`:74`)이고,
스텝 5 는 계획서대로 워커 쪽을 지워 다시 쟀다(rc=1, 9건).

전역을 잡아 주던 몽키패치가 사라지자 가짜 시계가 안 흐르고 메인 루프가 무한히 잔다.
계획서가 "여기서 안 죽으면 테스트가 여전히 전역에 붙어 있는 것" 이라고 적어 둔 그
판정이 **이제 통과한다.** 정식 3종 판정(M1·M2·M3)은 스텝 5 다.

### 사고 — 변이를 작업 트리에서 재지 마라

M2 를 제자리에서 쟀더니 10분 행이 걸렸고, 그 사이 **자동 스냅샷 훅이 변이된
`crawl.py` 를 커밋해 origin 에 푸시했다**(`0aac7b0` "자동 스냅샷 21:19").
`git checkout -- src` 가 그 스냅샷을 복원해 변이가 되살아났다 —
`git checkout 4e7feb0 -- src/websearch/crawl.py` 로 되돌렸고, 이번 커밋이 그 되돌림을
포함한다. 재측정은 `src`·`tests` 를 스크래치패드에 복사해 90초 타임아웃을 걸고 했다.
**스텝 5 는 처음부터 사본에서 돈다.**

## 계획의 가정 하나가 거짓이었다 (스텝 2에서 실측)

계획서 스텝 2 는 "몽키패치 10곳은 그대로지만 **전역 패치가 기본값도 잡으므로** 초록"
이라고 적어 뒀다. **거짓이다.** 기본 인자는 `def` 실행 시점에 한 번 평가돼
`_fetch_one.__defaults__` 에 **진짜 `time.sleep` 객체가 박힌다**. `mock.patch` 는
`time` 모듈의 **속성**을 갈아끼울 뿐이라 이미 박힌 기본값에는 닿지 않는다. 실측:

```
_fetch_one.__defaults__ : (<built-in function sleep>,)
패치 중 time.sleep      : <MagicMock ...>
기본값은 여전히 진짜인가 : True
```

그래서 첫 실행에서 **8건이 빨개졌다**(`TestRetriesKeepTheInterval` 3 ·
`TestRetryUsesWhatTheFrontierKnows` 5). 가짜 시계가 안 흘러 간격이 `[0.0, 0.0]` 으로
찍혔고, 진짜로 자느라 전체가 129초 걸렸다 — **주입이 실제로 동작한다는 반증**이기도 하다.

**최소 수정으로 닫았다**: 그 3개 호출 지점에 `sleep=ms` 를 넘긴다(이미 만들어 둔 가짜
시계 목 그대로). 기대값도 시나리오도 안 건드렸다. `mock.patch` 는 아직 남겨 뒀다 —
메인 쪽(`crawl.py:179`)이 아직 전역을 쓰므로 스텝 3 전에는 필요하다.

**기록해 둘 것**: `tests/test_crawl.py` 는 스텝 2 의 "건드릴 파일"(= `src` 만) **밖**이다.
다만 **계획 밖 파일은 아니다** — 스텝 4 의 건드릴 파일이 바로 그 파일이라 정지 조건
"계획에 없는 파일 수정" 에는 걸리지 않는다.
스텝 4(몽키패치 치환)의 일부를 3줄 선취한 셈이고, 대안이 없었다 — 기본값을 늦게 묶는
(`sleep=None` 센티널) 우회는 **스텝 1 이 이미 고정한 `test_default_sleep_is_the_real_one`
을 깬다.** 스텝 4 의 남은 일은 그만큼 줄었다.

## 다음에 할 일 — 테스트 phase (계획 33 의 마지막 스텝을 지났다)

개발 5스텝이 전부 끝났다. `test.md` 1절 표에 따라 **마지막 스텝이므로 전체를 돌린다**
(이미 433건 OK 를 받았다) — 테스트 phase 에서 볼 것은 나머지 둘이다:

- **빠뜨린 것**(`test.md` 3절) — 이 계획이 만든 새 public 표면은 `crawl(sleep=)` 과
  `_fetch_one(..., sleep=)` 둘뿐이고 `TestSleepIsInjected` 2건이 덮는다.
  기본값이 진짜 `time.sleep` 이라는 것까지 고정돼 있다(`test_default_sleep_is_the_real_one`).
- **단언을 낮추지 않았는지**(`test.md` 6절) — 이 계획의 핵심 위험이다.
  간격 기대값(`[1.0]`·`[5.0]`·`[1.0, 1.0]`)이 한 글자도 안 바뀌었는지 diff 로 확인한다.
  변이 3종이 전부 죽은 것이 "재는 척" 이 아니라는 1차 증거다.

그다음이 리뷰 → e2e 다. **e2e 가 이 계획의 진짜 관문이다** — 가짜 시계가 초록인데
진짜 대기가 사라지는 것이 유일한 실제 위험이고, `crawl_delay_e2e`·`perf_crawl`·
`deadline_e2e` 만 그것을 볼 수 있다(계획서 e2e 절). 스텝 3 에서 17종 전수 rc=0 을
받아 뒀지만 `src` diff 0줄이라 그 값이 아직 유효하다 — e2e phase 에서 다시 확인한다.

## 계획 33 요약 (상세는 `docs/plan_clock-injection.md`)

- **문제**: 시각 읽기는 **인자**(`now`), 잠들기는 **모듈 전역**(`time.sleep`)이다.
  그 비대칭 때문에 `tests/test_crawl.py` 가 `websearch.crawl.time.sleep` 을
  **10곳**에서 몽키패치한다. 이 저장소가 크롤 간격을 초 단위로 단언하는 근거가 전부 거기다.
- **막고 있는 것**: 워커까지 Ctrl-C 를 넣으려면 `crawl.py:74` 가 `Event.wait` 가 돼야
  하는데 그러면 10곳이 한꺼번에 눈이 먼다.
- **실측 정정**: digest 는 **9곳**이라고 적어 뒀지만 실제로 **10곳**이다
  (65·622·672·742·787·843·948·1023·1096·1325, 전부 `tests/test_crawl.py`. `e2e/` 는 0곳).
  계획 종료 시 `digest.md:156` 을 고친다.
- **스텝 5개**, 전부 일렬 의존. 완료 기준의 핵심 두 개:
  `grep -c 'crawl\.time\.sleep' tests/test_crawl.py` = **0** ·
  **기존 간격 기대값을 하나도 안 고친다.**
- **e2e 는 "달라진 게 없다" 를 증명하는 자리다** — `crawl_delay_e2e.py` ·
  `perf_crawl.py` · `deadline_e2e.py` 만 진짜 대기가 사라졌는지 볼 수 있다.

## 아직 남은 후보 (반복 152 의 분류 — (c) 첫 항목만 빠졌다)

**(a) 사람 승인 대기 — 무인 모드가 손대지 않는다**
`[8]` indexer 증분이 갱신을 반영 안 함(**스키마 변경**) · `[high]` `store.has` 가 상태
불문 스킵 = 재크롤 정책(**사람 판단**) · URL userinfo 가 `pages.url` PK 이자 검색 결과에
렌더됨(**보안 경계**) · `[5]` `X-Robots-Tag` http-equiv(**스키마**) · `loop/*` 병합 여부.

**(b) 도달 불가 — 고치면 오히려 정상값을 거절한다**
`[4]` `int_max_str_digits`(파이썬 3.9.6, 유지 판단 완료) · `[4]` `quality_eval` 의
`limit=100` 절단(실물 최대 28건) · `[4]` `fixture_defects` 가 ko·en 만 셈(코퍼스 동결이라
`ja` 질의가 생길 수 없다). 셋 다 **지금 짜면 죽은 코드**다.

**(c) 정식 계획 크기 — 설계 트리거에 걸린다**
~~`[6]` 가짜 시계 이음매~~ → **계획 33 으로 열었다.** 남은 둘:
`[4]` 간격 시계가 발신이 아니라 pop 시각에서 시작 · `[7]` 요청 사이 색인 변경 시
OFFSET 페이지네이션 드리프트. 둘 다 40줄을 넘고 대안이 갈려 **야간 자동 적용 밖**이다.

## 사람이 정해야 할 것

1. **브랜치 병합** — `loop/readme-perf-audit`(푸시 완료)과 이제 `loop/clock-injection`
   을 `main` 에 남길지. 무인 모드는 `main` 에 커밋하지 않는다.
2. **(a) 의 스키마·보안 건**을 열지 — 열면 무인 금지가 풀린다.

## 미결

`data/crawl.db` 는 URL 을 `pages.url` PK 로 쓴다 · CI 없음 · `docs/specs/` 는 동결이다.
