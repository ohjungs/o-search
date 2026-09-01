---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 204
updated: 2026-09-01
ctx: 58
night_iterations: 68
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 41 `crawl-db-guard` 설계 완료 — 대안 C. 다음은 개발 1스텝.**
설계서 `docs/design_crawl-db-guard.md` · 계획서 `docs/plan_crawl-db-guard.md`
이 스텝의 `src/`·`tests/`·`e2e/` diff 는 **0줄**이다(설계 문서·기록만).

## 방금 한 것 (2026-09-01 · 설계 1)

### ① 대안 C 를 골랐다 — `crawl()` 이 `Store(db_path)` **한 줄만** 감싼다

`crawl.py` 에 도메인 예외 `StoreOpenError` 를 두고(`NoUsableSeedsError` 옆),
`crawl()` 이 `except (sqlite3.Error, OSError)` 로 잡아 그것을 던지고,
`main()` 이 그것만 잡아 안내 한 줄 + **rc 1**. 문구는 `indexer.py:264` 와 글자까지 같다.
**제품 diff 는 `crawl.py` 한 파일**이고 `store.py`(=대안 B)·`indexer.py`·`serve.py`·
`README.md` 는 **0줄**이다.

가른 것은 **관용구가 이미 이 파일에 있다**는 것이다 — `NoUsableSeedsError` 가
"`crawl()` 이 판정하고 `main()` 이 화면·rc 로 번역한다" 를 이미 하고 있다(사다리 2번).

**A(넓은 그물)는 실측이 떨어뜨렸다.** 크롤 도중의 `store.upsert`(`crawl.py:315`)는
메인 스레드라 A 의 그물에 걸리는데, 다른 크롤이 락을 쥐면 그 자리가 **30.6초 뒤
`database is locked`** 로 죽는다(탐침). A 는 그것을 *"DB 를 열 수 없다"* 로 오진하고
이미 주운 `수집 N 페이지` 도 삼킨다. **B** 는 `src` 안의 `Store(...)` 호출이
`crawl.py:157` **한 곳**뿐이라(전수 grep) 예외를 `store.py` 로 내려도 받는 곳이 하나다.

### ② 탐침이 계획 표를 두 칸 넓혔다 — **다섯째 상황·셋째 던지는 줄**

계획이 적은 네 상황(`store.py:19`·`:22`·`:23`) 밖에 하나가 더 있다:
**다른 크롤이 쓰고 있으면** `store.py:24`(`execute(SCHEMA)`)가 30.68초 뒤
`sqlite3.OperationalError: database is locked` 를 던진다.
**계획 40 의 "여덟째 자리" 가 세 번째 반복이다** — 199 는 값을, 203 은 예외 타입을,
여기서는 **던지는 줄**을 안 세었다. → 그래서 그물을 줄이 아니라 **생성자 호출 한 줄
전체**에 건다. 넷째 던지는 줄이 생겨도 자동으로 덮인다.

### ③ 락은 따로 안 가른다 · e2e 0개를 **확인**했다

락 안내를 `indexer.py:262` 처럼 가르지 않는다 — `Store` 의 `timeout=30` 이 이 계획의
한도 밖이라 그 갈래를 재는 검사가 **30.6초**로 단위 전체(11.9초)보다 길다.
못 재는 갈래는 만들지 않는다. 여는 조건은 설계서에 적었다.
계획 7절의 잠정 판정(**새 e2e 0개**)은 **확인됐다** — 세 RED 는 전부 단위이고
`db_path` 주입으로 세워진다. `Store` 는 `crawl()` 의 첫 줄이라 **네트워크에 닿기 전에**
던지고, RED 2번은 "부모가 일반 파일" 이라 `chmod` 조차 없다(실측 재현 완료).

### ④ 한도를 또 밟았다 — 러너를 `| tail -4` 로 감쌌다

**한도로 그 조항을 읽은 그 반복에** 밟았다. 맨몸으로 다시 돌려 **462 OK 11.990초** 확인.
`digest ## 반복 실패` 를 **4회 → 5회**(뒤의 넷이 연속)로 올렸다. 저장소 밖 훅이라
근본 원인은 못 고친다 — 다섯 번째 증거는 "문장으로는 안 막힌다" 쪽이다.

**짧은 경로 판정**: 정식 경로를 유지한다. 개발 스텝이 파일 2개·20줄 안이지만
**설계 트리거에 이미 걸려 설계서가 있다** — 계획서·설계서가 선 뒤라 짧은 경로의 조건
("계획서를 안 만든다")이 성립하지 않는다.

## 다음 스텝 (개발 1/1)

설계서의 표 셋을 그대로 쓴다. **TDD** — RED 세 건을 먼저 만든다:
`test_unopenable_db_raises_store_open_error`(비 DB 파일) ·
`test_unusable_db_parent_is_the_same_error`(부모가 일반 파일 = `OSError` 갈래) ·
`test_store_open_error_is_environment_not_usage`(`main` 이 rc **1** + stderr 한 줄,
`test_crawl.py:141` 과 같은 mock 형태). 단위 **462 → 465건**.
변이 M1(그물에서 `OSError` 제거)이 **2번만**, M2(`return 1`→`2`)가 **3번만** 죽여야 한다.

---

## 이전 (2026-09-01 · 계획 41 계획 — 반복 203)

**계획 40 `exit-code-contract` DONE·아카이브 완료**(`plan_history_026.md`·`design_history_026.md`),
`digest [7]` 을 닫아 열린 항목 51 → **50**. 계획 41 을 `digest [6]`(6순위)에서 열었다 —
1~5순위는 전부 0건이었고 7순위(`## 반복 실패` 의 닫힌 항목)가 같은 자리를 가리켰다.
착수 탐침이 후보의 처방을 넓혔다(네 상황 중 하나는 `sqlite3` 가 아니라 `os.makedirs`).
브랜치 `loop/crawl-db-guard`(기점 `8a99617`). 계획 34~37 은 PR #2 로 `main` 에 병합됐고
(`main` 최신 `e0890c8`) 38·39·40·41 의 병합은 사람이 정한다.
곁가지 둘: 자동 스냅샷 훅이 반복 중간에 커밋·푸시했고(`b919e68`, `digest` 3→5회),
러너를 파이프로 두 번 감쌌다(`digest` 3→4회 — **이 반복이 다섯째다**).
전문은 `history_current.md` 반복 203.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 이번 스텝에서 대조함).
- **탐침은 임시 디렉터리에서만, `cwd` 도 거기다** — 이 계획은 특히 그렇다.
  `crawl` 은 `cwd` 밑에 `data/` 를 만들고 거기 쓴다. `chmod 500` 으로 만든 디렉터리는
  탐침 끝에 반드시 되돌린다.
- 단위 **462 → 465건**(설계가 RED 셋을 지목했다). 465 미만이면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`)이 줄면 RED · **200줄(상한 200)**.
  `[6]` 은 계획 41 이 DONE 될 때만 닫는다(그때 49). 항목을 더하려면 먼저 압축한다.
- 제품 diff 는 **`src/websearch/crawl.py` 한 파일**이다(설계가 대안 C 로 확정).
  `store.py`·`indexer.py`·`serve.py`·`README.md` 가 바뀌면 RED — B 는 버렸고
  README 의 rc 1 칸은 계획 40 이 이미 참으로 만들어 뒀다.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- **러너를 파이프로 감싸지 않는다**(`## 반복 실패` **5회** 항목 — 설계 반복이 다섯째다.
  한도로 이 줄을 읽은 그 반복에 밟았으니, 읽는 것으로는 안 막힌다).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
