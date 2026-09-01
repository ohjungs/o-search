---
signal: GREEN
phase: 개발
step: 2
attempt: 0
iteration: 245
updated: 2026-09-02
ctx: 58
night_iterations: 97
night_red: 0
night_retries: 0
plan: db-open-atomic
---

# 현재 상태

**계획 47 `db-open-atomic` 을 열었다 — 계획서 `docs/plan_db-open-atomic.md`.**
계획 46 이 어제 세운 상태 코드 계약(400·404·500·503·`version`)에 **이미 뚫려 있던
구멍 둘**을 닫는다. 뿌리는 하나다 — `src/websearch/indexer.py` 가 **DB 가 있나** 를
보는 방식이다. 하나는 「보는 시점과 여는 시점이 갈라져 있다」(TOCTOU), 하나는
「보느냐 마느냐가 **질의 내용**에 달려 있다」. 제품 파일 **1개**(`indexer.py`) ·
새 e2e 파일 **0개** · 의존성 **0** · 스키마·`data/crawl.db` 무관.
**설계 끝났다 — `docs/design_db-open-atomic.md`(111줄). 개발 스텝 1/2 도 끝났다 —
`_connect()` 가 서고 세 호출부가 옮겨졌다. 다음 반복은 개발 스텝 2/2.**

## 방금 한 것 (2026-09-02 · 개발 phase 1/2)

**DB 를 여는 자리가 하나가 됐다.** `src/websearch/indexer.py` 에 `_connect(db_path)`
(`file:…?pathname2url…?mode=rw` URI · `timeout=30`)를 세우고 `index_pages`·`_doc_count`·
`search` 의 `os.path.exists` + `sqlite3.connect` 짝을 전부 그것으로 갈았다.
제품 **+31 / -8줄** · 파일 1개 · 의존성 0(`urllib.request` 는 stdlib).

**RED 를 눈으로 봤다 — 한 뿌리인데 증상이 셋으로 갈라져 나왔다.**

| 자리 | 고치기 전 (RED) | 고친 뒤 |
|---|---|---|
| `search` | 빈 DB 를 만들고 `[]` → **200** | `FileNotFoundError` → 503 · 파일 0 |
| `_doc_count` | 값은 0 인데 **빈 파일이 남는다** | 0 · 파일 0 (독스트링이 참이 됐다) |
| `index_pages` | 만든 빈 DB 에 `pages` 가 없어 `NoCrawlDataError` | `FileNotFoundError` · 파일 0 |

**변이 넷을 실제로 심어 죽는 것을 봤다** (제자리에 심고 즉시 원복 · `PYTHONDONTWRITEBYTECODE=1`).
M1 `mode=rw`→`rwc`: 신규 3건 + **기존 `test_missing_db_raises` 2건**까지 6실패.
M2 `pathname2url` 제거: `a b#c?d.db` 하나만 죽고 **한글 경로를 지나는 기존 테스트는 멀쩡**하다
(설계가 «인용 없이도 우연히 돌아간다» 로 적어 둔 그대로). M3 사후 `exists` 삭제: 디렉터리가
`FileNotFoundError`(→503)로 오분류돼 죽는다. M4 `_doc_count` 의 `except` 삭제: 2건. **넷 다 사망.**

**M2·M3 를 재는 두 건은 RED 를 안 지난다** — 오늘 코드에도 초록이라 «심어 보기» 말고는
이빨이 있는지 알 방법이 없었다. 새 갈래가 아니라 **새 구현이 열 수 있는 구멍**을 막는
단언이라 그렇다. 변이를 안 심었으면 장식 둘을 커밋할 뻔했다.

`serve.py` 는 **0줄** — `_connect` 가 던지는 것이 `FileNotFoundError`(→503)와
`sqlite3.OperationalError`(→500) 둘뿐이라 계획 46 의 번역표가 그대로 참이다.

## 계획서를 정정했다 — 스텝 둘 사이에 **엣지가 없다**

계획서(와 `index.md` 계획 47 행)는 *"엣지 하나 — ② 가 ① 의 산출물을 읽는다"* 로 적었지만
**의존이 아니다.** ① 은 `os.path.exists`+`connect` 짝을, ② 는 `if not match: return []` 의
**위치**를 건드리고 두 편집은 겹치지 않는다. 짝 검사(`digest [8]`)도 같이 답했다 —
**어느 하나만 고쳐도 회수가 0 이 아니다**(① 만 고치면 손상 DB + `q=%01` 이 그대로 200,
② 만 고치면 레이스가 그대로 빈 파일을 만든다). 둘 다 필요하고 **순서는 아무래도 좋다.**
각자 검증 가능하므로 **스텝은 2 로 그대로 두고 순서만 임의로 만든다** — 계획을 더
쪼갤 이유는 없다(갈림길 넷은 한계선이지 초과가 아니다).

