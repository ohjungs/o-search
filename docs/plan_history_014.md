# 계획: retry-interval — 재시도도 프런티어가 아는 간격을 지킨다

- 브랜치: `loop/retry-interval` (기점 `5e7b525`, `loop/pagination-ui` 위)
- 출처: `docs/digest.md ## 판단 필요` 의 `[5]` (반복 95 리뷰 패스 A 지적 → 탐침 실측)
- 의존: 014(`crawl-politeness`, 발신 훅 `before_send` 와 재시도 사이 sleep)

## 1. 문제 · 목표 · 기대 결과

### 문제 — 재시도만 스킴별 robots 를 보고, 프런티어가 아는 것을 모른다

`_fetch_one`(`src/websearch/crawl.py:37-38`)이 간격을 이렇게 구한다:

```python
requested = robots.delay(url)
interval = max(DOMAIN_INTERVAL, requested or 0)
```

`robots.delay(url)` 이 돌려주는 것은 **그 스킴의 `robots.txt`** 가 선언한 값이다.
그런데 `Frontier` 는 **netloc 단위**로 간격을 들고 `set_delay` 로 단조 증가시킨다
(`frontier.py:34`) — `http://b.test` 가 선언한 5초를 `https://b.test` 에도 건다.

**같은 서버인데 두 경로가 다른 값을 쓴다.** 실측(`http` 만 `Crawl-delay: 5`):

| 무엇 | 간격 |
|---|---|
| URL 사이 (프런티어가 잰다) | **5.000초** |
| `https` URL 의 **재시도 3회** (`_fetch_one` 이 잰다) | **1.000초** |

https 쪽 robots 가 선언한 값이 없으니 **절대 조건 위반은 아니다.** 그러나
**재시도 경로만 URL 사이 경로보다 덜 조심한다** — 그리고 재시도가 나가는 상황은
서버가 이미 아플 때다(연결 거부·RST). 덜 조심할 자리로 최악이다.

### 목표

`_fetch_one` 이 쓰는 간격의 **바닥을 프런티어가 아는 값까지 올린다.** 그뿐이다.
간격을 내리는 방향은 이 계획에 없다.

### 기대 결과 (측정 가능하게)

| # | 기대 | 재는 법 |
|---|---|---|
| 1 | `http` 만 `Crawl-delay: 5` 일 때 `https` **재시도** 간격이 5초 이상 | 발신 시각 차 (지금 1.0) |
| 2 | 선언이 없는 도메인의 재시도는 여전히 하한 1초 — **올리지 않는다** | 대조군, 1.0 ≤ g < 2.0 |
| 3 | 스킴별 선언이 서로 다르면 **큰 쪽**을 쓴다 | `https` 가 7, 프런티어가 5 → 7 |
| 4 | 워커는 여전히 `Frontier` 를 안 만진다 (설계 계약 4) | 바닥값은 **제출 시점에 메인 스레드가** 읽어 넘긴다 |
| 5 | `MAX_DELAY` 초과 도메인은 여전히 `retries=0` | 깎아서 때리지 않는다 |
| 6 | 회귀: 차단 사이트 처리량 | `e2e/perf_crawl.py` [차단] ≥ 9.0/s |

## 2. 읽고 확인한 것 (추측 아님)

- `Frontier._interval(domain)`(`frontier.py:37-38`)이 **이미 있다.** 하는 일이 정확히
  "이 도메인에 대해 아는 간격, 모르면 하한" 이다. 새로 만들 것이 없고 **밑줄만 뗀다**
- 그 값은 이미 `max(self._interval(domain), seconds or 0)` 로 **단조 증가**한다
  (`frontier.py:34`) — 내려가는 경로가 없다는 것이 이 계획의 안전 근거다
- **워커는 `Frontier` 를 만지면 안 된다**(설계 계약 4, `crawl.py:21` 주석).
  그러므로 `_fetch_one` 안에서 부르지 않는다 — 제출 시점(`crawl.py:101`)에 메인
  스레드가 이미 `domain` 을 손에 들고 있으므로(`crawl.py:99`) 거기서 읽어 넘긴다
- `interval` 은 `before_send` 의 재우기와 `retries=... if interval <= MAX_DELAY else 0`
  **두 곳**에 쓰인다(`crawl.py:49,57`) — 바닥을 올리면 둘 다 따라 오른다. 5번 기대가
  그것이 뒤집히지 않았는지 잰다

## 3. 스텝

### 스텝 2 — 바닥값을 제출 시점에 읽어 워커에 넘긴다

의존: 없음. 파일: `src/websearch/frontier.py` · `src/websearch/crawl.py` (+ `tests/test_crawl.py`)

- `Frontier._interval` → `Frontier.interval` (공개 읽기. 내부 호출부도 함께 고친다)
- `_fetch_one(url, robots, now, floor)` — `interval = max(floor, requested or 0)`.
  `floor` 는 이미 `DOMAIN_INTERVAL` 이상이라 하한이 사라지지 않는다
- `crawl.py:101` 이 `frontier.interval(domain)` 을 읽어 넘긴다

RED 를 먼저 본다: 기대 1을 단언하는 테스트가 현재 코드에서 **1.0초**로 실패하는 것을 확인한다.

### 스텝 3 — 테스트 phase

의존: 2. `rules/test.md` 6개 카테고리. 변이는 **"이 줄을 안 썼다면"** 기준. 무변이 기준선 먼저.

### 스텝 4 — 리뷰

의존: 3. **별도 백지 세션**(diff + 소스만, `docs/` 차단).

### 스텝 5 — e2e

의존: 4. `docs/e2e/retry-interval/result.md`. **사이트 로그 쪽에서** 잰다
(`crawl_politeness_e2e.py` 와 같은 자세 — 우리가 의도한 것이 아니라 사이트에 닿은 시각).

1. 한 서버가 `http` 로는 `Crawl-delay: 5`, `https` 로는 선언 없음. `https` 페이지가
   연결을 끊어 재시도를 만든다 → **서버 로그의 재시도 간격이 5초 이상**
2. 대조군 도메인(선언 없음)의 재시도는 1초대에 머문다 — **남의 값이 새지 않는다**
3. 잴 대상이 사라지면(재시도 표본 부족) **종료 코드 2**
4. 회귀: `e2e/perf_crawl.py` [차단] 처리량

## 4. 하지 않을 것

- `robots.delay` 를 스킴 무관으로 바꾸기 — `robots.txt` 는 **스킴별로 다른 문서**다.
  없는 선언을 있는 것처럼 읽는 것은 사양을 어기는 쪽이다. 우리는 **더 기다리기만** 한다
- `Frontier` 에 쓰기 경로 추가 · 워커가 `Frontier` 를 만지게 하기 (설계 계약 4)
- `DOMAIN_INTERVAL`·`MAX_DELAY`·`fetcher.RETRIES` 값 변경
- recrawl · `X-Robots-Tag` · `loop/*` 병합 · `docs/specs/` 수정 · `pages` 테이블
