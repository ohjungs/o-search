# 계획: crawl-throughput — 크롤 처리량 0.5 → 5문서/초

브랜치 `loop/crawl-throughput` · 슬러그 `crawl-throughput` · 8번째 계획

## 문제

사용자가 실제 웹을 크롤하며 실측했다. **초당 0.5문서.**
`docs/specs/concept.md:44` 성능 축 2번의 기준은 **초당 5문서 이상 지속** — 10배 차이다.

원인은 `src/websearch/crawl.py:26-51` 의 루프가 **한 번에 한 페이지씩 순차로** 받는다는 것이다.
`fetcher.fetch(url)`(`src/websearch/fetcher.py:20`, 타임아웃 10초)이 돌아올 때까지
프로세스 전체가 멈춘다. 그래서 **처리량 = 1 / 평균 응답시간** 이고,
응답 2초짜리 사이트를 만나면 그 2초 동안 다른 도메인도 하나도 못 받는다.
CPU 도 디스크도 놀고 있다 — **네트워크 대기가 곧 총 소요시간**이다.

같은 실측에서 두 번째 사실이 나왔다. 1,700문서쯤에서 `store.upsert`
(`src/websearch/store.py:23`)가 `sqlite3.OperationalError: database is locked` 로
**크롤 프로세스를 통째로 죽였다.** 같은 DB 파일을 `indexer`
(`src/websearch/indexer.py:25,62,88` 이 각각 `sqlite3.connect(db_path)`)가 읽는 동안이었다.
죽은 크롤의 처리량은 0.5가 아니라 0이다 — 그래서 이 계획 안에 있다.

## 목표

**politeness 를 한 톨도 깎지 않고** 처리량을 초당 5문서 이상으로 올린다.
`concept.md:44-45` 가 방법까지 못박아 두었다:

> 도메인 다양성으로 해결하는 문제이지 간격을 줄여 해결하는 문제가 아니다.

즉 **도메인당 1초 이상 간격(`frontier.DOMAIN_INTERVAL`)과 robots.txt 준수는 그대로 두고,
서로 다른 도메인의 요청을 동시에 띄워** 대기 시간을 겹치게 만든다.
`concept.md:59` 우선순위에서 크롤 윤리는 성능보다 위다 — 부딪히면 윤리가 이긴다.

## 기대 결과

- `PYTHONPATH=src python3 e2e/perf_crawl.py` 가 **초당 5문서 이상**을 찍고 종료 코드 0
- 같은 실행에서 **도메인당 요청 간격이 전부 0.95초 이상** (동시성이 윤리를 깨지 않았다)
- `PYTHONPATH=src python3 -m unittest discover tests` 199/199 유지
- `store` 가 다른 연결이 DB 를 잡고 있는 동안에도 `OperationalError` 를 내지 않는다

## 이미 참인 것 (착수 전 상태)

- `Frontier`(`src/websearch/frontier.py`)가 **이미** 도메인 라운드로빈 + 도메인별 간격을
  큐 수준에서 보장한다. `next()` 는 간격이 안 찬 도메인을 건너뛰고, 팝하는 순간
  `_last_fetch[domain]` 을 찍는다. **간격 로직을 새로 만들 필요가 없다**
- `RobotsCache`(`src/websearch/robots.py:69`)는 base(`scheme://netloc`)당 robots.txt 를
  한 번만 받아 캐시한다
- 크롤 루프의 상태(`Store`·`Frontier`·`RobotsCache`)는 전부 한 스레드가 만지고 있다
- 199/199 통과. `loop/non-ascii-url`(007) 까지 머지된 트리에서 시작한다

## 스텝

### 스텝 1 — 처리량을 재는 수단을 먼저 만든다 (`e2e/perf_crawl.py`)

**의존: 없음** · 건드릴 파일: `e2e/perf_crawl.py`(신규) · `docs/project.md`

없는 것을 개선했다고 말하지 않으려면 숫자가 먼저다. `e2e/perf_search.py` 가
검색 p95 에 대해 하는 일을 크롤 처리량에 대해 한다.