## 계획 phase 가 남긴 것 (2026-09-02 · 탐색)

**착수 탐침을 먼저 돌렸다**(`digest` 의 `[7] 기록된 답을 실행 전에 다시 재라`).
`digest.md ## 판단 필요` 의 `[4]` 가 적어 둔 것은 **전부 참이었고 한 줄이 모자랐다.**

| 상황 | 질의 | `indexer.search` | 서버 |
|---|---|---|---|
| 손상 DB | `q=김치` | `DatabaseError` | 500 (계약대로) |
| **손상 DB** | **`q=%01`** | **`[]`** | **200** — 계약에 없는 갈래 |
| 없는 DB | 어느 질의든 | `FileNotFoundError` | 503 (안 샌다) |

**모자랐던 한 줄이 값을 바꿨다.** `exists` 와 `connect` 사이를 실제로 벌려 보니
`search()` 가 `[]`(→200)를 내는 것에 더해 **크기 0 의 빈 DB 파일을 그 자리에 만든다.**
`digest` 는 이 건을 *"창은 마이크로초 · 값은 낮다"* 로 적었는데 **흔적이 영구적**이다 —
빈 파일이 남으므로 그 뒤로 `os.path.exists` 가 계속 참이고 **503 은 다시는 안 난다.**
같은 창이 `_doc_count()` 의 독스트링(*"DB 파일을 만들지 않는다"*)도 거짓으로 만든다 —
세 자리(`index_pages`·`_doc_count`·`search`)가 한 뿌리라 **한 곳에서 고친다.**

**대안 셋의 함정까지 탐침이 냈다**(설계가 고른다). 대안 A(`?mode=rw` URI)는 원자적이고
파일을 안 만들지만, 경로를 날것으로 끼우면 **조용히 다른 파일을 연다** — `a b#c?d.db`
를 넣으니 `#` 뒤가 잘려 `a b` 라는 새 파일이 생겼고 `mode=rw` 는 통째로 무시됐다
(`urllib.request.pathname2url` 로 감싸면 옳다). 그리고 `OperationalError` 를 전부
번역하면 **권한 오류까지 503** 이 된다(지금은 500).

## 한도 (매 반복 확인)

- `main` 직접 커밋 금지 · `--no-verify` 금지 · 외부 네트워크 금지 ·
  `docs/specs/` 읽기만 · `data/crawl.db` 무변경 · 의존성 추가 금지(stdlib 만).
- **러너 호출에는 출력 조작을 아무것도 붙이지 않는다 — 파이프·`grep`·`tail`·
  `2>&1`·`2>/dev/null` 전부.** 직전 반복이 ⑭·⑮ 로 두 번 뚫렸다.
  **이번 반복 러너 호출 6회 · 출력 조작 0회** — 앞뒤로 `PYTHONPATH=src python3 -m
  unittest discover tests` 를 맨몸으로 한 번씩(**RED 3실패 → 501건 OK · 12.400초**),
  변이 4회는 `PYTHONDONTWRITEBYTECODE=1 … -m unittest tests.test_indexer` 를 맨몸으로.
  범위를 좁힌 것은 인자이지 출력 조작이 아니다 — 판정 줄은 여섯 번 다 통째로 봤다.
- 이번 반복 실측: 제품 `src/` **+31 / -8줄** · 새 파일 **1개**(`history_028.md` · 회전) ·
  의존성 0 · 변이 4회(전부 원복 · `git diff` 로 확인) · `data/crawl.db` 무변경 · 스키마 무변경.
- 기준선: 단위 **495 → 501건** · `e2e/*.py` **19종**(안 건드렸다) · p95 **8.71ms** ·
  품질 ko 20/20 · en 19/20 · 처리량 10.22/10.21/s · 디자인 4축.
- **README 카운트 가드가 이번 반복에 울었다** — 테스트 +6 에 `test_readme` 가 즉시
  FAILED. `README.md` 의 `단위 495건` → `501건` 한 곳만 고쳤다(`e2e/*.py` 19 그대로).
