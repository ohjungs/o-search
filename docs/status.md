---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 개발
step: 3/3
attempt: 0
iteration: 67
night_iterations: 4
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 67)
ctx: 82% / 200k
rules: rules/dev.md
---

# 현재 상태

**`crawl-throughput`(008) 개발 스텝 2/3 완료 — 목표 숫자를 넘겼다.**
브랜치 `loop/crawl-throughput`. **다음은 개발 스텝 3/3 (`store` 잠금 내성).**

## 스텝 2가 만든 것

**초당 1.95문서 → 초당 10.30문서** (`concept.md:44` 기준 5.0의 2배).
12도메인·응답지연 0.4초·48문서를 4.66초에 수집. **간격 위반 0 · 중복 요청 0.**

- `src/websearch/crawl.py` — `ThreadPoolExecutor` 로 **네트워크만** 동시화.
  `_fetch_one()` 워커는 `robots.allowed()` → `robots.delay()` → 발신 시각 → `fetch()`
  만 하고 튜플을 돌려준다. `_store_result()` 가 메인 스레드에서 반영한다.
  **`Store`·`Frontier` 는 여전히 메인 전용 — 락도 스레드별 커넥션도 0**
- `src/websearch/frontier.py` — `next(exclude=)` · `seconds_until_ready(exclude=)` ·
  `mark_sent(domain, at)` 신설
- CLI `--workers N`(기본 8, `_number_flag()` 로 `--max` 와 같은 방어)

## 검증 (전부 실제로 돌렸다)

| 무엇 | 결과 |
|---|---|
| `unittest discover tests` | **209/209** |
| `e2e/perf_crawl.py` | **10.30/s** · 종료 0 |
| `e2e/crawl_e2e.py` · `crawl_delay_e2e.py` · `non_ascii_e2e.py` | 전부 종료 0 |
| 되돌리기 경로 `workers=1` | 1.82/s · 간격 위반 0 · 중복 0 |
| 변이 `exclude=busy` 제거 | `TestConcurrency` 실패 |
| 변이 `mark_sent` 제거 | 간격 위반 0.596초 재발 |

## 이 스텝이 바꾼 계약 하나 (리뷰가 봐야 한다)

`test_redirect_final_url_normalized_before_store` 를 **`workers=1` 로 좁혔다.**
동시 크롤은 **이미 떠 있는 요청**까지는 못 막는다 — 리다이렉트가 어디로 갈지는
응답이 와야 알고 그때 다른 워커는 이미 나갔다. 큐에 남아 있는 URL 은 그대로 막힌다
(제출 전 `store.has(url)`). 저장은 여전히 1행이고, 간격도 안 깨진다.
**잃은 것은 "리다이렉트로 수렴하는 두 URL 중 하나를 안 보낸다" 뿐**이다.

## 다음 스텝 3/3 — `store` 가 잠긴 DB 에 안 죽는다

건드릴 파일 `src/websearch/store.py`(`sqlite3.connect(path)` 한 줄) · `tests/test_store.py`.
먼저 실패하는 테스트를 쓴다: 임시 파일 DB 에 **두 번째 연결**이 쓰기 트랜잭션을 연 채
`Store.upsert()` 를 부르면 지금은 `sqlite3.OperationalError` 가 난다
(사용자가 1,700문서에서 실제로 밟은 크래시 — `indexer` 가 같은 DB 를 읽는 중이었다).
계획서 "스텝 3" 절 참조. **스텝 1·2와 독립이다.**

- 이미 한 것: 스텝 1·2 완료·커밋. 스텝 3은 아직 0줄

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
- digest `[7]` `robots.allowed()` 비ASCII 예외 누수 — 이 계획 범위 밖
- robots.txt 요청 **자체**를 간격 시계에 싣는 것 — 계약 9는 페이지 간격만 고쳤다
