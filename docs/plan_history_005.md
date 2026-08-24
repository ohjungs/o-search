# 계획: robots.txt Crawl-delay 존중

- **슬러그**: `crawl-delay`
- **브랜치**: `loop/crawl-delay` (`loop/search-api` 4f92e32 에서 갈라졌다 — 이 저장소의 계획 브랜치는 직렬로 쌓인다)
- **근거**: `docs/digest.md` 다음 계획 후보 `[높음·설계 범위 밖 메모] robots crawl-delay 존중 — 윤리 축이라 우선순위 높음`
- **시작**: 2026-08-25

## 목표

지금 크롤러는 **모든 도메인에 똑같이 1초**를 쓴다(`src/websearch/frontier.py:6`
`DOMAIN_INTERVAL = 1.0`). robots.txt 가 `Crawl-delay: 10` 이라고 적어 두어도
`src/websearch/robots.py` 는 `can_fetch` 만 보고 그 줄을 읽지 않는다 —
**사이트가 명시적으로 요청한 간격을 10배 어긴다.**

`docs/specs/concept.md:59` 의 갈림길 우선순위는 크롤 윤리가 1순위이고,
`concept.md:25` 는 robots 준수와 1초 간격을 "기능이 아니라 전제 조건" 이라고 못박았다.
완료되면 도메인별 간격이 **`max(1초, robots 의 Crawl-delay)`** 가 된다 —
간격을 늘리는 방향으로만 움직이므로 1초 하한은 그대로 유지된다.

## 이미 참인 것 (착수 전 사실)

- `Frontier` 는 도메인 라운드로빈 + 쿨다운을 **큐 수준에서** 보장한다.
  간격 판정은 `Frontier.next()` 와 `Frontier.seconds_until_ready()` 두 곳뿐이고,
  둘 다 모듈 상수 `DOMAIN_INTERVAL` 을 직접 읽는다.
- `crawl.crawl()`(`src/websearch/crawl.py`)의 루프 순서는
  `frontier.next()` → `store.has()` → `robots.allowed()` → `fetcher.fetch()` 다.
  **즉 robots.txt 는 그 도메인의 첫 URL 을 팝한 뒤에야 적재된다** —
  간격 값을 프런티어가 미리 알 수 없다. 배선 방향이 이 계획의 핵심 제약이다.
- `RobotsCache._parsers` 는 도메인(base)당 `RobotFileParser` 를 1회만 만든다
  (`tests/test_robots.py:31` 이 계약으로 고정). delay 도 같은 캐시에서 나온다.
- 기존 간격 계약 테스트: `tests/test_frontier.py:36` `test_same_domain_respects_interval`,
  `:43` `test_other_domain_served_while_first_cooling`, `:48` `test_wait_time_reported`.
  `Frontier(now=...)` 로 시계를 주입하므로 **새 테스트도 실제로 잠들지 않는다.**

## 계획 단계에서 실측한 stdlib 동작 (추측 아님, 이 저장소 Python 3.9.6)

`urllib.robotparser.RobotFileParser` 로 직접 확인했다:

| robots.txt | `crawl_delay("websearchbot/0.1")` |
|---|---|
| `User-agent: *` / `Crawl-delay: 3` | `3` |
| `User-agent: *` / **`Crawl-delay: 3.5`** | **`None`** ← 소수를 버린다 (`isdigit()` 검사) |
| `User-agent: websearchbot` / `Crawl-delay: 2` + `*` / `9` | `2` |
| `User-agent: *` / `Crawl-delay: 86400` | `86400` |

두 가지가 함정이다. **설계 phase 가 이 둘을 판정한다:**

1. **소수 간격이 조용히 사라진다.** `Crawl-delay: 0.5` 는 하한 1초가 먹으니 안전하지만,
   **`Crawl-delay: 3.5` 는 `None` 이 되어 1초로 떨어진다 — 요청보다 3.5배 빠르게 때린다.**
   윤리 축에서 이건 "지원 안 함"이 아니라 위반이다.
2. **간격 상한이 없다.** `Crawl-delay: 86400` 을 곧이곧대로 지키면 무인 크롤이 하루를 잔다.
   지켜서 멈출 것인가, 그 도메인을 버릴 것인가 — 방향이 갈린다.

또 하나 (범위 밖, 아래 "하지 않을 것"): `USER_AGENT = "websearchbot/0.1"` 에 슬래시가 있어
robots 의 `User-agent: websearchbot/0.1` 그룹은 **매치되지 않는다**(stdlib 이 UA 를
`/` 앞에서 자른 뒤 `in` 으로 비교한다). `User-agent: websearchbot` 은 매치된다.
`can_fetch` 도 이미 같은 규칙으로 돌고 있어 이 계획이 만드는 문제가 아니다.

## 하지 않을 것

