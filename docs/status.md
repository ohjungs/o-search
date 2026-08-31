---
signal: GREEN
phase: 개발
step: 2
attempt: 0
iteration: 194
updated: 2026-08-31
ctx: 58
night_iterations: 62
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 39 `indexer-lock` 개발 스텝 1 완료 — 계획서 `docs/plan_indexer-lock.md`.**
브랜치 `loop/indexer-lock`(기점 `bf78d02`, `loop/digest-rotate` 에서 팠다).
**계획 38 까지 전부 DONE·아카이브 완료.** 활성 계획 1개, 다음은 **개발 스텝 2**.
계획 34~37 은 PR #2 로 `main` 에 병합됐다(`main` 최신 `e0890c8`) — 38·39 의
`main` 병합은 사람이 정한다.

## 방금 한 것 (2026-08-31 · 개발 1/2)

**`indexer.py` 의 세 `sqlite3.connect(db_path)` 에 `timeout=30` 을 줬다 — 제품 3줄.**
값은 새로 안 정했다: `store.py:22` 가 계획 8 에서 고른 30초를 그대로 따른다(사다리 2번).

**TDD 를 순서대로 밟았다.** 먼저 테스트 하나(`TestCli.test_index_waits_out_a_write_lock_
instead_of_dying`) — 하위 프로세스가 `BEGIN IMMEDIATE` 로 **8초** 락을 쥐고, `locked` 한 줄을
읽어 락을 실제로 쥔 것을 본 뒤에 `indexer.main()` 을 부른다. **RED 를 눈으로 봤다**:
`sqlite3.OperationalError: database is locked` at `indexer.py:94`(`db.execute(SCHEMA)`) —
계획서 탐침 B·E 와 같은 자리다. 고친 뒤 **458건 OK**(11.9초, 새 테스트가 8초).

**변이 둘로 단언이 값을 못박는지 확인했다.** M1(`timeout=30` 3곳 삭제)은 위 RED 자체가
증거다 — 고치기 전 상태가 변이체와 바이트 단위로 같다. **M2(30 → 3)** 는 `.git` 없는
스크래치패드 사본(`src`·`tests` 만, `*.db` 없음)에 `sed -i ''` 로 심고 자리 3곳을 grep 으로
먼저 확인한 뒤 돌려 **RED**(8.03초, 같은 트레이스백). 즉 이 테스트는 인자의 **존재**만이
아니라 **값**을 고정한다 — `digest.md [7]` 이 지적한 0.3초 락의 거짓 초록을 피했다.

## 이번 계획이 하려는 일

**크롤이 도는 중에 색인을 돌리면 5초 만에 트레이스백이 난다.**
`store.py:22` 는 `sqlite3.connect(path, timeout=30)` 이고 주석이 이유까지 적어 뒀는데
(`실측에서 1,700문서째에 크롤을 죽인 게 이거다`, 계획 8), `indexer.py:78`·`136`·`181` 은
`sqlite3.connect(db_path)` 로 **timeout 을 안 준다** — 기본 5.0초다. 같은 DB 에 붙는 두
모듈이 락을 **6배 다르게** 기다린다. 계획 8 이 store 쪽에서 닫은 것의 **형제 구멍**이다.
그리고 `indexer.main` 에는 `sqlite3` 예외 갈래가 없어 rc **1** + 트레이스백이 된다 —
21·24·26·27·29 가 다섯 번 닫은 계약의 같은 파일·다른 입력이다. **앞의 다섯은 인자를
탐침했고 환경(락)은 아무도 안 쟀다.**

실측(전부 임시 디렉터리, `cwd` 도 거기):

| 상황 | 오늘 |
|---|---|
| 락 없음 | 0.03초 · rc 0 |
| 락 20초 · 첫 색인 | **5.02초 · rc 1 · 트레이스백** (`indexer.py:94`) |
| 락 20초 · 증분 색인 | **5.03초 · rc 1 · 트레이스백** — 갈래를 안 가린다 |
| 락 8초 | **5.03초 · rc 1** — `store` 의 30초 안인데도 `indexer` 만 죽는다 |
| 락 20초 · `--query` 검색 | 0.02초 · rc 0 — WAL 이라 읽기는 안 막힌다 |

**처방을 실행 전에 다시 쟀다**(`digest.md [7]`). `src` 를 스크래치패드로 통째 복사해
사본에만 `timeout=30` 을 심고(자리 3곳을 `assert` 로 먼저 확인 — `digest.md [8]`):
락 8초 **8.03초 rc 0** · 20초 **20.03초 rc 0** · 증분 8초 **8.02초 rc 0**.
그런데 **락 35초에서는 사본도 죽는다(30.04초 rc 1)** — 그래서 2스텝이다.
`timeout` 만으로는 계약을 못 닫고, 예외 갈래만으로는 5초 비대칭이 남는다.
`digest.md [8]`("깨우기와 접기는 하나다 — 한 줄씩은 0초를 회수한다")과 같은 모양이다.

## 다음 스텝 (개발 2/2)

`indexer.main` 에 `except sqlite3.DatabaseError` 갈래를 더한다 — 락이 **30초를 넘으면**
지금도 rc 1 + 트레이스백이다(탐침: 락 35초에서 30.04초 rc 1). 스텝 1 은 그 문턱을
5초에서 30초로 옮겼을 뿐 계약을 못 닫는다. `NoCrawlDataError`·`StaleIndexError` 와 같은
자리에서 rc **2** + 한 줄 안내로, `OperationalError` 의 상위인 `DatabaseError` 로 잡아
"진짜 DB 가 아닌 파일"(`file is not a database`) 형제 구멍까지 한 갈래로 덮는다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 이번 스텝에서 대조함).
  탐침은 임시 디렉터리에서만, `cwd` 도 거기다 — 색인 경로가 cwd 기준이다.
- 단위 **458건**(스텝 1 에서 +1)이 하나라도 줄면 RED · e2e 19종이 줄면 RED.
- `docs/digest.md` 열린 항목 **48**(`grep -c '^- \['`)이 줄면 RED · 189줄(상한 200).
- 제품 diff 는 `src/websearch/indexer.py` **한 파일**이다. 다른 `src/` 파일이 바뀌면 RED.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
