---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 196
updated: 2026-09-01
ctx: 36
night_iterations: 63
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 39 `indexer-lock` 테스트 phase 완료 — 계획서 `docs/plan_indexer-lock.md`.**
브랜치 `loop/indexer-lock`(기점 `bf78d02`, `loop/digest-rotate` 에서 팠다).
**계획 38 까지 전부 DONE·아카이브 완료.** 활성 계획 1개, 다음은 **리뷰**.
계획 34~37 은 PR #2 로 `main` 에 병합됐다(`main` 최신 `e0890c8`) — 38·39 의
`main` 병합은 사람이 정한다.

## 방금 한 것 (2026-09-01 · 테스트 1/1)

**갭 탐색 네 자리를 전부 실측했다. 진짜 갭은 하나였고 테스트 한 건으로 닫았다.**
`src/` 는 **0줄** — 개발이 만든 동작은 이미 옳았고 없던 것은 증거뿐이다.

| 의심한 자리 | 실측 | 판정 |
|---|---|---|
| 예외 갈래 순서 | `NoCrawlDataError`·`StaleIndexError` MRO 는 `RuntimeError` — `sqlite3.DatabaseError` 하위가 **아니다**. `KeyboardInterrupt` 는 `Exception` 하위가 아니다. 실행도 각자 제 문구를 냈다(`크롤 데이터가 없다`·`색인이 옛 정의로`·`DB 파일이 없다`) | **갭 없음** |
| 비 DB 파일(색인 경로) | `test_not_a_database_is_a_message_and_rc_2` 가 이미 실물 파일로 잰다(스텝 2 의 변이 M4 가 죽였다) | **갭 없음** |
| **`--query` + 비 DB 파일** | 동작은 옳다(rc 2 · `file is not a database` 원문 · 한 줄). **그런데 이 진입점을 재는 단언이 0건이었다** — 새 갈래를 색인 경로에서만 쟀다 | **갭 — 닫았다** |
| rc 2 충돌(usage 대 환경) | 이 스텝의 판단 범위 밖 · `## 보류` 로 넘긴다 | 리뷰로 |

**새 테스트 `TestCli.test_query_on_a_not_a_database_file_is_a_message_and_rc_2`.**
락은 안 쓰므로 스위트가 안 느려진다(461건 **11.74초**, 기준선 460건 11.94초).
**변이 M5 로 값을 증명했다** — `except sqlite3.DatabaseError` 갈래 첫 줄에
`if query is not None: raise` 를 심으니(티켓이 말한 경로로만 좁히는, 가장 그럴듯한 변이)
**65건 중 새 테스트 하나만 ERROR** 였고 색인 쪽 형제 테스트 셋은 전부 초록이었다.
그것이 이 테스트가 남의 커버리지와 겹치지 않는다는 증거다.

**곁가지로 형제를 하나 더 쟀다**: 디렉터리를 DB 로 주면
`unable to open database file` — 같은 갈래가 rc 2 로 덮는다(트레이스백 0줄).
테스트는 안 지었다 — 같은 `else` 가지를 비 DB 파일이 이미 세우고 있어
변이로 죽지 않는 테스트가 된다(`test.md` 5절).

## 보류

**rc 2 가 usage(인자 오류)와 환경 오류(락·손상 DB)를 구분하지 않는다.**
`README.md:28` 은 "인자 없이 부르면 각 명령이 자기 usage 를 낸다(rc 2)" 다.
호출 스크립트가 `rc == 2` 로 "인자를 고쳐라" 를 분기하고 있었다면 락일 때 틀린 길로 간다.

**다만 이 충돌은 계획 39 가 만든 것이 아니다.** 실측으로 확인했다 — `indexer.main` 은
`FileNotFoundError`(계획 21)·`NoCrawlDataError`·`StaleIndexError` 를 **이미 rc 2** 로
내고 있었고, `crawl.py:380` 의 `NoUsableSeedsError` 도 인자 **모양**이 아니라 인자
**내용**의 환경 오류인데 rc 2 다. 즉 이 저장소에서 rc 2 는 이미 "사람이 고칠 것" 이고
구분자는 stderr 문구다. 39 의 `DatabaseError` 는 그 관례에 **맞춰** 들어간 것이다.

**고치지 않은 이유**: 새 rc 값을 도입하면 `indexer`·`crawl`·`serve` 세 모듈과 계획
21·24·26·27·29 가 정한 계약을 한꺼번에 바꾸는 일이고, 이번 계획의 한도(제품 diff 는
`indexer.py` 한 파일)를 넘는다. 판단이 갈리는 자리라 **리뷰가 정한다.**

## 이번 계획이 하려는 일

**크롤이 도는 중에 색인을 돌리면 5초 만에 트레이스백이 난다.**
`store.py:22` 는 `sqlite3.connect(path, timeout=30)` 이고 주석이 이유까지 적어 뒀는데
(`실측에서 1,700문서째에 크롤을 죽인 게 이거다`, 계획 8), `indexer.py:78`·`136`·`181` 은
`sqlite3.connect(db_path)` 로 **timeout 을 안 줬다** — 기본 5.0초다. 같은 DB 에 붙는 두
모듈이 락을 **6배 다르게** 기다렸다. 계획 8 이 store 쪽에서 닫은 것의 **형제 구멍**이다.
그리고 `indexer.main` 에는 `sqlite3` 예외 갈래가 없어 rc **1** + 트레이스백이 됐다.

개발 두 스텝이 둘 다 닫았다 — 락 8초·20초 rc 0(스텝 1) · 락 35초 rc 2 · 비 DB 파일
rc 2 · 트레이스백 0줄(스텝 2). 테스트 phase 가 `--query` 진입점의 빈 자리를 메웠다.

## 다음 스텝 (리뷰)

**리뷰가 볼 자리 셋.**
① 위 `## 보류` 의 rc 2 충돌 — 계약을 바꿀지 문서에 적을지.
② **e2e 19종에 동시 실행 시나리오가 없다.** 락 갈래는 단위(예외를 세움) + 탐침(실물
35초)으로만 봤다. `indexer_e2e.py` 옆에 락 e2e 를 붙일지가 리뷰의 물음이다 — 붙이면
e2e 하나가 최소 8초를 쥐어야 의미가 있다(0.3초 락은 기본 5초가 받아줘 거짓 초록).
③ `_doc_count`(136)·`search`(181) 의 `timeout=30` 은 **단위 단언이 없다** — 죽인 변이는
`index_pages`(78) 경로를 지나는 것뿐이었다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 이번 스텝에서 대조함).
  탐침은 임시 디렉터리에서만, `cwd` 도 거기다 — 색인 경로가 cwd 기준이다.
- 단위 **461건**(테스트 phase 에서 +1)이 하나라도 줄면 RED · e2e 19종이 줄면 RED.
- `docs/digest.md` 열린 항목 **48**(`grep -c '^- \['`)이 줄면 RED · 189줄(상한 200).
- 제품 diff 는 `src/websearch/indexer.py` **한 파일**이다. 다른 `src/` 파일이 바뀌면 RED.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
