# 설계: 중단 신호 — 네 자리를 **두 자리로** 줄이고 하나의 객체로 덮는다

- **계획**: `plan_graceful-interrupt.md`
- **트리거**: 공개 인터페이스 변경(`crawl()`·`_fetch_one()` 시그니처) + 대안 3갈래 + 3개 파일
- **작성**: 2026-08-30

## 결정

**`stop` 이벤트 하나를 `now`·`sleep` 옆에 인자로 받는다.** 그 하나가 두 가지 일을 한다 —
**잠에서 깨우고**(`stop.wait`), **발신을 접는다**(`stop.is_set`).

**네 자리 중 둘은 아무것도 안 한다.** 계획서가 "네 자리를 몇 개의 기제로 덮는가" 를 물었고,
답은 **둘**이다. 소켓 읽기(축1)와 `futures.wait`(축4)는 **덮지 않는 것이 옳다**:

| 축 | 자리 | 무엇으로 | 왜 |
|---|---|---|---|
| 1 | 소켓 읽기 `fetcher.py:39` | **아무것도 안 한다** | 재시도를 접으면 3회×10초가 **1회 10초**로 줄고, 10초는 목표 12초 **안**이다. `TIMEOUT` 인하는 느린 서버를 통째로 버리는 별개 판단(계획 6절) |
| 2 | 재시도 잠 `crawl.py:74` | `stop.wait` + `is_set` | **깨우기와 취소는 한 변경이다**(계획 2절 3번). 깨우기만 하면 `Crawl-delay: 30` 서버에 10초 간격 3발 → RED |
| 3 | 메인 루프 잠 `crawl.py:179` | `stop.wait` | 축4와 달리 **깨워 줄 워커가 없다.** 유일하게 `Event.wait` 가 아니면 못 깨는 자리 |
| 4 | `futures.wait` `crawl.py:184` | **아무것도 안 한다** | 축1·2를 덮으면 워커가 10초 안에 끝나고, **그 완료가 `FIRST_COMPLETED` 로 메인을 깨운다**. 아래 탐침 |

## 가정 — 깨봤다 (`design.md` 3-2)

