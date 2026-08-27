# 계획: crawl-politeness — 예의가 새는 구멍 2건을 닫는다

**DONE** (2026-08-27, 반복 96). 6스텝 전부 통과 · 단위 296건 · e2e 4/4 ·
결과 `docs/e2e/crawl-politeness/result.md`. 실측 A 1.0 → **2.01초**, B 0.0002 → **1.00초**.

- 브랜치: `loop/crawl-politeness` (기점 `cdbd842`, `loop/cooldown-burn` 위)
- 출처: `docs/digest.md ## 판단 필요` 의 `[high]` 2건 (2026-08-27 반복 86·87 실측)
- 의존: 012(`cooldown-burn`) — `_store_result` 가 "시계를 거는 유일한 자리" 라는 계약이 전제다

## 1. 문제 · 목표 · 기대 결과

### 문제 A — Crawl-delay 가 예외 한 번에 증발한다

`src/websearch/crawl.py:20` `_fetch_one()` 은 `robots.delay(url)` 을 **워커 스레드 안에서**
부르고 그 값을 **반환값으로만** 메인 스레드에 넘긴다. 워커가 예외로 끝나면
`src/websearch/crawl.py:105` 의 `except` 가지가 `frontier.set_delay()` 를 못 부른다.
프런티어는 그 도메인을 `frontier.DOMAIN_INTERVAL` = **1.0초**로 안다.

실측(2026-08-27 반복 86 테스트 phase): `Crawl-delay: 5` 도메인에서 첫 요청이 예외로 끝나면
다음 간격이 **1.0초**. 대조군(예외 없음)은 5.0초. → **robots 위반.**

### 문제 B — fetcher 의 재시도가 도메인 간격을 안 지킨다

`src/websearch/fetcher.py:44` 의 `except (URLError, OSError, HTTPException): continue` 는
**즉시** 다음 시도를 보낸다(`RETRIES=2`, 총 3회). 간격 계약은 `Frontier`/`crawl` 이 재는데
재시도는 `fetcher` **안에서** 일어나 `mark_sent` 를 한 번도 안 지나므로 프런티어는
이것을 요청 1회로 안다.

실측(2026-08-27 반복 87 리뷰 탐침): 연결을 받자마자 끊는 로컬 서버에 요청 1건
→ **TCP 연결 3회, 간격 0.0002s**. 타임아웃 실패는 10초씩 벌어져 문제가 안 되고,
**빠르게 실패하는 경로(연결 거부·RST)만** 뭉친다.

파생 문제: 재시도가 간격을 지키게 되면 마지막 발신 시각이 `_fetch_one` 이 재는
`sent_at`(첫 발신) 보다 뒤가 된다. `_store_result` 가 첫 발신 시각으로 시계를 걸면
**마지막 재시도 직후 0초 만에** 다음 요청이 나간다 — 고치면서 새 구멍을 여는 자리다.

### 왜 한 계획인가

뿌리가 같다(예의 계약이 워커 경계를 못 넘는다). 건드릴 파일이 겹친다
(`src/websearch/crawl.py` 의 `_fetch_one`·`_store_result`). 따로 열면 같은 함수를
두 번 설계하고 두 번 리뷰한다.

### 목표

1. `Crawl-delay: N` 을 선언한 도메인은 **예외 경로에서도** 그 간격 아래로 요청받지 않는다
2. `fetcher` 의 재시도도 도메인 간격을 지킨다
3. 재시도가 생긴 뒤에도 다음 요청은 **마지막 실제 발신**으로부터 간격을 센다

### 기대 결과 (측정 가능)

- `Crawl-delay: 5` + 첫 요청 예외 → 다음 간격 **≥ 5.0초** (지금 1.0초)
- 연결 거부 도메인 1 URL → TCP 연결 3회의 인접 간격 **각각 ≥ 1.0초** (지금 0.0002초)
- 회귀 없음: `PYTHONPATH=src e2e/perf_crawl.py` [차단] **≥ 9.0/s** (`BASELINE_BLOCKED`)

## 2. 갈림길이 있어 설계로 넘긴다

설계 트리거(`rules/design.md` 1절)에 걸린다:
- 3개 이상 파일(`crawl.py`·`fetcher.py`·`robots.py`)
- 공개 인터페이스 변경(`fetcher.fetch` 시그니처 / `RobotsCache` 새 메서드)
- 대안이 갈린다(아래)
- 되돌리기 어려운 선택(동시화 설계 계약 4 를 건드린다)

갈림길 요약 — **판단은 `docs/design_crawl-politeness.md` 가 한다:**

- A: 메인 스레드가 캐시에 이미 있는 delay 를 들여다보는 수단(peek) vs 반환 경로 변경.
  peek 은 **네트워크를 안 타야** 동시화 계약 4(메인 스레드는 네트워크를 안 한다)를 지킨다
- B: 재시도 사이 sleep 을 `fetcher` 안에 두기 vs 재시도를 크롤 루프로 끌어올려
  프런티어가 재게 하기 vs `fetcher` 에 발신 훅을 주고 간격 판단은 `crawl` 이 하기

**어떤 대안을 고르든 지키는 것**(`docs/specs/concept.md` 갈림길 1순위 = 크롤 윤리):
선언된 `Crawl-delay` 보다 빠르게 때리지 않는다. 모르면 **느린 쪽**으로 틀린다.
도메인당 1초는 하한이지 상한이 아니다. 성능과 부딪히면 **성능을 깎는다.**

