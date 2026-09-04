# 계획 53 — `passage-db-state`

**`/passages` 는 DB 상태를 500 으로 내고, 그 판정이 질의 내용에 달려 있다.**
`pages` 테이블이 사라진 DB(색인 `docs` 는 살아 있다)에 매치되는 질의를 보내면
`indexer.passages()` 의 `SELECT html FROM pages` 가 `sqlite3.OperationalError` 로
터져 `serve` 의 `except Exception` → **500** 이 나간다. 그런데 **매치가 없는 질의**를
같은 DB 에 보내면 그 SELECT 까지 못 가서 **200 `{"passages": []}`** 다 — 같은 DB
같은 순간에 소비자가 받는 답이 «우리가 터졌다» 와 «근거가 없다» 로 갈린다.

- **슬러그**: `passage-db-state`
- **브랜치**: `loop/passage-db-state`
- **기점**: `a4a4da1` (`loop/focus-ring-combinator` 의 HEAD · 계획 52 DONE 문서까지)
- **기점을 `main` 으로 안 잡은 이유**: 이 반복이 원격을 직접 다시 읽었다 —
  `git ls-remote origin loop/focus-ring-combinator` 가
  `a4a4da12f9ec96a3b9a519eb36cf9d03147d47a8` 로 로컬 `HEAD` 와 같고,
  `git ls-remote origin main` 은 `687a1598cbef66b68ca000634fe3a2de068d8e5e`(계획 47)다.
  `gh pr list` 는 PR **#7**(`loop/merge-48-50` → `main`)이 **OPEN · `mergedAt: null`** 이다.
  계획 48~52 는 아직 원격 `main` 에 없고, `README.md` 의 `단위 593건`·`e2e 21종` 과
  `tests/test_readme.py` 의 건수 단언이 이 기점에 맞춰져 있어 `main` 에서 따면 첫
  커밋부터 RED 다. **PR #7 은 안 건드린다** — 병합은 사용자 몫이다.
- **phase**: 설계 (트리거 셋이 걸린다 — 6절)
- **스텝**: 1개
- **시작**: 2026-09-04 (반복 309)

## 1. 문제 · 목표 · 기대 결과

### 문제

`indexer.passages()`(`src/websearch/indexer.py:274`)는 `search()` 로 문서를 고른 뒤
**연결을 하나 더 열어** 문서마다 `SELECT html FROM pages WHERE url = ?` 를 친다.
`pages` 테이블 자체가 없으면 그 SELECT 가 `sqlite3.OperationalError` 를 내고,
`serve.do_GET` 의 사다리에서 `FileNotFoundError`·`StaleIndexError` 어느 쪽도 아니라
`except Exception` 으로 떨어져 **500 «검색 중 오류가 났다»** 가 나간다.

고장이 둘이다.

1. **신호가 틀렸다.** `pages` 가 없는 상태는 «크롤한 적 없는 DB 이거나 남의 DB» 이고
   (`indexer.NoCrawlDataError` 의 docstring 이 그렇게 적었다) 크롤·색인을 다시 돌리면
   낫는다. 500 은 «재시도하지 마라» 라 인프라에게 틀린 말을 한다. `README.md:40` 이
   *"낫는 상태(DB 파일 없음·옛 색인)에는 **503**, 그 밖의 오류에는 500"* 이라고
   계약으로 적어 뒀는데 이 상태가 그 목록에 없다.
2. **판정이 질의 내용에 달렸다.** `hits` 가 비면 루프가 한 번도 안 돌아 SELECT 에
   닿지 않는다 — 같은 고장난 DB 가 `q=김치찌개` 면 500, `q=zzzznope`·`q=%01` 이면
   200 `[]` 다. 이것은 계획 47 `db-open-atomic` 이 `search()` **안**에서 닫은 고장과
   글자 그대로 같은 것이다. `indexer.py:246-249` 가 그 자리에 남긴 주석이 원칙을
   못박아 뒀다: *"무토큰 질의의 조기 반환은 **DB 상태 판정 뒤**다. 앞에 두면 판정이
   질의 내용에 달린다."* 그 원칙이 함수 하나 건너에서 안 지켜지고 있다.

