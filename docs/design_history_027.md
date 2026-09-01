# 설계: `crawl` 의 환경 오류를 트레이스백 대신 **안내 한 줄 + rc 1** 로

**계획**: `plan_crawl-db-guard.md` · **트리거**: 대안이 2개 이상 갈린다(`design.md` 1절) ·
**작성**: 2026-09-01

## 결정

**대안 C.** `crawl()` 이 **`Store(db_path)` 한 줄만** 감싸고 `crawl.py` 의 도메인 예외
`StoreOpenError` 를 던진다. `main()` 이 그것만 잡아 안내를 찍고 **rc 1**.
제품 diff 는 `src/websearch/crawl.py` **한 파일**이고 `store.py`·`indexer.py`·`serve.py`·
`README.md` 는 **0줄**이다.

가른 것은 **`NoUsableSeedsError` 가 이미 이 파일에 있다**는 사실이다(`crawl.py:25`·`:184`·`:376`).
"크롤이 시작될 수조차 없는 이유를 `crawl()` 이 판정하고, `main()` 이 화면과 rc 로
번역한다" 는 관용구가 그대로 맞는 자리다 — 새 구조가 아니라 **있는 구조의 두 번째 사례**다.

## 탐침이 계획의 표를 두 칸 넓혔다 (2026-09-01 실측, 임시 디렉터리)

| 상황 | 예외 | 던진 곳 | 계획 표에 있었나 |
|---|---|---|---|
| 비 DB 파일 · 쓰기 불가 부모 · 경로가 디렉터리 | `sqlite3.DatabaseError`/`OperationalError` | `store.py:22`·`:23` | 있다 |
| 부모가 일반 파일 | `FileExistsError`(=`OSError`) | `store.py:19` | 있다 |
| **다른 크롤이 쓰고 있다(락)** | `sqlite3.OperationalError: database is locked` | **`store.py:24`** (`execute(SCHEMA)`) | **없다 — 다섯째 상황·셋째 던지는 줄** |

**계획 40 의 "여덟째 자리" 가 세 번째로 반복됐다.** 열거는 `상황` 도 `타입` 도 아니라
**던지는 줄**까지 세어야 다 센 것이다. → 그래서 그물을 줄 번호가 아니라
**생성자 호출 한 줄 전체**에 건다. 넷째 던지는 줄이 생겨도 자동으로 덮인다.

## 대안 비교

| | 그물 자리 | 제품 diff | 왜 안/왜 골랐나 |
|---|---|---|---|
| A | `main` 이 `crawl(...)` 통째로 | `crawl.py` 2줄 | **오진한다 — 실측했다.** 크롤 도중 `store.upsert`(`crawl.py:315`)는 메인 스레드라 이 그물에 걸린다. 다른 크롤이 락을 쥐면 **30.6초 뒤 `database is locked`** 로 죽는데(탐침), A 는 그것을 *"DB 를 열 수 없다"* 로 찍고 이미 주운 N페이지의 `수집 N 페이지` 도 삼킨다 |
| B | `Store.__init__` 이 예외를 던진다 | `store.py` + `crawl.py` | 그물은 정확하지만 **값이 없다.** `src` 안의 `Store(...)` 호출은 `crawl.py:157` **한 곳**뿐이라(전수 grep) 예외를 아래로 내려도 받는 곳이 하나다. `store.py` 를 여는 대가만 남는다 |
| **C** ← | `crawl()` 안의 `Store(db_path)` 한 줄 | `crawl.py` 만 | 그물이 A 만큼 짧고 B 만큼 정확하다. `db_path` 를 **아는 자리**라 안내가 경로를 부른다. 관용구가 이미 있다 |

**버린 축**: A 가 한 줄 더 짧다. 작은 쪽을 안 골랐다 — 짧은 그물이 넓은 그물이었다.

## 계약 (개발이 이대로 쓴다)

- `class StoreOpenError(Exception)` — `crawl.py` 의 `NoUsableSeedsError` 옆. docstring 에
  **"환경이 안 된 것이라 rc 1, 명령줄 오류 2 와 가른다"** 를 적는다.
- `crawl()`: `store = Store(db_path)` 를 `try` 로 감싸고
  `except (sqlite3.Error, OSError) as err: raise StoreOpenError("DB 를 열 수 없다: %s — %s" % (db_path, err)) from err`.
  두 타입은 **서로 겹치지 않고**(실측: `sqlite3.Error` 는 `OSError` 의 하위가 아니다)
  둘이면 위 다섯 상황을 다 덮는다. `crawl.py` 에 `import sqlite3` 가 새로 든다(stdlib).
