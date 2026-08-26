---
signal: YELLOW
mode: night
plan: (없음 — 다음 계획 승인 대기)
phase: 보류
step: 3/3
attempt: 0
iteration: 72
night_iterations: 9
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 72)
ctx: 81% / 200k
rules: rules/discover.md
---

# 현재 상태

**`crawl-throughput`(008) DONE.** 브랜치 `loop/crawl-throughput`. 계획·설계·개발 3스텝·
테스트·리뷰(패스 A/B)·e2e 전부 통과. **e2e 4/4** — `docs/e2e/crawl-throughput/result.md`.

**사용자 실측 초당 0.5문서 → 같은 조건 e2e 에서 초당 10.25문서.**
`concept.md:44` 기준 5.0의 2배다. 순차(1.95/s) 대비 **5.3배**이고 간격 위반 0·중복 0.
1,700문서에서 크롤을 죽이던 `database is locked` 도 닫았다.

**discover 를 돌렸고 🟡 보류로 멈춘다 — 남은 후보 셋이 전부 사람 판단을 요구한다.**
`rules/discover.md` 142줄: digest 보류 항목은 승인 대기이므로 야간에 재시도 금지.

| 후보 | 무엇에 막혔나 | 아침에 정할 것 |
|---|---|---|
| **쿨다운 태우기** (digest `[high]`) | 프런티어 계약 변경 = 설계 승인 | 올릴지. 순진한 수정은 **간격 위반 구멍**이 있다(아래) |
| **`recrawl`** (`concept.md:31`, 사양 8번) | `docs` 에 `fetched_at` 추가 = **스키마 변경**. 야간 금지 항목 | 마이그레이션을 승인할지 |
| **`search-ui`** | 경량·디자인 축의 **측정 명령이 아직 `없음`** | 무엇으로 잴지 (`concept.md` 에 숫자를 적어야 루프가 고른다) |

셋 다 "밤에 넘겨짚으면 아침에 되돌릴 코드만 남는" 종류라 착수하지 않았다.
**한 줄만 정해주면 바로 이어간다** — 어느 것을 열지.

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
| `unittest discover tests` | **213/213** (계획 시작 전 209) |
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

## 리뷰 phase 진행 중 (반복 69)

**패스 B(대조) 끝. 패스 A(백지)는 별도 세션에 넘겼고 결과 대기 중이다.**

- **패스 B 자동 수정 2건 적용** — 설계 문서가 코드와 어긋나 있었다
  (`rules/review.md` 렌즈 1 "코드만 바꾸고 문서를 남겨두면 반려"):
  계약 4의 워커 반환 튜플이 3개로 적혀 있었다(실제 4개 — 계약 9가 `sent_at` 을 넣었다) ·
  계약 8에 `seconds_until_ready(exclude=)` 의 `exclude` 가 빠져 있었다
- **렌즈 4 (과거 리뷰 지적 재발) — 없다.** `04b9fb6` 이 `frontier.py` 에 박은
  "간격은 늘어나는 방향으로만" 을 `mark_sent` 도 지킨다(`max(...)`, `frontier.py:82`).
  `set_delay` 는 안 건드렸다
- **렌즈 3 (과거 결정 되살리기) — 없다.** `store.py` 이력에 WAL·timeout 을
  의도적으로 피한 커밋이 없다(`git log -S journal_mode` 무소득). digest 에도 없다
- **렌즈 5 (주석 지침 위반) — 없다.** 수정한 파일에 "이렇게 하지 마라" 류 지침 없음

## 패스 A(백지) 결과 — 5건, **3건 반영 · 1건 보류 · 1건 부분기각**

**패스 A 가 내 눈이 먼 자리를 정확히 짚었다. 리뷰를 남에게 넘긴 값을 했다.**