### 목표

`passages()` 가 `pages` 를 읽기 전에 **DB 상태를 먼저 판정**하게 한다 —
`pages` 가 없으면 `NoCrawlDataError`, 그리고 그 예외가 `/passages` 에서 **503** 으로
나가게 한다. 판정은 `hits` 가 비었든 찼든 **같은 자리에서 같은 답**을 낸다.

### 기대 결과

- `pages` 없는 DB: `/passages` 가 질의 3종(매치 있음 · 매치 없는 낱말 · 무토큰)
  **전부 503**. 오늘은 500 / 200 / 200 이다.
- 정상 DB 대조군 3종은 **200 · 오늘과 같은 본문** (오탐 0).
- 같은 DB 의 `/search` 는 **200 무변** — 색인만으로 되는 검색을 안 깬다.
  «두 경로가 다른 답을 낸다» 를 «둘 다 200» 으로 접지 않는다(6절 갈림길 1).
- 제품 diff 는 `src/websearch/indexer.py` · `src/websearch/serve.py` 두 파일.
  스키마·재색인·마이그레이션 **0**.

### 무엇이 이미 참인가 (이 저장소를 처음 여는 사람을 위한 전제)

- **같은 가드가 이미 이 파일에 있다.** `indexer.index_pages()`
  (`src/websearch/indexer.py:142-145`)가 읽기 직전 한 번
  `SELECT 1 FROM sqlite_master WHERE type='table' AND name='pages'` 를 보고
  없으면 `NoCrawlDataError` 를 낸다. 새 관용구를 만들 필요가 없다(ponytail 2칸).
- `NoCrawlDataError` 는 `indexer.py:88` 에 이미 있고 docstring 이 원칙을 적었다 —
  *"«크롤 데이터가 없다» 와 «크롤했는데 색인할 게 0건» 은 다른 상태라 0 으로 합치지
  않는다. 합치면 DB 경로를 잘못 준 것이 조용한 성공으로 보인다."*
- `indexer.main` 은 `NoCrawlDataError` 를 이미 잡아 복구법을 찍고 rc 1 을 낸다
  (`indexer.py:371`). CLI 쪽은 손댈 것이 없다.
- **`serve` 의 503 튜플에는 `NoCrawlDataError` 가 없다.** JSON 사다리
  `serve.py:281` 은 `except (FileNotFoundError, indexer.StaleIndexError)` 이고
  화면 사다리 `serve.py:323` 도 같은 튜플이다. **후보가 적어 둔 처방
  («`passages()` 가 `NoCrawlDataError` 를 쓰면 된다»)만으로는 여전히 500 이다** —
  이 계획이 처방을 다시 재서 찾은 절반이다(3절).
- `passages()` 는 **문서 단위**로는 이미 «원본이 사라진 문서는 지어내지 않고 뺀다»
  (`indexer.py:303`, `continue`)를 한다. 이 계획이 여는 것은 «테이블 자체가 없다» 로,
  그 규칙의 극한을 같은 답(빈 목록)으로 접을지 다른 답(503)으로 가를지가 6절 갈림길 1 이다.
- `/passages` 의 상태 코드는 계획 46 `json-contract` 가 계약으로 만든 표면이고
  `docs/specs/concept.md:135`(디자인 5)가 *"HTTP 상태 코드가 뜻을 갖는다
  (400 질의가 틀렸다 · 503 색인이 없다)"* 로 사양에 적어 뒀다.

## 2. 근거

- `docs/digest.md` `## 다음 계획 후보` 의
  **[5] `pages` 테이블이 없으면 `/search` 는 200, `/passages` 는 500 이다**
  (2026-09-02 계획 48 리뷰 4 가 백지 패스 지적을 재측해 확인). 탐색 6순위.
- 탐색 1~5순위는 오늘 **0건**이다(3절에 실측을 적었다).
- `README.md:40` 의 상태 코드 계약에 이 상태가 빠져 있다.
- `docs/specs/concept.md:135` 디자인 5 — 상태 코드가 뜻을 갖는다.

## 3. 계획 phase 가 오늘 직접 잰 것 (2026-09-04 · 반복 309)