- **`Retry-After` · 429 백오프** — 응답 기반 제어라 `fetcher` 계약을 바꾼다. 별도 계획
- **`Request-rate` 지시자** — `Crawl-delay` 보다 드물다. 실물에서 보이면 그때
- **robots UA 매칭 규칙 수정** (위 슬래시 건) — `can_fetch` 의 판정까지 같이 바뀐다.
  `digest.md` 후보로 남긴다
- **`frontier` 공회전 수정** (`digest.md` 판단 필요: robots 차단 URL 이 쿨다운을 소모) —
  프런티어 계약 변경이라 사람 판단 대기 중. 이 계획은 **간격 값만** 건드린다
- **크롤 스키마·저장 형식** — 변경 없음. 무인 모드 금지 항목이다
- **`sitemap` 파싱**, robots 캐시 TTL — 범위 밖

## 설계

- **필요** → `docs/design_crawl-delay.md`
  (트리거: ① 파일 3개 이상 — `robots.py`·`frontier.py`·`crawl.py`
  ② `Frontier` 공개 인터페이스 추가 ③ **대안이 갈린다** — 위 함정 2개의 처리 방향과,
  간격 값을 프런티어에 넣는 배선 방향(크롤 루프가 밀어넣기 vs 프런티어가 콜백으로 당기기))

## 스텝

### 1. `RobotsCache` 가 Crawl-delay 를 읽는다
- **완료 기준**: `RobotsCache.delay(url)` 이 `Crawl-delay: 3` 인 robots 에 `3.0`,
  지시가 없으면 `None` 을 돌려준다. **소수(`Crawl-delay: 3.5`) 처리는 설계가 정한 대로**
  단언한다(stdlib 은 버린다 — 위 실측표). 도메인당 robots 1회 적재 계약
  (`tests/test_robots.py:31`)이 깨지지 않는다
- **건드릴 파일**: `src/websearch/robots.py`, `tests/test_robots.py`
- **의존**: 없음
- **상태**: 완료

### 2. `Frontier` 가 도메인별 간격을 갖는다
- **완료 기준**: `Frontier.set_delay(domain, seconds)` 후 그 도메인만 간격이 늘고
  (`next()` 가 `None`, `seconds_until_ready()` 가 늘어난 값 반환),
  **1초 미만 값을 넣어도 1초 아래로 내려가지 않는다.** 다른 도메인은 영향 없다.
  기존 `tests/test_frontier.py` 6건 그대로 통과
- **건드릴 파일**: `src/websearch/frontier.py`, `tests/test_frontier.py`
- **의존**: 없음 (스텝 1 과 병렬이지만 야간이라 순차로 돈다)
- **상태**: 완료

### 3. 크롤 루프 배선 — robots 값이 프런티어에 닿는다
- **완료 기준**: `Crawl-delay: 5` 를 내건 가짜 robots 를 주입해 `crawl()` 을 돌리면
  같은 도메인 두 요청 사이에 **5초 이상**의 간격이 요구된다(주입 시계로 확인, 실제로 안 잔다).
  상한 초과 도메인 처리는 설계가 정한 대로 단언한다. `tests/test_crawl.py` 기존 통과
- **건드릴 파일**: `src/websearch/crawl.py`, `tests/test_crawl.py`
- **의존**: 1, 2
- **상태**: 완료

### 4. e2e — 실제 초를 재서 확인한다
- **완료 기준**: `PYTHONPATH=src python3 e2e/crawl_delay_e2e.py` 가 0 으로 끝난다.
  로컬 HTTP 서버가 `Crawl-delay: 2` 를 내걸고 페이지를 링크로 잇는다.
  서버가 **요청 도착 시각을 기록**해, 같은 도메인 연속 요청 간격이 전부 2초 이상임을 단언한다
  (1초 하한만 지켜졌다면 실패한다). `docs/project.md` 명령 목록에 추가
- **건드릴 파일**: `e2e/crawl_delay_e2e.py`, `docs/project.md`
- **의존**: 3
- **상태**: 완료

## e2e 시나리오

1. `Crawl-delay: 2` 를 선언한 사이트를 크롤한다 → 크롤러가 그 사이트에는 2초에 한 번만 요청한다
   (서버가 잰 도착 시각으로 확인). 페이지는 전부 수집된다 — 느려질 뿐 빠뜨리지 않는다
2. `Crawl-delay` 를 선언하지 않은 사이트를 크롤한다 → 지금까지대로 1초 간격
3. `Crawl-delay: 0` 을 선언한 사이트 → **1초 아래로 내려가지 않는다**(전제 조건은 사이트가 못 푼다)

## 기록

- 2026-08-25 반복 40 — 스텝 1 완료. `RobotsCache.delay()`, 소수 폴백 포함. 130/130
- 2026-08-25 반복 41 — 스텝 2 완료. `Frontier.set_delay()`, 하한·폐기. 135/135
- 2026-08-25 반복 42 — 스텝 3 완료. 크롤 루프 배선. 138/138
- 2026-08-25 반복 43 — 스텝 4 완료. `e2e/crawl_delay_e2e.py` 4.6s 통과. **스텝 4/4 = 개발 끝**