로컬 서버로만 잰다 — **실제 네트워크를 치지 않는다.** 도메인 다양성은
**포트로 만든다**: `127.0.0.1:PORT` 는 포트마다 다른 netloc 이라
`Frontier` 에게 서로 다른 도메인이다(`frontier.py:44` 가 `urlsplit(url).netloc` 을 쓴다).
`e2e/crawl_delay_e2e.py` 가 `127.0.0.1`/`localhost` 두 개로 하던 것을 12개로 늘리는 것뿐이다.

- 서버 12개(`http.server.ThreadingHTTPServer`, 포트 0으로 OS 할당), 각각 스레드 하나
- 핸들러는 응답 전에 `time.sleep(0.4)` — **인위 지연이 이 측정의 핵심이다.**
  지연이 없으면 순차와 동시가 같은 숫자를 낸다
- 각 서버는 `robots.txt`(`User-agent: *` 만, 지시 없음)와 페이지 12개를 준다.
  홈 페이지가 자기 도메인의 나머지 페이지 + 다른 도메인 홈으로 링크한다
- 요청 시각·경로·Host 를 `REQUEST_LOG` 에 기록 (`crawl_delay_e2e.py:36` 과 같은 방식)

판정 3개, 전부 `assert`:
1. **처리량** `수집 문서 수 / 총 소요초 >= 5.0`
2. **간격** 도메인별 페이지 요청 간격이 전부 `>= 0.95` (`crawl_delay_e2e.py:86` 과 같은 여유값)
3. **중복 없음** 같은 URL 을 두 번 요청하지 않았다

**완료 기준:** `PYTHONPATH=src python3 e2e/perf_crawl.py` 를 지금 코드로 돌리면
**판정 1이 실패한다**(순차라 지연 0.4초 → 초당 2.5문서 근처). 판정 2·3은 통과한다.
실패 메시지에 실측 숫자가 찍힌다. 이 RED 가 스텝 2의 출발점이다.

### 스텝 2 — 크롤 루프를 동시 fetch 로 바꾼다

**의존: 1** (완료 판정에 스텝 1의 산출물을 실제로 돌려 읽는다)
건드릴 파일: `src/websearch/crawl.py` · `src/websearch/frontier.py` ·
`tests/test_crawl.py` · `tests/test_frontier.py`

`concurrent.futures.ThreadPoolExecutor` 로 **네트워크만** 동시에 돌린다.
`Store`·`Frontier` 는 계속 메인 스레드만 만진다 — 락도, 스레드별 커넥션도 필요 없다.
자세한 구조·대안 비교는 **설계 단계**가 정한다(아래 "설계 필요 여부").

TDD 로 먼저 쓸 실패 테스트(`rules/dev.md` 0절):
- **동시성** 가짜 `fetch` 가 `threading.Barrier(4)` 에서 만난다. 순차 루프면 배리어가
  타임아웃해 테스트가 실패한다 — 시간을 재지 않아 흔들리지 않는다
- **도메인당 동시 요청 1개** 한 도메인에 URL 이 몰려도 그 도메인의 in-flight 는
  절대 2가 되지 않는다. **이게 깨지면 동시성이 politeness 를 먹은 것이다**
- **간격 유지** 기존 `TestCrawlDelayWiring`(`tests/test_crawl.py:161`)이 그대로 통과한다
- **`max_pages` 상한** 동시 실행 중에도 반환값이 `max_pages` 를 넘지 않는다
- **워커 1개면 오늘과 같다** — 되돌리기 수단이 진짜 도는지 테스트가 확인한다

**완료 기준:** 위 테스트 전부 통과 + `unittest discover tests` 전체 통과 +
`e2e/perf_crawl.py` 판정 1·2·3 전부 통과(초당 5문서 이상).

### 스텝 3 — `store` 가 잠긴 DB 에 죽지 않는다

**의존: 없음** (스텝 1·2와 독립. 먼저 해도 된다)
건드릴 파일: `src/websearch/store.py` · `tests/test_store.py`