### 탐색 1~5순위 — 전부 0건

| 순위 | 출처 | 실측 |
|---|---|---|
| 1 | 실패하는 테스트 | `PYTHONPATH=src python3 -m unittest discover -b tests` → **`Ran 593 tests in 13.493s` OK**(맨몸·단독) |
| 2 | 타입·린트 에러 | 이 저장소에 타입체커·린터 설정 0개 (stdlib 전용) |
| 3 | 코드의 `TODO`/`FIXME`/`HACK` | `src/`·`e2e/`·`tests/` 전수 **1건**이고 그것은 `tests/test_indexer.py:758` 의 **HTML 문자열 안 fixture**(`"<p>김치찌개 <!-- TODO: <a href=x> 옛 링크"`)다 — 코드가 아니다 |
| 4 | `docs/candidates.md` | 파일 없음 |
| 5 | `digest.md` 보류(승인 대기) | 절이 주석 하나뿐 — **0건** |

### 중복 방지 (discover 5절) — `index.md` 전수 대조

`docs/index.md` 의 계획 표 전체 + `## 사양 분할` 번호 목록(1~37 + 확장 9~11)을
`digest.md` 의 후보·판단 필요 목록과 전수 대조했다. 겹치는 것 0. 진행 중 계획 0
(`docs/plan_<슬러그>.md` 는 아카이브 38개뿐) · `docs/patches/` 없음.

**「취소선만 안 그어진 완료 항목」을 하나 찾았다.** `digest.md` `## 다음 계획 후보` 의
**[6] `focus_rule` 은 규칙이 *어디에* 있고 셀렉터의 *극성*이 무엇인지는 아직 안 본다**
(계획 44 리뷰)는 오늘 기준 **네 갈래 ⓐⓑⓒⓓ 가 전부 닫혀 있다** —
`e2e/design_check.py` 의 조건 6(중괄호를 세서 at-rule 밖인지 본다, `:200·275-280`)이
ⓐⓑ 를, `INDIRECT_RE`+`FOCUS_RE` 낱말 매칭(`:196-199, 270-272`)이 ⓒⓓ 를 닫았다
(계획 49 `focus-rule-scope`). 점수가 6 이라 후보 목록에서 가장 높은 축에 있는데
**할 일이 남아 있지 않다.** 이번 반복은 그것을 근거로 삼지 않았고, `digest.md` 에
취소선과 닫은 계획을 적어 다음 탐색이 같은 함정에 다시 걸리지 않게 했다.

### 후보의 처방을 다시 쟀다 — **절반이었다**

후보가 적은 처방은 *"`indexer` 에 `NoCrawlDataError` 가 이미 있는데 `passages()` 는
안 쓴다 — 쓰면 503 이 맞는 자리다"* 였다. 실측하니 **`passages()` 만 고치면 여전히
500 이다**: `serve.py:281` 의 503 튜플이 `(FileNotFoundError, indexer.StaleIndexError)`
라 `NoCrawlDataError` 는 그 아래 `except Exception` 으로 떨어진다. 처방은 한 곳이
아니라 **두 곳**이다. digest `[7]` 「기록된 답을 실행 전에 다시 재라」의 다섯 번째
적용이다(계획 41·44·51·52 에 이어).

### 고장을 프로세스 밖에서 쟀다 (탐침 `scratchpad/probe_http2.py`)

`store.upsert` → `indexer.index_pages` 로 1문서 DB 를 만들고 `DROP TABLE pages` 한 뒤
`python3 -m websearch.serve <db> --port N` 을 실제로 띄워 HTTP 로 물었다.

| 질의 | 정상 DB(대조군) | `pages` 없음 |
|---|---|---|
| `q=김치찌개` (매치 있음) | 200 · `passages` 1건 | **500** `{"error":"검색 중 오류가 났다"}` |
| `q=zzzznope` (매치 없는 낱말) | 200 · `[]` | **200 · `[]`** |
| `q=%01` (무토큰) | 200 · `[]` | **200 · `[]`** |
| `GET /search?q=김치찌개` | 200 | **200**(결과 1건 — 색인은 멀쩡하다) |