**"축4는 저절로 깬다"** 가 틀리면 이 설계가 무너진다(계획서가 "특히 `futures.wait` 를
어떻게 깨울지" 를 물은 이유). 탐침 `gi_probe3.py`(스크래치패드, 커밋 안 함) 실측:

```
[A] 워커가 stop.wait(20) 에 잠   wait 복귀 0.51s · 핸들러 0.51s · done=1 · 조인 0.51s
[B] 워커가 time.sleep(3) 에 갇힘  wait 복귀 3.01s · 핸들러 0.51s · done=1 · 조인 3.01s
[C] 대조군(신호 없음, timeout 2)  wait 복귀 2.01s · 핸들러 안 불림 · done=0
```

**참이다.** 타임아웃 30초를 준 `futures.wait` 가 [A] 0.51초 · [B] 3.01초에 돌아왔다.
계획 탐침이 잰 "플래그만 세우면 `futures.wait(20)` 이 20.01초 다 잔다" 는 **워커가
계속 도는 경우**였고, 워커를 끝내면 같은 자리가 저절로 깬다. 축4 코드는 **0줄**이다.

**둘째 가정: 최악은 소켓 10초 하나뿐.** `robots.txt` 왕복(`robots.py:149`,
`timeout=10`·재시도 없음)과 페이지 요청은 직렬이지만, 뒤엣것이 계약 4로 취소되므로
**합쳐서 10초를 안 넘는다.** 워커가 여럿이어도 동시에 흐르니 10초 그대로다.

## 대안 비교

세 출발점에서 하나씩 냈다 (`design.md` 3-1).

| | A. `sleep` 자리 흡수 (최소) | **B. `stop` 인자 (정공법)** | C. 모듈 전역 이벤트 (되돌리기 우선) |
|---|---|---|---|
| **무엇** | CLI 가 `sleep=stop.wait` 만 넘긴다. 취소는 없다 | `stop=None` 을 `crawl()`·`_fetch_one()` 에 추가 | `crawl._STOP` 전역. 시그니처 변화 0 |
| **예절(계획 2절 3번)** | ✗ **깨진다** — 10초 간격 3발 | ○ 발신 훅이 접는다 | ○ |
| **12초 목표** | ✗ 워커가 재시도를 계속해 축4가 30초 | ○ **10초 + ε** | ○ |
| **되돌리기** | 쉬움 | **기본값 `None` 이 곧 꺼진 플래그**(`--deadline` 과 같은 형태). 커밋 하나 revert | 커밋 하나 revert |
| **테스트 격리** | ○ | ○ 인자로 준 것만 산다 | ✗ 전역이 새면 **다른 테스트가 조용히 중단된다** |
| **기존과 일치** | ○ | ○ `now`·`sleep`(계획 33)과 같은 모양 | △ 이 코드베이스에 전역 가변 상태가 없다 |

**선택: B** — 기본값 `None` 이 오늘 경로 그대로라 **C 의 되돌리기 이점을 이미 갖고**,
A 가 못 푸는 예절을 같은 객체 하나로 푼다. **버린 이유: A** — "대기 수단만 바꾸면 끝" 은
계획 탐침이 이미 거짓으로 판정한 것이다. **C** — 되돌리기 이점이 B 보다 크지 않은데
전역 상태 비용만 낸다.

## 계약 — 개발이 지킬 것

1. **시그니처.** `crawl(seeds, max_pages, ..., sleep=time.sleep, stop=None)` ·
   `_fetch_one(url, robots, now, floor, sleep=time.sleep, stop=None)`.
   `sleep` 기본값은 `time.sleep` **그대로 둔다**(계획 33 계약 ·
   `test_default_sleep_is_the_real_one` 이 두 함수 모두를 본다).
   `stop` 은 `is_set()`·`wait(t)` 를 가진 것 — `threading.Event`.
2. **대기 수단은 한 줄로 갈린다.** 두 자리 모두
   `wait = sleep if stop is None else stop.wait` 를 쓴다.
   `stop is None` 이면 **주입된 `sleep` 만 불린다** —
   `test_injected_sleep_is_the_only_one_used` 와 가짜 시계 10곳이 안 깨진다.
3. **잠에서 중단으로 깬 것과 시간이 다 된 것을 구별한다.**
   `if remaining > 0 and wait(remaining): <중단 처리>` — `time.sleep` 은 `None`(거짓)을,
   `Event.wait` 는 `True` 를 돌려주므로 **한 표현이 두 경우를 다 덮는다.**
4. **발신 취소 — `stop.is_set()` 를 두 곳에서 본다.** `_fetch_one` 진입 시(그 뒤가
   `robots.txt` 왕복이다) 와 `before_send` 진입 시. **신호 뒤에 새로 여는 소켓은 0개다.**
   `before_send` 는 모듈 사설 예외 `_Interrupted` 를 던지고 `_fetch_one` 이 그것을 잡는다 —
   훅 호출이 `fetch` 의 `try` **밖**이라(`fetcher.py:36-37`) 그대로 나온다.
   **`fetcher.py` 는 0줄이다**(계획 3절 ③을 버린다: `fetcher` 가 간격을 모른다는 계약을
   지킨다).
5. **중단된 시도의 반환 모양: `result is None`.**
   `(True, requested, sends[-1] if sends else None, None)` 을 돌려주고,
   `_store_result` 는 `mark_sent`·`_apply_delay` 를 **지난 뒤** `result is None` 이면
   `0` 을 돌려주고 **upsert 하지 않는다**. (오늘 `result` 가 `None` 인 경우는
   `allowed=False` 뿐이라 충돌하지 않는다.)
   - **예외로 흘리지 않는 이유**(계획 3절 ①): `_store_result` 의 `except` 가지는
     **모르는 실패**용이라 `요청이 예외로 끝났다` 를 in-flight 개수만큼 찍는다 —
     우리가 일부러 만든 상태를 오류로 보고하게 된다.
   - **`FetchResult(0, None, None)` 을 안 쓰는 이유**(계획 3절 ②의 순진한 형태):
     `store.upsert(url, None, 0)` 로 **안 받은 페이지가 status 0 으로 DB 에 박히고**,
     다음 실행의 `store.has()` 가 그 URL 을 영영 건너뛴다. **중단이 프런티어를
     오염시켜서는 안 된다.**
6. **종료는 예산 소진 가지를 그대로 쓴다.** 루프 맨 위에서
   `interrupted = stop is not None and stop.is_set()` 를 예산 검사와 **한 가지로 묶어**
   in-flight future 를 전부 `_store_result` 로 줍고(**이미 받은 응답 유실 0**),
   사유를 stderr 에 찍고 `break`. 메시지만 갈린다: `중단 — %d페이지에서 멈춘다`.
7. **`main()`.** `stop = threading.Event()` 를 만들고 `signal.signal(SIGINT, handler)`.
   핸들러는 **`signal.signal(SIGINT, SIG_DFL)` 을 먼저, `stop.set()` 을 그다음** —
   **두 번째 Ctrl-C 는 즉사**라 사용자가 탈출구를 잃지 않는다.
   `finally` 에서 원래 핸들러를 복원한다(`signal.getsignal(SIGINT)` 로 떠 둔다).
   **반환값: 중단이면 130**, 아니면 오늘 그대로 0. `수집 N 페이지` 는 중단이어도 찍는다.
   - **130 인 이유**: 오늘 관측값(셸 130 · `returncode -2`)과 **같은 값**이라
     래퍼 스크립트의 판정이 안 바뀐다. 0 으로 바꾸면 `crawl && indexer` 가 중단 뒤에도
     다음 단계를 돈다 — 실패를 성공으로 위장하는 종류다(digest 의 `cli.py` 개명 사례).
8. **중단 단위 테스트는 `stop` 을 미리 세워 둔다** — `wait()` 가 즉시 `True` 라
   실시간이 안 흐른다. 가짜 시계(`now=`)와 섞어도 된다: 이미 세운 이벤트는 시계를 안 본다.
9. `crawl()` 독스트링의 "Ctrl-C 가 즉시 안 먹는다 … 최악 90초" 문단을 **실측으로 고친다**
   (그 90초는 계획 탐침이 오답으로 판정했다 — 실측 69.57초, 분해는 계획서 2절).

## 되돌리기

커밋 하나 revert. 그전에 **`main()` 이 `stop=` 을 안 넘기기만 해도** `crawl()` 은
오늘 경로 그대로다 — 기본값이 곧 꺼진 플래그다(`design_deadline.md` 6절과 같은 형태).

## 범위 밖

- **`fetcher.TIMEOUT` 인하** · **소켓을 강제로 끊는 기제**(축1) — 12초 목표에 불필요하다.
- **SIGTERM** · `serve.py`·`indexer.py` 의 중단 — 계획 6절 그대로 digest 후보.
- **`futures.wait` 를 깨우는 기제**(더미 future·폴링) — 탐침이 불필요를 보였다.
  워커를 10초 안에 끝내지 **못하게** 되는 변경이 오면 그때 다시 연다.