- `main()`: `except NoUsableSeedsError` **아래에** `except StoreOpenError as exc:
  print(exc, file=sys.stderr); return 1`. `finally` 의 시그널 복구는 그대로 지난다.
- **문구는 `indexer.py:264` 와 글자까지 같다** — 같은 상황을 두 CLI 가 다르게 부르면
  안내가 아니라 소음이다.

### 물음 셋에 대한 답

1. **그물 폭** — 생성자 한 줄. 크롤 도중의 쓰기 실패는 **오늘 그대로 트레이스백**이다.
   덮지 않는다: 그것은 "DB 를 못 열었다" 가 아니라 "N페이지를 줍고 나서 죽었다" 라
   안내 문구가 달라야 하고, 지금은 그 문구를 정할 실사용 근거가 없다.
2. **경로를 부르는가** — 부른다. `indexer` 의 안내 넷이 모두 경로를 찍고,
   `crawl` 의 경로는 사용자가 준 적 없는 기본값(`data/crawl.db`)이라 더 필요하다.
3. **락을 따로 안내하는가** — **가르지 않는다.** 도달은 가능하지만(위 표)
   `Store` 의 `timeout=30` 이 이 계획의 한도 밖이라 그 갈래를 재는 검사는 **30.6초**가
   든다 — 11.9초짜리 단위 전체보다 길다. 못 재는 갈래를 만들면 리뷰가 잡는다.
   원인 문구(`database is locked`)는 `%s` 로 이미 화면에 나온다.
   **여는 조건**: `Store` 의 timeout 을 손대는 계획이 생기면 그때 함께 잰다.

**받아들인 순서**: `Store` 는 시드 검사보다 **먼저** 열린다(`crawl.py:157` vs `:161`).
그래서 DB 가 깨진 채 시드도 틀리면 rc 1 이 rc 2 를 이긴다. 순서를 바꾸는 것은
이 계획과 직교한 편집이라 안 한다.

## 되돌리기 · 마이그레이션

**커밋 하나로 revert**(`design.md` 3절 ③). 피처 플래그 없음 — 안내 한 줄에 플래그를 달면
"어느 계약인지" 가 설정으로 갈린다. **DB·스키마 무관**이라 expand/migrate/contract 해당 없음.

## 스텝 — 계획의 잠정 1스텝을 **확정**한다. 개발 1스텝

TDD 로 RED 를 먼저 만든다. 셋 다 **단위**이고 임시 디렉터리에서 `db_path` 를 주입한다 —
`Store` 는 `crawl()` 의 첫 줄이라 **네트워크에 닿기 전에** 던진다(가짜 robots 도 불필요).

| # | 테스트 | 재는 것 |
|---|---|---|
| 1 | `test_unopenable_db_raises_store_open_error` | 비 DB 파일 → `StoreOpenError`, 메시지에 **경로**와 원문 |
| 2 | `test_unusable_db_parent_is_the_same_error` | 부모가 일반 파일 → 같은 예외 (`OSError` 갈래) |
| 3 | `test_store_open_error_is_environment_not_usage` | `mock.patch("websearch.crawl.crawl", side_effect=...)` → `main` 이 **rc 1** + stderr 한 줄 (`test_crawl.py:141` 과 같은 형태) |

단위 **462 → 465건**. **변이로 확인한다**: M1 그물에서 `OSError` 제거 → **2번만** 죽는다 ·
M2 `return 1` → `2` → **3번만** · M3 `try` 통째 제거 → 셋 다.

**`README.md` 는 0줄이다** — 계획 40 이 이미 *"`crawl`: DB 손상·쓸 수 없는 경로"* 를
rc 1 칸에 적어 뒀다(`README.md:35`). **값은 이미 참이었고 거짓이던 것은 화면뿐이다.**

## 검증

- 단위 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
  — **465건 OK**(기준선 462건 11.925초). 러너를 파이프로 감싸지 않는다.
- e2e 새로 만들지 않는다(계획 7절의 잠정 판정을 **확인**했다) — 재는 것은 `main(argv)` 의
  반환값과 stderr 이고, 다섯 상황 전부 `tempfile` 로 세워진다. `chmod` 조차 필요 없다
  (2번은 "부모가 일반 파일" 이라 권한과 무관하다 — root 로 돌려도 결과가 같다).
  회귀로 `crawl_e2e.py`(rc 0 경로) 한 번은 돈다.
- `data/crawl.db` sha256 무변경 · `digest.md` 열린 항목 50 유지(`[6]` 은 DONE 때 닫아 49).