## 3. 스텝

### 스텝 1 — 설계
- 의존: 없음
- 산출물: `docs/design_crawl-politeness.md`
- 완료 기준: 대안 A·B 각각에 선택과 근거, 계약 문장, 되돌리는 법이 적혀 있다

### 스텝 2 — 문제 A: 예외 경로에서도 Crawl-delay 를 건다
- 의존: 1
- 예상 파일: `src/websearch/crawl.py`, `src/websearch/robots.py`,
  `tests/test_crawl.py`, `tests/test_robots.py`
- 시작 지점: `src/websearch/crawl.py:105` 의 `except Exception as err:` 가지
- 완료 기준(TDD, 먼저 실패해야 한다):
  - `Crawl-delay: 5` 도메인 + 첫 요청 예외 → 주입 시계로 잰 다음 발신 간격 **≥ 5.0**
  - **긍정 짝**: 같은 도메인에서 예외가 없으면 그대로 5.0 (측정 대상이 살아 있음을 보인다)
  - **음성 대조**: robots 를 한 번도 못 읽은 도메인은 1.0 그대로 (모르는 값을 지어내지 않는다)
  - 변이: 새로 추가한 줄을 지우면 위 첫 테스트가 실패한다 (**무변이 기준선을 먼저 잡는다**)

### 스텝 3 — 문제 B: 재시도가 간격을 지킨다
- 의존: 1 (스텝 2 와는 서로 의존하지 않는다. 같은 파일을 건드려 순차로 돈다)
- 예상 파일: `src/websearch/fetcher.py`, `src/websearch/crawl.py`,
  `tests/test_fetcher.py`, `tests/test_crawl.py`
- 시작 지점: `src/websearch/fetcher.py:44` 의 `continue`
- 완료 기준(TDD):
  - 주입한 sleep 으로: 연결 실패 3회 시 **재시도 2회 앞에 각각 간격 이상 대기**
  - **긍정 짝**: 성공하면 대기가 0회 (대기가 항상 걸리는 것이 아님을 보인다)
  - `HTTPError`(확정 응답)·`UnicodeError`(URL 오류)는 재시도도 대기도 없다 — 기존 계약 유지
  - `_store_result` 가 거는 시각이 **마지막 발신 ≥** 임을 주입 시계로 잰다
  - 실제 `time.sleep` 으로 테스트를 느리게 만들지 않는다
- 자동 적용 한도: 40줄. 넘으면 패치로만 남긴다 (`SKILL.md` 무인 모드)

### 스텝 4 — 테스트 phase (갭 탐색 + 전체)
- 의존: 2, 3
- 완료 기준: `PYTHONPATH=src python3 -m unittest discover tests` 전부 통과,
  269건 이상. 새 public 함수·분기에 테스트 0 인 곳이 없다

### 스텝 5 — 리뷰
- 의존: 4
- **별도 백지 세션**에 넘긴다(`docs/` 차단, diff·소스만) → `rules/review.md`

### 스텝 6 — e2e
- 의존: 5
- 산출물: `docs/e2e/crawl-politeness/result.md`

## 4. e2e 시나리오 (지금 확정한다 — 구현에 맞춰 낮추지 않는다)

1. **예외를 겪고도 느린 사이트를 존중한다**: `Crawl-delay: 2` 를 선언한 로컬 사이트에서
   첫 요청이 예외로 끝난다. 그 도메인의 **인접 요청 간격이 모두 ≥ 2.0초**.
   대조군으로 `Crawl-delay: 0` 사이트는 ≥ 1.0초이면서 < 2.0초 (남의 간격이 새지 않는다)
2. **재시도가 몰아치지 않는다**: 연결을 받자마자 끊는 로컬 서버에 URL 1건.
   서버가 본 **TCP 연결 3회의 인접 간격이 각각 ≥ 1.0초**
3. **잴 대상이 사라지면 조용히 통과하지 않는다**: 시나리오 1·2 가 세는 대상
   (요청 로그 · 연결 수)이 0이거나 기대 개수와 다르면 실패가 아니라 **측정 불능(종료 코드 2)**
4. **회귀 없음**: `PYTHONPATH=src e2e/perf_crawl.py` [차단] ≥ 9.0/s,
   `PYTHONPATH=src e2e/crawl_delay_e2e.py` 종료 코드 0

## 5. 하지 않을 것

- `pages` 테이블·스키마 — 원본이다. 손대지 않는다
- recrawl(`store.has` 상태 불문 스킵 · indexer 증분) — 별도 계획
- `X-Robots-Tag` — 별도 계획
- `--deadline` · Ctrl-C 30초 지연(digest `[4]`) — 같은 파일을 지나가지만 범위 밖
- `RETRIES`·`TIMEOUT` 값 자체를 바꾸는 것 — 간격만 다룬다
- `loop/*` 브랜치 병합 — 사람 몫
- `docs/specs/` — 읽기만 한다
- `frontier.DOMAIN_INTERVAL`·`MAX_DELAY` 값 변경 — 윤리 하한이다
- `e2e/perf_crawl.py` 의 기준선 숫자 완화 — 회귀를 숨기는 것이다
