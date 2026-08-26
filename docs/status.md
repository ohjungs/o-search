---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 테스트
step: 3/3
attempt: 0
iteration: 68
night_iterations: 5
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 68)
ctx: 84% / 200k
rules: rules/test.md
---

# 현재 상태

**`crawl-throughput`(008) 개발 3스텝 전부 완료.** 브랜치 `loop/crawl-throughput`.
**다음은 테스트 phase** (`rules/test.md`) — 계획 전체를 한 번에 본다.

## 스텝 3이 만든 것 — 잠긴 DB 에 크롤이 안 죽는다

`src/websearch/store.py` 연결 두 줄. 사용자가 실제 크롤 **1,700문서째**에 밟은
`sqlite3.OperationalError: database is locked` 를 막는다.

- **WAL** — 읽는 연결(`indexer`)이 쓰는 연결(`crawl`)을 못 막는다
- **`timeout=30`** — 쓰기끼리 부딪히면 죽는 대신 기다린다. 기본 5초는 부족하다:
  `indexer.index_pages` 가 색인 **전체를 트랜잭션 하나로** 돌리고 끝에서 commit 한다
  (`indexer.py:39` INSERT 루프 → `:52` commit)
- `tests/test_store.py` — `TestConcurrentAccess` 2개. 읽기 트랜잭션이 열린 채 upsert,
  그리고 다른 연결이 커밋된 행을 본다

## 검증 (전부 실제로 돌렸다)

| 무엇 | 결과 |
|---|---|
| `unittest discover tests` | **211/211** (스텝 3 전 209) |
| RED 확인 | 고치기 전 `database is locked` 로 죽었다 — 사용자 크래시와 같은 예외 |
| 변이 `PRAGMA journal_mode=WAL` 제거 | `TestConcurrentAccess` 실패 (복원 확인) |
| `timeout=30` 탐침 (6초 붙들기) | 기본 5.0 → 5.2초 만에 죽음 · 30 → 6.5초 기다렸다 성공 |
| `e2e/perf_crawl.py` | **10.22/s** · 간격 위반 0 · 중복 0 · 종료 0 |
| `e2e/crawl_e2e.py` · `crawl_delay_e2e.py` · `non_ascii_e2e.py` | 전부 종료 0 |

스위트가 **빨라졌다** — 잠금 대기가 사라져 `test_store` 가 5.25초 → 0.013초.

## 테스트 phase 가 볼 것

1. **계약 바꾼 곳 하나** — `test_redirect_final_url_normalized_before_store` 를
   `workers=1` 로 좁혔다. 아래 절 참조. 이게 정당한 축소인지 판정한다
2. `timeout=30` 은 **커밋한 테스트가 없다** (탐침만 있다 — 6초짜리라 스위트에 안 넣었다).
   기록으로 충분한지, 느린 테스트를 하나 넣을지 판정한다
3. 동시성 테스트가 시계·배리어에 의존한다 — 불안정(flaky)한지

## 바꾼 계약 하나 (테스트·리뷰가 봐야 한다)

`test_redirect_final_url_normalized_before_store` 를 **`workers=1` 로 좁혔다.**
동시 크롤은 **이미 떠 있는 요청**까지는 못 막는다 — 리다이렉트가 어디로 갈지는
응답이 와야 알고 그때 다른 워커는 이미 나갔다. 큐에 남아 있는 URL 은 그대로 막힌다
(제출 전 `store.has(url)`). 저장은 여전히 1행이고, 간격도 안 깨진다.
**잃은 것은 "리다이렉트로 수렴하는 두 URL 중 하나를 안 보낸다" 뿐**이다.

## 보류 (그대로)

- `recrawl` 정책 (`concept.md:31`) · `search-ui`(경량·디자인 축 측정 명령이 아직 `없음`)
- digest `[7]` `robots.allowed()` 비ASCII 예외 누수 — 이 계획 범위 밖
- robots.txt 요청 **자체**를 간격 시계에 싣는 것 — 계약 9는 페이지 간격만 고쳤다
- WAL 이 만드는 `-wal`·`-shm` 사이드카 파일 — `data/` 안이라 배포·백업 영향 없다
