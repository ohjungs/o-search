---
signal: GREEN
phase: 설계
step: 1
attempt: 0
iteration: 198
updated: 2026-09-01
ctx: 52
night_iterations: 64
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 39 `indexer-lock` DONE · 계획 40 `exit-code-contract` 개설.**
계획서 `docs/plan_exit-code-contract.md` · 브랜치 `loop/exit-code-contract`
(기점 `064e8a5`, `loop/indexer-lock` 에서 팠다).
**계획 39 까지 전부 DONE·아카이브 완료** — 39 의 계획서는 `docs/plan_history_025.md`.
이 스텝의 `src/`·`tests/`·`e2e/` diff 는 **0줄**이다(문서·계획만).
계획 34~37 은 PR #2 로 `main` 에 병합됐다(`main` 최신 `e0890c8`) — 38·39·40 의
`main` 병합은 사람이 정한다.

## 방금 한 것 (2026-09-01 · 계획 40)

### ① 계획 39 를 DONE 으로 마감했다

`git mv docs/plan_indexer-lock.md docs/plan_history_025.md`(계획 38 이
`plan_history_024.md` 로 간 것과 같은 방식) · 계획서 머리를 **DONE** 으로 ·
`docs/index.md` 39행을 진행 → **완료**로 + `DONE(2026-09-01) · 계획서 plan_history_025.md`.

**옛 경로(`plan_indexer-lock.md`) 인용은 남겨 둔다** — `history_current.md` 의
그때 기록은 당시엔 참이었고, 아카이브 기록을 소급 수정하지 않는 것이 관례다
(계획 38 마감이 같은 판단을 했다, `git show 1cd3958`).

### ② discover 를 1~8순위로 돌렸다 — **6순위에서 나왔다**

1~5순위 **전부 0건**(실측): 단위 **462건 OK · 11.883초** · 린터/타입체커 없음 ·
`src`·`tests`·`e2e` 의 `TODO`/`FIXME`/`HACK` **0건** · `docs/candidates.md` 없음
(`scripts/` 디렉터리 자체가 없다) · `digest.md ## 보류` 비어 있음.

**6순위 `## 다음 계획 후보` 의 `[7]`** — 세 CLI 의 종료 코드 계약이 갈렸다.
6순위의 나머지는 전부 걸러진다(종속 1 · 저장소 밖 룰 1 · 값 낮음/안 고치는 게 답 2 ·
도달 불가·천장 수용 4). 왜 걸렀는지는 계획서 2절에 항목별로 적었다.

### ③ 착수 탐침이 근거 항목의 진술 **둘을 정정했다**

`[7]` 은 계획 39 리뷰의 **백지 패스**가 쓴 것이라 전수가 아니었다 — 39 자신이
"백지 패스의 근거는 전수 조사가 아니었다" 로 열린 계획인데, 그 리뷰가 남긴 후보도
같은 자리에서 틀렸다.

- **"세 모듈짜리 계획" 이 아니라 둘이다.** `crawl.main` 에는 환경 오류 갈래가 **0개**다.
  `[7]` 이 환경으로 센 `crawl.py:380 NoUsableSeedsError` 는 `crawl.py:25-32` docstring 이
  **사용자 입력 오류(rc 2)** 라고 이유까지 적어 뒀다("0페이지 수집과 다르다").
  → `crawl` 은 이미 계약을 지킨다. 갈린 것은 `indexer` 와 `serve` 뿐이다.
- **`serve` 의 rc 1 을 고정하는 단언이 0건이다.** `grep "serve.main" tests/*.py e2e/*.py`
  에 rc 1 을 재는 자리가 없다 — **관례로 인용된 값을 아무도 안 붙들고 있다.**
  계획 39 리뷰가 `_doc_count`·`search` 의 `timeout=30` 에서 잡은 것과 같은 모양이다.

실측 rc(임시 디렉터리, `cwd` 도 거기): 없는 DB **2** · 비 DB 파일 **2** · 무인자 2 ·
`serve --port 80` 특권 포트 **1** · `file://` 시드 2.
바꾸면 움직이는 단언 전수: **7곳**(`test_indexer.py` 환경 6 + `tokenizer_e2e.py:153` 1).
`test_crawl.py` 의 rc 2 단언 7건은 전부 인자라 **안 움직인다**.

## 다음 스텝 (설계 1)

**설계가 필요하다** — `rules/plan.md` 6-1 트리거에 걸렸다. 대안이 셋이고 서로 다른
것을 희생한다: **A** 환경 오류를 rc 1 로 모은다(단언 7곳 이동, `README.md:28` 과 맞다) ·
**B** `serve` 를 rc 2 로 내린다(제품 1줄, 대신 `README.md:28` 이 거짓이 되고
`serve.py:329-333` 의 근거를 지운다) · **C** 재시도 가능(락)만 별도 코드로 가른다
(문제의 절반을 정면으로 풀지만 계약 값이 하나 는다). A 와 C 는 배타적이지 않다.

설계 문서는 `docs/design_exit-code-contract.md`. 답할 것 셋은 계획서 6절에 적었고,
셋째가 **자기 대조**다 — 39 의 근거가 백지 패스라 틀렸으니 이 계획의 근거(2-1 ①)도
설계가 한 번 더 확인한다.

**7절 e2e 는 미정이다** — 무엇을 e2e 로 잴지가 대안 선택에 달렸다. 대신 판정 기준을
계획 시점에 못박았다(프로세스 경계·진짜 OS 자원이 필요하면 붙인다, 목으로 세워지면
단위로 끝낸다) — 계획 39 가 쓴 것과 같은 기준이다.

**곁가지**: 계획 39 리뷰 중 자동 스냅샷 훅이 만든 `9f034eb` 는 그대로 둔다
(저장소 밖 훅) — `digest.md ## 반복 실패` 의 스냅샷 훅 항목에 **네 번째 사례**다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 이번 스텝에서 대조함).
  탐침은 임시 디렉터리에서만, `cwd` 도 거기다 — 색인 경로가 cwd 기준이다.
- 단위 **462건**이 하나라도 줄면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`)이 줄면 RED · 191줄(상한 200).
  `[7]` 은 계획 40 이 DONE 될 때만 닫는다(그때 49).
- 제품 diff 는 설계가 지목한 **한 파일**이다. `src/websearch/crawl.py` 가 바뀌면 RED.
- 변이는 `.git` 없는 스크래치패드 사본에서만 심는다(`## 반복 실패` 3회 항목).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