실측에서 크롤을 죽인 `sqlite3.OperationalError: database is locked` 를 막는다.
`Store.__init__`(`src/websearch/store.py:20`)의 `sqlite3.connect(path)` 한 줄이 전부다.

먼저 쓸 실패 테스트: 임시 파일 DB 에 **두 번째 연결**이 쓰기 트랜잭션을 연 채로
`Store.upsert()` 를 부른다 → 지금은 `OperationalError` 가 난다.

**완료 기준:** 그 테스트가 통과하고, 되돌린(문제 재현) 상태에서는 실패한다(변이 확인).
`tests/test_store.py` 기존 테스트 전부 통과.

## 하지 않을 것

- **간격·robots 완화** — `DOMAIN_INTERVAL` 1.0 은 내리지 않는다. `concept.md:25-26` 이
  "어기는 코드는 리뷰에서 RED" 라고 못박았다
- **멀티프로세스·비동기(asyncio) 재작성** — 스레드로 기준을 넘으면 거기서 멈춘다 (사다리 1번)
- **의존성 추가** — stdlib 만. `concept.md:37`
- **`store.has()` 를 메모리 집합으로 바꾸기** (digest 후보) — 지금 병목은 네트워크지
  DB 왕복이 아니다. 스텝 1의 숫자가 그렇게 말하면 그때 연다
- **robots.txt 왕복이 도메인 간격 시계에 안 실리는 것** (digest `[4]`) — 이 계획 이전부터
  있던 별개 건. 동시화가 그것을 **악화시키지 않는지만** 스텝 2 테스트로 지킨다
- **`robots.allowed()`·`delay()` 의 비ASCII 예외 누수** (digest `[7]`) — 별도 계획
- **재크롤·색인 파이프라인** — `recrawl` 은 별도 계획(8번)
- **`indexer` 쪽 커넥션 옵션** — 스텝 3은 `store.py` 만 건드린다. journal 모드는
  파일 속성이라 한쪽이 켜면 양쪽에 적용된다

## 설계 필요 여부 — **필요하다**

`rules/design.md` 1절 트리거에 **셋이 걸린다**:
- **공개 인터페이스 변경** — `crawl.crawl()` 시그니처(워커 수)와 `Frontier.next()`
- **3개 이상 파일에 걸침** — `crawl.py`·`frontier.py`·`store.py`
- **대안이 2개 이상 갈림** — "메인 스레드가 상태를 독점하고 fetch 만 던진다" 와
  "워커가 팝부터 저장까지 다 한다"는 둘 다 동작하지만 락·실패 격리·되돌리기가 전부 다르다

→ `phase: 설계`, 산출물 `docs/design_crawl-throughput.md`.
설계가 답할 것: ① 동시성 수단 ② 프런티어·저장소 동시 접근 안전 ③ 워커 하나가
죽어도 크롤 전체가 안 죽는 실패 격리 ④ 되돌리기 수단.

## e2e 시나리오 (사용자 관점, 계획 시점에 확정)

1. 12개 도메인 · 도메인당 12페이지 · 응답 지연 0.4초인 웹을 크롤한다
   → **48문서를 10초 안에** 수집한다(초당 5문서 이상)
2. 같은 실행에서 **어떤 도메인도 1초 안에 두 번 맞지 않는다**
3. 같은 실행에서 **같은 URL 을 두 번 요청하지 않는다**
4. 워커를 1로 두고 같은 크롤을 돌리면 결과 문서 집합이 같다 (느릴 뿐 동작은 동일)

## 검증 명령

| 무엇 | 명령 |
|---|---|
| 전체 테스트 | `PYTHONPATH=src python3 -m unittest discover tests` |
| 처리량 e2e | `PYTHONPATH=src python3 e2e/perf_crawl.py` |
| 기존 크롤 e2e | `PYTHONPATH=src python3 e2e/crawl_e2e.py` |
| 간격 e2e | `PYTHONPATH=src python3 e2e/crawl_delay_e2e.py` |

`PYTHONDONTWRITEBYTECODE=1` 을 붙여 돌린다 — 변이 검사가 `__pycache__` 때문에
거짓말한 적이 있다 (`docs/project.md`).
