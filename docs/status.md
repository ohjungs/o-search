---
signal: GREEN
phase: 설계
step: 1
attempt: 0
iteration: 203
updated: 2026-09-01
ctx: 62
night_iterations: 68
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 40 `exit-code-contract` DONE · 계획 41 `crawl-db-guard` 개설.**
계획서 `docs/plan_crawl-db-guard.md` · 브랜치 `loop/crawl-db-guard`
(기점 `8a99617`, `loop/exit-code-contract` 에서 팠다).
**계획 40 까지 전부 DONE·아카이브 완료** — 40 의 계획서는 `docs/plan_history_026.md`,
설계서는 `docs/design_history_026.md`.
이 스텝의 `src/`·`tests/`·`e2e/` diff 는 **0줄**이다(문서·계획만).
계획 34~37 은 PR #2 로 `main` 에 병합됐다(`main` 최신 `e0890c8`) — 38·39·40·41 의
`main` 병합은 사람이 정한다.

## 방금 한 것 (2026-09-01 · 계획 41)

### ① 계획 40 을 DONE 으로 마감했다

`git mv docs/plan_exit-code-contract.md docs/plan_history_026.md` ·
`git mv docs/design_exit-code-contract.md docs/design_history_026.md`
(계획 34 가 `plan/design 021` 을 함께 민 것과 같은 방식 — 번호는 계획서와 설계서가 공유한다) ·
계획서 머리를 **DONE** 으로 · `docs/index.md` 40행을 진행 → **완료**로 ·
`digest.md` `[7]`(세 CLI 종료 코드 계약이 갈렸다)을 **닫았다 → 열린 항목 51 → 50**.

**옛 경로 인용은 남겨 둔다** — `history_current.md` 반복 198~202 와
`design_history_026.md` 머리의 `plan_exit-code-contract.md` 인용은 당시엔 참이었고,
아카이브 기록을 소급 수정하지 않는 것이 관례다(계획 38·39 마감과 같은 판단).
살아 있는 문서인 `index.md` 의 설계서 인용만 새 이름으로 고쳤다.

**계획 40 이 남긴 것**: `crawl` 의 환경 오류는 값(rc 1)만 맞고 여전히 트레이스백이다.
제품 diff 한도(`indexer.py` 한 파일) 밖이라 `digest [6]` 으로 넘겼고 — **그것이 계획 41 이다.**

### ② discover 를 1~8순위로 돌렸다 — **6순위에서 나왔다**

1~5순위 **전부 0건**(실측): 단위 **462건 OK · 11.925초** · 린터/타입체커 없음 ·
`src`·`tests`·`e2e` 의 `TODO`/`FIXME`/`HACK` **0건** · `docs/candidates.md` 없음
(`scripts/` 디렉터리 자체가 없다) · `digest.md ## 보류` 비어 있음.

**6순위 `## 다음 계획 후보` 의 `[6]`** — *"`crawl` 환경 오류는 값만 맞고 트레이스백을
그대로 낸다"*(2026-09-01 계획 40 테스트 실측). **7순위도 같은 자리를 가리킨다** —
`## 반복 실패` 의 닫힌 항목 *"CLI 가 예상 못 한 입력에 트레이스백을 낸다"* 는
*"착수 때 셋을 다 탐침하니 `crawl.main` 은 이미 막고 있었다"* 며 닫혔는데,
**그 탐침이 인자 오류만 봤다.** 같은 원인의 세 번째다.
6순위의 나머지 8개를 왜 걸렀는지는 계획서 2절에 항목별로 적었다
(종속 1 · 저장소 밖 룰 1 · 값 낮음/안 고치는 게 답 2 · 도달 불가 1 · 천장 수용 3).

### ③ 착수 탐침이 근거 항목의 처방을 **넓혔다**

`[6]` 은 *"`except sqlite3.Error` 갈래를 하나 더는 일"* 이라고 적었다. **열거가 덜 됐다** —
네 상황 중 하나는 `sqlite3` 가 아니라 `os.makedirs` 의 `FileExistsError` 다.

실측(임시 디렉터리, `cwd` 도 거기 — `crawl` 은 `cwd` 밑에 `data/` 를 만든다):

| 상황 | 새어 나온 예외 | 던진 곳 | rc | stderr |
|---|---|---|---|---|
| `data/crawl.db` 가 비 DB 파일 | `sqlite3.DatabaseError: file is not a database` | `store.py:23` | **1** | **14줄** |
| `data/` 쓰기 불가(`chmod 500`) | `sqlite3.OperationalError: unable to open database file` | `store.py:22` | **1** | **14줄** |
| `data` 가 일반 파일 | `FileExistsError: [Errno 17]` | `store.py:19` | **1** | **16줄** |
| `data/crawl.db` 가 디렉터리 | `sqlite3.OperationalError` | `store.py:22` | **1** | **14줄** |
| 대조군 — 닿지 않는 시드 | 없음 | — | **0** | 0줄 |

