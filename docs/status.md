---
signal: GREEN
mode: night
plan: crawl-throughput
phase: 리뷰
step: 3/3
attempt: 0
iteration: 69
night_iterations: 6
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 69)
ctx: 81% / 200k
rules: rules/review.md
---

# 현재 상태

**`crawl-throughput`(008) 개발 3스텝 + 테스트 phase 완료.** 브랜치 `loop/crawl-throughput`.
**다음은 리뷰 phase** (`rules/review.md`) — 계획 3스텝 전체를 본다.

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
| `unittest discover tests` | **212/212** (스텝 3 전 209) |
| RED 확인 | 고치기 전 `database is locked` 로 죽었다 — 사용자 크래시와 같은 예외 |
| 변이 `journal_mode=WAL` 제거 · 변이 `timeout=0` | 각각 실패 (둘 다 복원 확인) |
| `timeout=30` 탐침 (6초 붙들기) | 기본 5.0 → 5.2초 만에 죽음 · 30 → 6.5초 기다렸다 성공 |
| `e2e/perf_crawl.py` | **10.22/s** · 간격 위반 0 · 중복 0 · 종료 0 |
| **e2e 7종 전부** (`crawl`·`crawl_delay`·`non_ascii`·`indexer`·`noindex`·`search_api`·`perf_crawl`) | 전부 종료 0 |

스위트가 **빨라졌다** — 잠금 대기가 사라져 `test_store` 가 5.25초 → 0.013초.

## 테스트 phase 결과 (반복 69)

`rules/test.md` 3절 7카테고리로 훑었다. **8점 이상 갭 1건 — 메웠다.**

- **갭(8점): `timeout` 이 하는 일에 커밋한 테스트가 없었다.** WAL 쪽은 변이로 잡히는데
  "쓰기끼리 부딪히면 죽지 않고 기다린다" 는 아무도 안 밟았다. 크롤 프로세스가 통째로
  죽는 경로라 8점. **`test_upsert_waits_out_a_writer_instead_of_dying` 추가** —
  쓰기 락을 0.3초만 붙든다(빠르다). 고정하는 계약은 "얼마나" 가 아니라 **"죽지 않는다"**.
  변이 `timeout=0` → 실패 확인
- **갭 아니었다 (확인함)**: 워커 예외 격리(계약 6) `test_crawl.py:279` ·
  `--workers` 잘못된 입력 3종 `:305-309` · `seconds_until_ready(exclude=)` `test_frontier.py:163` ·
  `workers=1` 되돌리기 `:289`
- **④ 불안정 패턴 — 시계에 안 걸었다**: 동시성 판정은 `threading.Barrier` 와
  주입한 `itertools.count` 시계다. 실시간 단언은 `e2e/perf_crawl.py` 안에만 있다
- **③ 격리** — 새 테스트는 `tempfile` + `addCleanup`, 커넥션은 만든 스레드가 소유

## 리뷰 phase 가 볼 것

1. **계약 바꾼 곳 하나** — `test_redirect_final_url_normalized_before_store` 를
   `workers=1` 로 좁혔다. 아래 절 참조. 이게 정당한 축소인지 판정한다
2. `--workers` 기본 8이 실제 웹에서 **남의 서버에 과한지** — `concept.md:59` 크롤 윤리
3. WAL 사이드카(`-wal`·`-shm`)가 배포·백업 전제를 건드리는지

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