프로세스 **안**에서도 확인했다: `indexer.passages(db, "김치찌개")` →
`sqlite3.OperationalError: no such table: pages` · `indexer.passages(db, "\x01")` → `[]`.

**후보가 안 적은 절반이 이 표의 2·3행이다** — 후보는 «매치 있는 질의의 500» 만
적었고, 판정이 질의 내용에 달린 것은 아무도 안 쟀다. 그것이 이 계획의 무게를 올린다:
고칠 것이 «틀린 코드 하나» 가 아니라 «계획 47 이 닫은 고장의 형제» 다.

## 4. 스텝 (그래프)

노드가 하나다 — 그리지 않는다. 세 편집(가드 · 503 튜플 · 계약 문서)이 **같은
관측 하나**(`/passages` 가 503 을 낸다)로만 검증되므로 쪼개면 중간 상태가 검증
불가다(가드만 넣으면 500 그대로, 튜플만 넣으면 아무 일도 안 일어난다).

### 스텝 1/1 — `passages()` 가 `pages` 를 읽기 전에 DB 상태를 판정한다

- `src/websearch/indexer.py` — `passages()` 의 `_connect(db_path)` **직후**,
  `hits` 루프 **앞**에 `pages` 존재 검사. `index_pages` 가 쓰는 것과 같은
  `sqlite_master` 질의이고 같은 `NoCrawlDataError` 를 낸다. 자리가 루프 앞인 것이
  요점이다 — 그래야 판정이 `hits` 의 비어 있음에 안 달린다.
- `src/websearch/serve.py` — JSON 사다리의 503 튜플에 `indexer.NoCrawlDataError`.
  화면 사다리도 같이 넣을지는 설계가 판정한다(6절 갈림길 3).
- `README.md` — 상태 코드 계약 줄(40행)에 이 상태를 더한다.
- `tests/test_indexer.py` · `tests/test_serve.py` — 5절의 관측을 단언으로.

## 5. 완료 기준 (대칭으로 잰다)

전부 **오늘 실측한 값과 짝**이다. 왼쪽이 오늘, 오른쪽이 목표다.

1. `pages` 없는 DB · `q=김치찌개` → `/passages` **500 → 503**,
   본문 `{"version":1,"error":"색인이 아직 준비되지 않았다"}`.
2. `pages` 없는 DB · `q=zzzznope` → **200 `[]` → 503**.
3. `pages` 없는 DB · `q=%01`(무토큰) → **200 `[]` → 503**.
   (2·3 이 «판정이 질의 내용에 안 달린다» 를 재는 유일한 축이다.)
4. **정상 DB 대조군 3종 무변**: 200 · `passages` 1건 / 200 `[]` / 200 `[]`.
   오탐 0 — 이 계획의 최대 위험이 여기다(8절).
5. `pages` 없는 DB · `GET /search?q=김치찌개` → **200 무변**(결과 1건).
6. `indexer.passages()` 가 내는 예외가 `sqlite3.OperationalError` → **`NoCrawlDataError`**.
7. 단위 **593 → 593+N `OK`**(맨몸·단독, 파이프·리다이렉션 0).
   건수가 바뀌므로 `README.md` 의 `단위 593건` 과 `tests/test_readme.py` 의 건수
   단언을 **같은 커밋에서** 맞춘다.
8. **e2e 21종 전수 rc 0** · `e2e/passage_eval.py` 의 정확도 **100.0%** · 채택률
   **99.5%** · HTTP p95 예산 안 — 세 숫자 무변.
9. 제품 diff 는 `src/websearch/indexer.py`·`src/websearch/serve.py` **두 파일뿐** ·
   `data/crawl.db` sha256 무변 · `docs/specs/` 무변.
10. **변이 둘이 죽는다**: ① 가드 삭제 → 1·2·3 을 재는 단언 RED ·
    ② 503 튜플에서 `NoCrawlDataError` 제거 → 1 을 재는 단언 RED.
    변이는 `.git` 없는 스크래치패드 사본에서 돌리거나 `touch .mutation-lock` 후 삭제한다.

## 6. 설계가 필요하다 — 트리거 셋이 걸린다

