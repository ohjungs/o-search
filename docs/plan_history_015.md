# 계획: domain-key — 같은 서버는 한 칸이다

- 브랜치: `loop/domain-key` (기점 `677ed3e`, `loop/retry-interval` 위)
- 출처: `docs/digest.md ## 판단 필요` 의 `[high]` (반복 105 백지 리뷰 지적 #1 → 탐침 실측)
- 의존: 016(`retry-interval`) — 같은 열쇠를 쓰는 코드가 거기서 하나 더 늘었다

## 1. 문제 · 목표 · 기대 결과

### 문제 — 대소문자 하나로 예의 계약이 통째로 빠져나간다

도메인 열쇠를 **날 `netloc`** 으로 쓴다:

```python
domain = urllib.parse.urlsplit(url).netloc     # frontier.py:57 · crawl.py:108
```

호스트는 **대소문자 무관**이고 `:80`/`:443` 은 **기본 포트**다. 셋 다 같은 서버인데
큐도 `_last_fetch` 도 `_delays` 도 칸이 갈린다.

**진짜 소켓·진짜 크롤 루프 실측** (서버가 `Crawl-delay: 3` 을 선언하고,
시드 페이지가 `http://LOCALHOST:P/x` 와 `http://localhost:P/y` 를 건다):

```
+0.000  Host=localhost:P    /robots.txt
+0.001  Host=localhost:P    /
+0.002  Host=LOCALHOST:P    /robots.txt      ← 같은 서버의 robots.txt 를 두 번 받는다
+0.002  Host=LOCALHOST:P    /x
+3.009  Host=localhost:P    /y               ← 대조군: 제대로 3초를 기다린다
```

**3초를 요구한 서버가 2밀리초 안에 요청 4개를 받는다.** 그리고 `/`와 `/x` 는
in-flight 집합도 열쇠가 갈려 **동시에 떠 있다**(동시화 계약 3 위반).

프런티어 단위 탐침도 같은 말을 한다 — `http://b.test/1` · `http://B.test/2` ·
`http://b.test:80/3` 을 넣고 `http://b.test` 에만 `Crawl-delay: 5` 를 걸면
셋이 **t=1000.000 에 전부 발신, 간격 0.000초**이고 선언한 5초는 나머지 둘에 안 걸린다.

**이것은 절대 조건 위반이다** — "어떤 경우에도 선언된 `Crawl-delay` 보다 빨리 치지
않는다". 014·016 이 닫은 구멍들과 달리 이번 것은 **아무것도 잘못되지 않아도** 열린다:
사이트가 자기 링크에 호스트를 대문자로 쓰기만 하면 된다.

### 목표

**열쇠를 만드는 자리를 한 곳으로 모으고, 거기서 같은 서버를 같은 칸으로 넣는다.**
호스트 소문자화 + 스킴별 기본 포트 제거. 그뿐이다.

### 기대 결과 (측정 가능하게)

| # | 기대 | 재는 법 |
|---|---|---|
| 1 | 대소문자만 다른 호스트가 간격을 나눠 갖는다 | 서버 수신 간격 ≥ 선언값 (지금 **0.002초**) |
| 2 | 기본 포트를 붙인 URL 도 같은 칸 — `http://h:80` ≡ `http://h` | 같은 자로 잰다 |
| 3 | **기본이 아닌 포트는 여전히 다른 도메인** | 대조군. `http://h:443` 은 `http://h` 와 별개 |
| 4 | 같은 서버가 동시에 안 뜬다 (동시화 계약 3) | in-flight 겹침 0 |
| 5 | 같은 서버의 `robots.txt` 를 두 번 안 받는다 | 서버 로그의 `/robots.txt` 건수 (지금 2) |
| 6 | **읽을 수 없는 포트가 크롤 루프를 안 죽인다** | `:abc` · `:99999` 를 넣어도 예외 0 |
| 7 | 회귀: 차단 사이트 처리량 | `e2e/perf_crawl.py` [차단] ≥ 9.0/s |

## 2. 읽고 확인한 것 (추측 아님)

- **열쇠를 계산하는 자리는 정확히 셋이다.** `frontier.py:57`(`add`) ·
  `crawl.py:108`(제출 직전) · `robots.py:66`(`_base`, 여기만 `스킴://` 을 앞에 붙인다).
  `grep -rn netloc src/` 로 확인했고 나머지는 전부 주석이거나 `urls.py` 내부다
- `Frontier` 의 다른 메서드(`next`·`mark_sent`·`set_delay`·`interval`·
  `seconds_until_ready`)는 **도메인을 받기만 한다** — 만드는 자리가 아니다
- `Store` 와 `Frontier._seen` 은 **URL** 로 센다. 이 계획은 그쪽을 안 건드린다
- **`urlsplit(...).port` 는 ValueError 를 던진다** (실측: `:99999` → "Port out of
  range", `:abc` → "could not be cast"). 지금 `netloc` 은 절대 안 던지므로
  **`.port` 를 쓰면 없던 크래시 경로가 생긴다** — 문자열로만 가른다
- `urlsplit(...).hostname` 은 소문자화·브래킷 제거·userinfo 제거를 한 번에 하지만
  IPv6 를 되-브래킷해야 하고 위 `.port` 와 짝이라 결국 같은 함정이다. 실측:
  `http://[::1]:80/` → `netloc='[::1]:80'` · `hostname='::1'`
- `to_ascii()` 는 **ASCII URL 을 한 글자도 안 바꾼다**(`urls.py:31`). 그래서
  대소문자가 여기까지 살아 온다 — 그 규칙 자체는 회귀 방어라 안 건드린다
- `e2e/perf_crawl.py` 는 "포트가 곧 netloc" 에 기대 도메인 12개를 만든다.
  전부 **기본이 아닌 포트**라 이 변경의 영향 밖이다 (기대 3 이 그것을 못박는다)

## 3. 스텝

### 스텝 2 — 열쇠를 만드는 자리를 하나로 모은다

의존: 없음. 파일: `src/websearch/urls.py` · `frontier.py` · `crawl.py` · `robots.py`
(+ `tests/test_urls.py` · `tests/test_frontier.py` · `tests/test_crawl.py`)

- `urls.domain_key(url)` 신규 — userinfo 를 떼고, 호스트를 소문자로, 스킴의 기본
  포트를 지운다. **문자열로만 가른다**(위 `.port` 실측). IPv6 리터럴은 `]` 가
  포트 자리에 있는지로 판별한다
- 세 호출부가 그것만 쓴다. `robots._base` 는 `스킴 + "://" + domain_key(url)`

RED 를 먼저 본다: 기대 1을 단언하는 테스트가 현재 코드에서 **0초대**로 실패하는 것을
확인한다(탐침 실측과 같은 자리여야 한다).

### 스텝 3 — 테스트 phase

의존: 2. `rules/test.md` 6개 카테고리. 변이는 **"이 줄을 안 썼다면"** 기준. 무변이 기준선 먼저.
기대 3(대조군)과 기대 6(안 죽는다)이 이 계획에서 가장 쉽게 빠지는 단언이다.

### 스텝 4 — 리뷰

의존: 3. **별도 백지 세션**(diff + 소스만, `docs/` 차단).

### 스텝 5 — e2e

의존: 4. `docs/e2e/domain-key/result.md`. **사이트 로그 쪽에서** 잰다
(`crawl_politeness_e2e.py`·`retry_interval_e2e.py` 와 같은 자세).

1. `Crawl-delay` 를 선언한 서버에 **대소문자가 다른 호스트**로 링크가 걸린다
   → 서버 수신 간격이 선언값 이상 · `robots.txt` 는 **1회**
2. 기본 포트를 붙인 링크(`http://h:80/`)도 같은 칸
3. 대조군: **기본이 아닌 포트**는 여전히 다른 도메인 — 남의 간격에 안 묶인다
4. 잴 대상이 사라지면(요청 표본 부족) **종료 코드 2**
5. 회귀: `e2e/perf_crawl.py` [차단] 처리량

## 4. 하지 않을 것

- **URL 정규화** (digest `[5]`) — `http://A.com/` 과 `http://a.com/` 은 이 계획 뒤에도
  **두 번 수집되고 두 행으로 저장된다.** 여기서 고치는 것은 **예의 계약이 세는 단위**
  하나뿐이다. URL 동일성은 `store`·`_seen`·리다이렉트·끝 슬래시·퍼센트 표기가 전부
  걸린 별개의 수술이고, 그쪽은 크롤 **양**의 문제지 크롤 **윤리**의 문제가 아니다
- **끝점 하나(`b.test.` ↔ `b.test`)** — DNS 상 같은 이름이지만 Host 헤더가 달라지고
  가상호스트가 갈릴 수 있다. 실물에서 보이면 그때 잰다
- `DOMAIN_INTERVAL`·`MAX_DELAY`·`fetcher.RETRIES` 값 변경
- recrawl · `X-Robots-Tag` · `loop/*` 병합 · `docs/specs/` 수정 · `pages` 테이블