1. **[반영·중대] `timeout=30` 을 검증하는 테스트가 없었다.** sqlite3 기본
   `busy_timeout` 은 0이 아니라 **5000ms** 라, 0.3초만 붙드는 테스트는 `timeout=` 을
   통째로 지워도 통과한다. **내가 반복 69에 "갭을 메웠다" 고 쓴 것은 틀렸다** —
   변이를 `timeout=0` 으로 잡은 게 실수였다(진짜 되돌리기는 인자 삭제).
   → `PRAGMA busy_timeout > 5000` 한 줄로 상한 계약을 고정했다.
   변이 `sqlite3.connect(path)` → **실패 확인**(`5000 not greater than 5000`)
2. **[보류] `store.has()` 로 건너뛴 URL 이 도메인 쿨다운을 태운다.** 사실이다 —
   `frontier.next()` 가 팝 시점에 `_last_fetch` 를 쓰는데(`frontier.py:70`) 요청은 안 나간다.
   **다만 야간에 안 고친다. 리뷰어가 제안한 수정(팝의 쓰기 제거)에 구멍이 있다** —
   워커가 예외로 끝나면 `_store_result` 가 `mark_sent` 없이 반환하는데 요청은 이미 나갔을
   수 있다. 그러면 그 도메인은 쿨다운 없이 곧바로 다시 뽑힌다 = **간격 위반**.
   `concept.md:59` 는 크롤 윤리를 성능 위에 둔다. 제출 시점 `mark_sent` + 팝 쓰기 제거가
   답으로 보이지만 프런티어 계약 변경이라 사람이 볼 자리다.
   **이 계획의 목표 숫자에는 영향 없다** — `_seen` 이 한 실행 안의 중복을 막아
   `store.has` 는 주로 **이어받기 크롤**에서 참이 된다(신규 크롤인 `perf_crawl` 은 무관)
3. **[반영] `_fetch_one` 독스트링이 거짓이었다.** `robots` 는 워커 공유 `RobotsCache` 이고
   `_parser` 는 check-then-set 이다. 계약 3이 막아줘서 버그는 아니지만 문장이 잘못 안심시킨다
   → "계약 3을 풀면 여기가 깨진다" 까지 조건을 명시
4. **[반영] Ctrl-C 가 최대 30초 안 먹는다** — 이 계획이 만든 회귀다(풀이 나갈 때 기다린다).
   유실은 없다(upsert 마다 커밋). `cancel_futures` 는 **약이 안 된다** — 취소되는 건 대기 중
   작업뿐인데 여기선 제출한 것이 곧 실행 중인 것이다. 그래서 코드가 아니라 독스트링에 적었다
5. **[부분기각] `perf_crawl` 기준선이 헐겁다** — 사실이다(workers 8→4 도 통과).
   **다만 "문서와 어긋난다" 는 성립하지 않는다** — 문서가 주장한 건 "지연이 없으면 순차와
   동시가 같은 숫자를 낸다" 뿐이고 그건 참이다(1.95 대 10.27, 기준 5.0이 그 사이).
   `TARGET_RATE` 는 `concept.md:44` 의 제품 목표라 **올리지 않는다** — 야간에 목표를
   옮기지 않는다. 대신 무엇을 못 잡는지 상수 옆에 적었고, 부분 회귀는 시간이 아니라
   `TestConcurrency`(배리어)가 잡는다

**리뷰어가 정상 확인한 것**: 도메인 간격 계약 성립(`exclude=busy` + `mark_sent` 의 max 단조성),
`saved + len(inflight) < max_pages` 게이트, `seconds_until_ready() or None` 의 바쁜대기 차단

## e2e 결과 4/4 (반복 71)

| # | 시나리오 | 결과 |
|---|---|---|
| 1 | 48문서를 10초 안에 | **4.68초 · 10.25/s** |
| 2 | 도메인 간격 1초 | 12도메인 전부 0.95s 이상 · 위반 0 |
| 3 | 같은 URL 두 번 안 받는다 | 중복 0 |
| 4 | 워커 1로도 같은 결과 | **sha1 동일** · 24.59초 · 1.95/s |

시나리오 4를 위해 `perf_crawl.py` 가 인자로 워커 수를 받게 했다(6줄).
되돌리기 경로가 **느릴 뿐 결과가 같다**는 걸 e2e 수준에서 처음 증명했다.

## 남긴 것 (다음 계획 후보 / 사람이 볼 자리)

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
