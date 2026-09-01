---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 201
updated: 2026-09-01
ctx: 85
night_iterations: 67
night_red: 0
night_retries: 0
---

# 현재 상태
**계획 40 `exit-code-contract` 테스트 1/1 완료 — 계약은 코드에서 전수였고, 계약을 적은
README 표가 거짓이었다.** 계획서 `docs/plan_exit-code-contract.md` ·
설계서 `docs/design_exit-code-contract.md` · 브랜치 `loop/exit-code-contract`(기점 `064e8a5`).
**계획 39 까지 전부 DONE·아카이브 완료.** 계획 34~37 은 PR #2 로 `main` 병합됨
(`main` 최신 `e0890c8`) — 38·39·40 의 `main` 병합은 사람이 정한다.

## 방금 한 것 (2026-09-01 · 테스트 1)

**새 테스트를 안 썼다.** 이 phase 는 빠뜨린 것을 찾고 전체를 돌리는 곳이라, 찾은 것 중
중요도 8 이상은 하나였고 그것은 테스트가 아니라 **문서**였다.

### ① 종료 코드 자리 전수 — 세는 단위를 `main` 의 반환값으로 잡았다

프로세스 rc 를 정하는 곳은 `sys.exit(main(sys.argv))` **3곳뿐**이다(`grep` 으로 확인).
그래서 `main` 의 반환값 **14개**가 계약의 전부다 — `indexer` 8(2·2·1·1·1·1·130·0) ·
`crawl` 7(2×6·130/0) · `serve` 4(2·2·1·0). 전부 단언이 붙어 있다.

### ② 변이 4종 추가 — rc 1 다섯 자리가 **5/5 사망**

`.git` 없는 스크래치패드 사본에서 **변이 전 462 OK 로 기준선을 먼저 찍고** 하나씩 심었다.

| 변이 | 자리 | 죽은 테스트 |
|---|---|---|
| M1(개발) | `indexer.py:245` | 1건 `test_missing_db_is_error_not_traceback` |
| M2 | `indexer.py:251` | 1건 `test_db_without_pages_is_error_not_traceback` |
| M3 | `indexer.py:256` | 1건 `test_cli_query_on_drifted_index...` |
| M4 | `indexer.py:265` | **3건** 락·비 DB·비 DB+질의 (한 `return` 이 두 갈래를 덮는다) |
| M5 | `serve.py:333` | 1건 `test_bind_failure_is_reported_instead_of_crashing` |

**아무 테스트도 안 붙들고 있는 rc 1 자리는 0곳이다.** 붙일 단언이 없었다.

### ③ 실측 — 세 CLI 를 진짜 프로세스로 15가지 상황에 돌렸다

전부 `cwd=<임시 디렉터리>`, 크롤 시드는 `127.0.0.1` 의 닫힌 포트(외부 네트워크 0).
**첫 탐침은 `data/` 를 사례끼리 공유해 오염됐다** — `crawl` 넷을 사례마다 새 디렉터리로
다시 쟀다(오염판은 "가져올 수 없는 시드 → rc 1" 이라는 거짓을 냈다. 실제는 2).

| 명령 | 상황 | rc |
|---|---|---|
| `indexer` | DB 없음 · pages 없음 · 손상 DB · 손상+`--query` | **1** ×4 |
| `indexer` | usage · `--query` 값 없음 | **2** ×2 |
| `serve` | **DB 없음 · 손상 DB** | **rc 없음 — 뜬다** |
| `serve` | usage · `--port` 범위 밖 | **2** ×2 |
| `serve` | 포트 점유 | **1** |
| `crawl` | 손상 DB · 쓸 수 없는 `data/` | **1**(트레이스백) |
| `crawl` | 가져올 수 없는 시드 / usage | **2** |
| `crawl` | 닿지 않는 시드 | **0**(수집 0 페이지 = 성공) |

### ④ 찾은 갭 — 8 이상은 하나, 그것은 `README` 였다

**[8] `README` 종료 코드 표가 `serve` 에 대해 거짓이었다.** 설계서 표에는 **"어디서" 칸**이
있었는데 README 로 옮기며 빠졌고, 남은 표는 *"세 명령이 같은 값을 쓴다"* 아래 rc 1 을
"DB 없음·…·포트 점유" 라고만 적어 `serve missing.db; echo $?` 가 1 을 낼 것처럼 읽혔다.
실제로는 **뜬 채로 요청마다 500** 이다. 칸을 되살리고 그 문장을 한 줄 덧붙였다(`README` 만).
**새 테스트는 안 붙였다** — 되살린 서술을 `TestMissingDb`(뜬 채 500·유출 없음)와
`test_bind_failure_is_reported_instead_of_crashing`(rc 1 은 bind 뿐)이 이미 붙들고 있다.
없는 것을 새로 쓰는 것이 아니라 있는 것을 가리키는 것이 맞았다(`test.md` 5절).

**[6] `crawl` 의 환경 오류는 값만 맞고 트레이스백이다** → `digest` 신설 항목.
제품 diff 한도가 `indexer.py` 한 파일이라 **안 고치고 넘겼다.**
**[5] `README` 의 rc 표 자체를 재는 검사가 없다** → 같은 항목에 함께 적었다.

## 다음 (리뷰 phase)

계획 40 은 개발·테스트가 끝났다. 리뷰가 볼 것 셋:
① `README` 표의 "어디서" 칸이 실제와 맞는지(위 ③ 표가 근거) ·
② `digest [6]`(crawl 트레이스백)을 이 계획에서 열지 말지 ·
③ **`docs/history_current.md` 가 299줄이다 — 회전이 이번엔 안 늦게 돌아야 한다**
(`digest ## 반복 실패` 가 네 번 적은 것). `digest.md` 도 200줄로 상한에 닿아 있다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — **확인함**).
- 단위 **462건**이 하나라도 줄면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **51**(`grep -c '^- \['`)이 줄면 RED · **200줄(상한 200)**.
  `[7]` 은 계획 40 이 DONE 될 때만 닫는다(그때 50).
- 제품 diff 는 **`src/websearch/indexer.py` 한 파일**이다. `crawl.py`·`serve.py` 가
  바뀌면 RED. 이 테스트 스텝의 diff 는 `README.md` + `docs/` 뿐 — `src/` **0줄**.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- **러너를 파이프로 감싸지 않는다**(`## 반복 실패` 2회 항목 — 이 반복에서 한 번 밟았다).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