1. **공개 인터페이스 변경** — `/passages` 의 상태 코드는 계획 46 `json-contract` 가
   계약으로 만든 표면이고 `README.md:40` 이 문서로 갖고 있다. 500 → 503 은 소비자가
   재시도할지를 가르는 값이다.
2. **3개 이상 파일에 걸침** — `indexer.py` · `serve.py` · `README.md` · 테스트 둘.
3. **대안이 2개 이상 갈린다** — 아래 셋이 전부 «어느 쪽이든 동작하지만 결과가 다름» 이다.

- **갈림길 1 — 503 이냐 200 `[]` 이냐.** `passages()` 는 문서 단위로는 이미 «원본이
  사라진 문서는 뺀다»(`indexer.py:303`)를 하므로 «테이블 째로 사라졌다» 를 그 규칙의
  극한으로 보고 200 `[]` 를 내는 것도 일관된 답이다. 반대편 근거는 `NoCrawlDataError`
  docstring 의 «0 으로 합치면 DB 경로를 잘못 준 것이 조용한 성공으로 보인다» 와
  `README.md:40` 의 계약이다. **말로 고르지 않는다** — 설계가 «소비자가 두 상태를
  구별해야 하는가» 를 표로 재서 고른다.
- **갈림길 2 — 가드를 `passages()` 안에 두나 `_connect()` 에 두나.** `_connect` 에
  두면 `search()` 까지 걸려 완료 기준 5(색인만으로 되는 검색)가 깨진다. 지금 판단은
  `passages()` 안이지만, 그러면 `index_pages` 와 **같은 세 줄이 두 곳**이 된다 —
  헬퍼로 뽑을지가 설계 몫이다(ponytail: 두 곳이면 뽑을 값이 아직 얇다).
- **갈림길 3 — 화면 사다리(`serve.py:323`)의 503 튜플도 같이 넓히나.** `_page_hits`
  → `search()` 는 `NoCrawlDataError` 를 안 내므로 오늘은 **닿을 수 없는 코드**다.
  넣으면 두 사다리가 대칭이고 안 넣으면 죽은 코드가 없다. 설계가 근거를 적고 고른다.

## 7. 하지 않을 것 (범위 고정)

- **`/search` 의 200 을 안 바꾼다.** `docs` 색인이 살아 있으면 검색 결과는 정직하다.
  후보가 적은 «두 경로가 다른 답을 낸다» 를 «둘 다 죽인다» 로 읽지 않는다.
- **스키마·재색인·마이그레이션 0.** `data/crawl.db` 를 안 건드린다.
- **`pages` 는 있는데 행이 없거나 `html` 이 빈 문서**는 오늘대로 문서 단위 `continue`.
- **`docs` 가 아직 없는 DB(색인 전)** 의 갈래는 안 건드린다 — `search()` 가 `[]` 를
  내는 오늘 동작 그대로다.
- **`e2e/passage_eval.py` 와 코퍼스는 안 건드린다.** 정확도·채택률은 회귀 축이다.
- **`docs/specs/` 는 읽기 전용.**
- **PR #7 무접촉** — `loop/merge-48-50` 은 OPEN 이고 병합은 사용자 몫이다.
- 새 e2e 스크립트를 만들지 않는다. 21종이 이미 있고 이 계획의 관측은 단위와
  e2e phase 의 실서버 탐침으로 잡힌다.

## 8. 위험

- **최대 위험은 오탐이다.** 가드가 정상 DB 에서 발화하면 `/passages` 가 통째로 죽는다.
  `sqlite_master` 질의는 `index_pages` 에서 이미 도는 것이라 새 위험은 «자리» 뿐이고,
  완료 기준 4(대조군 3종)와 8(e2e 21종 전수)이 그 축이다.
- **e2e·측정 스크립트가 임시 DB 를 만드는 경로 중 `pages` 를 안 만드는 것이 있으면**
  전수 RED 가 난다. 그것이 있으면 오히려 오늘 잡아야 할 것이라 21종 전수로 잰다.
- 상태 코드가 바뀌므로 **README·테스트가 같은 커밋에서 안 움직이면 RED** 다
  (`digest ## 반복 실패` 의 «기록 3파일 불일치» 와 같은 자리).