**계획 40 이 배운 것과 같은 모양이다** — 설계서의 "전수 7곳" 이 여덟째를 빠뜨린 것은
단언의 *문법형*을 안 세어서였고, 이번엔 *예외 타입*이 그 자리다.

`crawl` 의 **환경** 오류를 붙들고 있는 단언은 `tests/`·`e2e/` 에 **0건**이다
(`test_crawl.py` 의 `..._not_traceback` 세 건은 전부 인자 오류다).

### ④ 곁가지 — 자동 스냅샷 훅이 반복 중간에 커밋·푸시했다 (`b919e68`)

마감 작업의 **절반**(`git mv` 둘 + `index.md` + `digest.md`)이 그 커밋에 실려 갔다.
갓 판 로컬 브랜치라 접을 수 있어 보였지만 **훅이 브랜치까지 원격에 만들어**
이미 `origin/loop/crawl-db-guard` 가 있었다 — 전례대로 되감지 않고 앞으로 커밋했다.
**한 스텝이 두 커밋으로 갈렸다.** `digest ## 반복 실패` 의 스냅샷 항목을 **3회 → 5회**로
올렸다(계획 39 리뷰의 `9f034eb` 가 안 세어져 있어 ④로 함께 넣었고, 200줄은 압축으로 유지).
저장소 밖 훅이라 근본 원인은 여전히 못 고친다.

**한도도 하나 밟았다** — 러너를 `| tail -3` 과 `| grep -E ...` 로 **두 번** 감쌌다
(둘 다 맨몸으로 다시 돌려 462 OK 확인). `digest ## 반복 실패` 를 **3회 → 4회**로 올렸다.
계획 40 리뷰가 *"조항을 자기 손으로 적어 놓고 밟았다"* 고 쓴 **바로 다음 반복**이다.

## 다음 스텝 (설계 1)

**설계가 필요하다** — `design.md` 1절의 "대안이 2개 이상 갈린다" 에 걸렸다.
값은 안 바뀌고 바뀌는 것은 stderr 한 줄인데, **그물의 폭과 자리가 갈린다**:
**A** `main()` 이 `crawl(...)` 을 통째로 감싼다(가장 짧지만 크롤 도중의
`store.upsert` 실패까지 "DB 를 열 수 없다" 로 덮는다 — `crawl.py:315` 는 메인 스레드다) ·
**B** `Store.__init__` 이 도메인 예외를 던지고 `main()` 이 그것만 잡는다(그물이 정확하지만
`Store` 의 공개 계약이 바뀐다) · **C** `crawl()` 안에서 `Store(db_path)` 한 줄만 감싼다.
직교 물음 둘: 안내가 **DB 경로를 부르는가**(`main()` 은 경로를 모른다 —
`db_path` 는 `crawl()` 의 기본 인자다) · **락을 따로 안내하는가**(`indexer.py:262` 는 가른다).

설계 문서는 `docs/design_crawl-db-guard.md`. 답할 것 넷은 계획서 6절에 적었다.

**7절 e2e 는 미정으로 두지 않았다** — 계획 40 리뷰가 *"계획서가 스스로 되받아 적어라
고 적어 둔 7절이 세 반복째 비어 있었다"* 를 잡았으므로 **잠정 판정을 계획 시점에 적었다**:
**새 e2e 0개**(재는 것은 `main(argv)` 의 반환값과 stderr 이고, 진짜 OS 자원은
`tempfile`+`chmod` 로 단위 안에서 세워진다). 반증 신호도 함께 적었다.
설계가 확인하거나 정정해서 되받아 적는다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 이번 스텝에서 대조함).
- **탐침은 임시 디렉터리에서만, `cwd` 도 거기다** — 이 계획은 특히 그렇다.
  `crawl` 은 `cwd` 밑에 `data/` 를 만들고 거기 쓴다. `chmod 500` 으로 만든 디렉터리는
  탐침 끝에 반드시 되돌린다.
- 단위 **462건**이 하나라도 줄면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`)이 줄면 RED · **200줄(상한 200)**.
  `[6]` 은 계획 41 이 DONE 될 때만 닫는다(그때 49). 항목을 더하려면 먼저 압축한다.
- 제품 diff 는 **설계가 지목한 파일**이다. `src/websearch/indexer.py`·`serve.py` 가
  바뀌면 RED. `crawl.py` 는 확정, `store.py` 는 설계가 B 를 고를 때만.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- **러너를 파이프로 감싸지 않는다**(`## 반복 실패` 3회 항목 — 계획 40 이 세 번째로 밟았다).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