- `history_current.md` **회전 1회**(315 → 247줄 · `history_028.md`) · 아카이브 **28개** ·
  `digest.md` **198줄**(회전 요약 1줄 추가 + 스스로 «위 항목이 담고 있다» 라 적어 둔
  완료 항목 하나를 지워 200 아래로 되돌렸다 — `[4]` 는 계획이 닫을 때 지운다).

## 다음 — 개발 스텝 2/2 (DB 판정이 질의 내용을 안 따르게)

**어디서 시작하나**: `src/websearch/indexer.py` 의 `search()` 안 `match = _fts_query(query)` /
`if not match: return []`. 스텝 1 이 끝나 `db = _connect(db_path)` 가 그 **바로 아래**에 있다.

**할 일**: 조기 반환을 `db` 를 연 **뒤**로, 그리고 **옛 색인 검사(`sql != _CURRENT_SQL`) 뒤**로
옮긴다. 앞에 두면 옛 색인 + `q=%01` 이 `[]`→200 으로 새 나가 구멍이 절반 남는다(변이 M6).

**RED 로 먼저 볼 것** (`tests/test_indexer.py` · `tests/test_serve.py`):
손상 DB + `q=%01` → `sqlite3.DatabaseError` → **500**(기존 `test_corrupt_db_is_500_not_503`
옆에 붙인다) · 옛 색인 + `q=%01` → `StaleIndexError` → **503** · 정상 색인 + `q=%01` 은
**`[]` · 200 그대로**(이 갈래를 안 바꾸는 것이 계약이다 — `tests/test_serve.py` 에 이미 있다).

**비용은 재 뒀다 — 0.066ms/회**(무토큰 질의가 이제 DB 를 연다). p95 8.71ms · 예산 300ms 대비 무시 가능.

## 기점 — 원격 갈라짐은 닫혀 있다 (2026-09-02 확인)

`origin/main` 은 `494313b`(PR #5 병합). 계획 43·44·45·46 의 커밋들(`bc40ea9` 이후)이
아직 안 갔다. **남은 것 (사람 결정)**: 그것들을 `main` 으로 보내는 PR.
무인 모드는 병합하지 않는다 — **이 반복도 PR 을 안 열었다.**
**웹 UI 의 *Update branch* 는 여전히 누르지 않는다** — `main` 이 rebase-merge 로 해시가
새로 쓰인 뒤의 그것은 머지가 아니라 복제다(PR #3 을 깨뜨린 원인).
계획 47 의 기점은 `3d4eaba`(계획 46 DONE 커밋 · 현재 HEAD)이고 `main` 이 아닌 이유는
계획서 머리말에 적혀 있다 — `main` 기점이면 이 계획이 재는 503 계약 자체가 없다.

## 사람이 정할 것 — 넷이 열려 있다

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
   `NO_PAIR` 사유가 판단 보류를 적어 두고 있다.
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1). 그 배경은 `outline-offset` 이
   0 일 때만 링의 이웃이 되고, 검사기가 매 실행 offset > 0 을 확인한다(실측 2px).
3. **회전 규약이 저장소 밖 룰 파일과 갈린다** (리뷰 [B1], 2026-09-02). `digest.md` 는
   *"`## 완료` 첫 줄의 명부는 회전이 지우지 않는다"* 를 자기 주석에 적고 검사로
   강제하는데, `~/.claude/skills/loop-harness/rules/docs.md` 에는 그 예외가 없다.
   **저장소 밖이라 루프가 못 고친다.**
4. **«러너 호출에 출력 조작을 붙이지 않는다» 를 룰 파일에 못박는 일** (2026-09-02,
   계획 47 탐색이 후보 3 을 접으며 올렸다). 재발 **15회**이고 저장소 쪽 자리
   (`docs/project.md ## 명령`)에는 이미 적혀 있는데도 났다. 남은 자리는
   `~/.claude/skills/loop-harness/rules/` 이고 **저장소 밖이라 루프가 못 고친다.**

**사양이 사람에게 남긴 것 셋** (`docs/specs/concept.md` 의 `## 사람이 정할 것`):
속도 제한 시점(가정 IP 당 분당 60회) · JSON 검색과 근거 문단의 분할(가정 쪼갠다 —
**계획 46 이 그 가정을 따랐고 닫았다**) · 사양 숫자들이 초안이라는 것(90% · 500ms ·
60회/분). 첫째와 셋째는 아직 열려 있다.
