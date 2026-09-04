# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

**회전 명부는 `digest.md` 의 `## 완료` 절 «아카이브 명부» 줄이 정본이다.**
여기 있던 스물한 회전의 서술(233줄)은 그 줄과 내용이 겹쳤고, 검사가 강제하는 명부도
그쪽 하나뿐이라(`tests/test_docs.py` 의 `ArchiveIndexTest`) **개발 9(반복 269)가 이
자리에서 지웠다** — 회전으로는 300줄 상한을 못 맞추던 세 반복(309 → 372 → 418줄)의
원인이 이 명부였다. **지운 것은 머리말이지 반복 기록이 아니다** — 항목은 여전히
append 전용이고 수정·삭제 금지다. 각 회전의 사유는 `digest.md` 의 같은 줄에, 원문은
`history_<NNN>.md` 에 그대로 있다.

## 2026-09-04 18:05 | passage-db-state | 계획 | 시도0

- 한 일: **계획 53 을 열었다.** `rules/discover.md` 순위대로 돌아 **1~5순위 실측 0건** —
  단위 `Ran 593 tests in 13.493s OK`(맨몸·단독) · 타입체커·린터 **설정 0개** ·
  `src/`·`tests/`·`e2e/` 전수 grep 의 유일한 `TODO` hit 는 `tests/test_indexer.py:758`
  의 **fixture HTML 문자열 안**이라 코드가 아니다 · `docs/candidates.md` 없음 ·
  `digest ## 보류` 는 빈 절. 6순위 `digest ## 다음 계획 후보` 의 `[5]`(「`pages` 테이블이
  없으면 `/search` 는 200, `/passages` 는 500 이다」)를 채택했다.
- **중복 방지(discover 5절)가 값을 냈다 — 취소선 누락 하나를 잡았다.** `index.md` 의
  계획 표 전체와 사양 분할 목록을 `digest` 후보와 전수 대조하니 겹침 0 인데, 후보 중 점수가
  가장 높은 축인 `[6] focus_rule 의 위치·극성` 이 **계획 49 `focus-rule-scope` 로 이미
  닫혀 있었다**(`e2e/design_check.py` 의 조건 6 이 중괄호를 세서 ⓐⓑ 를,
  `INDIRECT_RE`+`FOCUS_RE` 가 ⓒⓓ 를 닫는다). 취소선만 없어서 후보로 남아 있었다 —
  그대로 믿었으면 **완료된 것을 다시 여는 반복**이었다. `digest` 에 취소선과 닫은
  계획을 적었다.
- **채택한 후보의 처방도 다시 재서 절반인 것을 찾았다.** 후보는 «`passages()` 가
  `NoCrawlDataError` 를 쓰면 503 이 맞다» 인데, `serve.py:281` 의 503 튜플이
  `(FileNotFoundError, StaleIndexError)` 뿐이라 **그것만으로는 여전히 500** 이다.
  고칠 자리가 한 곳이 아니라 두 곳이다 — `digest [7]` 「기록된 답을 실행 전에 다시
  재라」의 **다섯 번째** 적용(계획 41·44·51·52 에 이어).
- **후보의 서술도 절반이었다 — 실서버로 쟀다.** `store.upsert` → `index_pages` 로 만든
  1문서 DB 에 `DROP TABLE pages` 한 뒤 `python3 -m websearch.serve` 를 실제로 띄웠다
  (탐침 `scratchpad/probe_http2.py`). `pages` 없는 DB: `q=김치찌개` **500** ·
  `q=zzzznope` **200 `[]`** · `q=%01` **200 `[]`** · `GET /search?q=김치찌개` **200**.
  정상 DB 대조군 3종은 200(문단 1건 / `[]` / `[]`). 즉 「`/passages` 는 500」이 아니라
  **DB 상태 판정이 질의 내용에 달려 있다** — `hits` 가 비면 `SELECT html FROM pages`
  에 닿지도 않는다. 이것은 계획 47 `db-open-atomic` 이 `search()` **안**에서 닫은 고장의
  형제이고, `indexer.py:246-249` 의 주석이 그 원칙을 못박아 뒀는데 함수 하나 건너에서
  안 지켜졌다.
- 결과: `docs/plan_passage-db-state.md`(1~8절). **설계 필요 — 트리거 셋**(공개 계약
  `/passages` 상태 코드·`README.md:40` · 3파일 이상 · 갈림길 셋). 완료 기준은 오늘
  실측값과 **짝**으로 적었다(500/200/200 → 503 셋 · 대조군 3종 무변 · `/search` 200 무변 ·
  단위 593+N · e2e 21종 rc 0 · 정확도 100.0% · 채택률 99.5% · 변이 둘).
- 브랜치 `loop/passage-db-state` 를 **`a4a4da1`** 에서 땄다. 기점을 `main` 으로 안 잡은
  이유는 원격을 직접 다시 읽어서다 — `git ls-remote origin loop/focus-ring-combinator`
  = `a4a4da12…`(로컬 HEAD 와 같다) · `git ls-remote origin main` = `687a1598…`(계획 47) ·
  `gh pr list` 로 **PR #7 `OPEN` · `mergedAt: null`**. `main` 에서 따면 `README.md` 의
  건수 단언이 첫 커밋부터 RED 다. **PR #7 무접촉.**
- 문서: `status.md`(iteration 309 · `plan: passage-db-state` · phase 계획 · step 0/1) ·
  `metrics.md`(반복 309 · 진행 1 · phase 계획 33) · `index.md`(53번 행 + 확장 10번에
  「계약의 빈칸」 한 문단) · `digest.md`(취소선 하나 + `[5]` 에 재측 결과) ·
  `history_current.md`. `docs/specs/`·`data/crawl.db`·`src/` **무변**.
- **회전 하나 돌렸다** — 항목을 붙이기 전 `grep -c ""` 이 **300줄**(상한 정확히)이라
  계획 52 의 여섯 항목(반복 303~308)을 통째로 `history_055.md` 로 밀었다.
  계획 52 가 DONE 이라 경계가 깨끗하고, 다음 설계 phase 가 읽을 것은 이 항목 하나다.
  스물두 회전 연속 지각 0. 명부는 `digest ## 완료` 의 같은 줄에 이어 붙였다.
- 다음: **설계 1/1** — 갈림길 셋(① 503 이냐 200 `[]` 이냐 ② 가드를 `passages()` 안이냐
  `_connect()` 냐 ③ 화면 사다리의 503 튜플도 넓히나)을 실측으로 가른다.


## 2026-09-04 17:55 | passage-db-state | 설계 | 1/1 시도0

- 한 일: **계획 53 설계 1/1.** 계획서 6절이 연 갈림길 셋을 각각 ① 최소 · ② 정공법 ·
  ③ 되돌리기 우선 **세 출발점에서** 안을 내고 표로 갈랐다. `docs/design_passage-db-state.md`.
  결정은 **편집 둘 + 주석 하나** — ① `indexer.passages()` 의 `_connect()` 직후·`hits`
  루프 **앞**에 `index_pages()` 와 같은 `sqlite_master` 가드 네 줄을 인라인으로,
  ② `serve.do_GET` JSON 사다리의 503 튜플에 `indexer.NoCrawlDataError`,
  ③ 화면 사다리는 **안 넓히고** `# JSON 과 같은 값` 주석을 비대칭 사유로 고친다.
- **갈림길 1(503 대 200 `[]`) → 503.** 가른 행은 「소비자가 «우리가 터졌다» 와 «근거가
  없다» 를 구별하나」다. 같은 고장난 DB 의 `/search` 가 **200 · 결과 1건**이라, 200 `[]`
  가 내는 「문서는 있는데 근거는 0건」은 **오늘의 정상 응답과 글자 그대로 같다** —
  제목만 매치됐거나 2-gram 이 문단 경계를 넘은 문서가 그 답을 내고 그것을
  `e2e/hidden_passage_e2e.py` 가 0/5 로 재고 있다. `NoCrawlDataError` docstring 이
  금지한 «0 으로 합치면 조용한 성공으로 보인다» 가 바로 이 합침이다. C(200 + 경고 필드)는
  상태 코드만 읽는 인프라에게 A 와 같은 답이고 계약 표면이 가장 넓어져 버렸다.
- **갈림길 2(가드 자리) → `passages()` 안, `search()` 뒤·루프 앞.** A(`_connect()`)는
  `search()` 도 그 문을 지나므로 `pages` 없는 DB 의 `/search` 를 200 → 503 으로 죽인다
  (계획서 완료 기준 5·7절이 금한 「둘 다 죽인다」). C(헬퍼 추출)는 관측이 B 와 같은데
  `index_pages()` 를 건드리는 **직교 편집**이라 버렸다 — 저장소의 「두 벌 문자열은 갈린다」
  선례(`_CURRENT_SQL`)는 **서로 맞아야만 참인** 두 문자열 얘기고 여기 둘은 그렇지 않다.
  대신 천장을 `ponytail:` 주석으로 코드에 남긴다(셋째 호출자가 생기면 뽑는다).
  자리를 `search()` **뒤**로 좁힌 것도 값이다 — 옛 색인의 우선순위가 오늘 그대로고
  이미 연 연결을 써서 **연결 추가 0**이다.
- **갈림길 3(화면 사다리) → 안 넓힌다.** 실측이 갈랐다: `pages` 없는 DB 의
  `/?q=김치찌개` 는 **200 · 결과 1건**이다 — `_page_hits()` → `search()` 는
  `NoCrawlDataError` 를 못 낸다. 넣으면 **어떤 테스트로도 RED 로 못 만드는 줄**이 생겨
  계획서 완료 기준 10(변이가 죽는다)이 못 덮는 코드가 된다. 값은 주석 한 줄이라,
  거짓이 되는 `# JSON 과 같은 값` 을 「왜 좁은지」로 바꾸는 것으로 갚는다.
- **가장 위험한 가정을 깼고 참이었다.** 「정상 경로 어디에도 `pages` 없는 DB 로
  `passages()` 를 부르는 곳이 없다」 — 추측하지 않고 **두 편집을 실제로 넣고 전수를
  돌린 뒤 되돌렸다**(커밋 0 · 제품 `src/` 최종 0줄). 단위 `Ran 593 tests OK` 를
  **두 번**(가드만 · 가드+튜플) · e2e **21종 전수 rc 0** · `passage_eval` 정확도
  **100.0%** · 채택률 **99.5%** · p95 **1.52ms** 무변 · `search_api_e2e` 의 503/500
  계약 단언도 통과. 대조군 다섯 줄(`/passages` 3종 · `/search` · 화면)이 세 열에서
  한 글자도 안 움직였다.
- **덤으로 둘이 굳었다.** ① **가드만으로는 여전히 500** — 계획서 3절의 「처방은 한 곳이
  아니라 두 곳」이 프로세스 밖 HTTP 로 확인됐고, 그 열이 그대로 완료 기준 10 변이 ②의
  기대값이다. ② **「판정이 질의 내용에 안 달린다」를 내는 것은 가드 하나다** — 가드만
  넣어도 세 질의(매치 있음·매치 없는 낱말·무토큰)가 500 하나로 모인다. 503 은 그 위에
  얹는 «맞는 이름» 이다. 겹쳐 있던 두 고장을 **서로 다른 편집이** 고친다.
- 탐침은 새로 안 짰다 — 계획 phase 의 `scratchpad/probe_http2.py` 에 `/search` 와
  화면 두 줄만 더해 재사용했다(ponytail 2칸). 서버는 열마다 띄우고 끝에 종료했다.
- 결과: `docs/design_passage-db-state.md`(1~6절 — 갈림길 셋의 표 · 깬 가정 · 계약 ·
  천장 · 역할 검토 · 되돌리기). 개발이 새로 고를 것은 없다. 설계가 완료 기준 둘을
  더했다(화면 200 무변 · 화면 사다리 주석의 비대칭 사유).
- 문서: `status.md`(iteration **310** · phase 설계 · step 0/1) · `metrics.md`(반복 310) ·
  `index.md`(53번 행에 설계 결과) · `history_current.md`. 커밋 `fc3e6ef` 는
  **일찍 커밋·푸시**했고(앞 설계 에이전트가 두 시간 무응답으로 아무것도 못 커밋한 뒤라
  중간 결론부터 올렸다) 원격 `loop/passage-db-state` 에 올라간 것을 `ls-remote` 로 확인했다.
  `docs/specs/`·`data/crawl.db`·`src/` **무변** · **PR #7 무접촉**.
- **러너 규율 위반 0회** — 단위·e2e·탐침·`git push` 어디에도 파이프·리다이렉션 0.
- 다음: **개발 1/1** — TDD 로 세 질의를 먼저 RED 로 세운다.
  `tests/test_indexer.py` 의 `test_missing_db_raises` 옆에 `subTest` 셋,
  `tests/test_serve.py` 의 `test_every_passages_response_carries_version` 표에
  `NoCrawlDataError → 503` 행 + 실제 DB HTTP 503 하나(같은 DB 의 `/search` 200 을 옆에).
  `README.md` 계약 줄과 `단위 593건`·`tests/test_readme.py` 건수 단언은 **같은 커밋**.

## 2026-09-04 18:20 | passage-db-state | 개발 | 1/1 시도0

- 한 일: **설계서 3절 계약을 그대로 심었다.** ① `indexer.passages()` 의 `_connect()`
  직후·`hits` 루프 **앞**에 `index_pages()` 와 같은 `sqlite_master` 가드 · ② `serve` JSON
  사다리의 503 튜플에 `indexer.NoCrawlDataError` · ③ 화면 사다리는 **안 넓히고**
  `# JSON 과 같은 값` 주석을 「왜 더 좁은가」로 다시 썼다. 헬퍼는 안 뽑았고 천장 둘은
  `ponytail:` 주석과 「테이블 유무만 본다」 주석으로 코드에 있다. 제품 diff 는
  `src/websearch/indexer.py` **+10** · `src/websearch/serve.py` **+8/-2** 두 파일뿐.
- **RED 를 먼저 눈으로 봤다** — `FAILED (failures=5, errors=1)`. 계획서 완료 기준 1·2·3 이
  각각 `OperationalError: no such table: pages`(HTTP 500) · `NoCrawlDataError not raised`
  (200 `[]`) · 같은 것(무토큰)으로 나왔다. 계획·설계 phase 가 프로세스 밖 HTTP 로 잰
  500/200/200 이 **단위 테스트 안에서 글자 그대로 재현됐다** — 탐침이 잰 것과 테스트가
  잡는 것이 같은 고장이라는 확인이다. GREEN 은 **593 → 596 OK**(13.596초 · 맨몸·단독).
- **대조군이 RED 때부터 초록이었다.** `TestPassagesWithoutPagesTable` 의
  `test_search_still_answers_200` 은 구현 전에도 통과했다 — 갈림길 2(가드를 `_connect()`
  에 두면 `/search` 가 죽는다)를 붙드는 자리라 **구현 후에도 초록인 것**이 값이다.
  가드가 `search()` 로 번지는 변이는 여기서 죽는다.
- **변이 둘 다 사망**(완료 기준 10): ① `passages()` 가드 삭제 → `failures=3, errors=1` ·
  ② 503 튜플에서 `NoCrawlDataError` 제거 → `failures=2`. 스크래치패드 사본에서 돌려
  `.mutation-lock` 도 `git checkout` 도 안 썼다(계획 52 개발이 산 교훈).
- **변이 첫 판이 엉뚱한 자리를 지웠다 — 설계서의 천장이 도구에서 먼저 나타났다.**
  `t.index("if not db.execute(")` 가 `index_pages()` 의 **같은 가드**를 먼저 잡아 변이 ①이
  `passages()` 가 아니라 `index_pages()` 를 지웠고, 그 결과가 「무관한 테스트 하나 에러」로
  보였다. 설계가 「같은 세 줄이 두 곳 — 헬퍼는 안 뽑고 `ponytail:` 주석으로 천장을 남긴다」
  고 적은 그 중복이, 제품이 아니라 **변이 도구를 먼저 물었다.** `def passages` 뒤부터
  찾도록 고쳐 다시 쟀다. 두 벌 문자열의 값은 여전히 얇지만 **비용이 0 은 아니라는 실측**이
  하나 생겼다 — 셋째 호출자가 생기면 뽑는다는 주석의 근거가 그만큼 굳었다.
- 범위: `data/crawl.db` sha256 `85c967…5bda18` 무변(`git status` 에 안 뜬다) ·
  `docs/specs/` 무변 · `e2e/` **0줄** · 새 파일 0 · **PR #7 무접촉**. `README.md` 는 계약
  줄(`pages` 없음 추가)과 `단위 596건` 둘 다 **같은 커밋**이다 — 건수 단언
  (`tests/test_readme.py`)이 RED 목록에 함께 떠서 잊을 수 없었다.
- **러너 규율 위반 0회** — 단위·변이 어디에도 파이프·리다이렉션 0. 서버를 띄운 것은
  `ServeTestCase` 안뿐이라 남은 프로세스 0.
- 커밋 `a4efdd9` 를 푸시했고 `git ls-remote origin loop/passage-db-state` 가
  `a4efdd94763f937c43541b787eb3a3f219bc4a80` 으로 로컬 HEAD 와 같음을 확인했다.
- 다음: **테스트** phase. 갭 후보 셋 — `pages` 는 있는데 `html` 열이 없는 DB(설계서 4절이
  「500 이 맞는 이름」으로 적어 둔 천장인데 붙드는 단언이 **0개**) · 가드가 `search()`
  **뒤**라는 순서(옛 색인 우선순위) · 화면 사다리를 **안 넓힌 것**.


## 2026-09-04 18:35 | passage-db-state | 테스트 | 1/1 시도0

- 한 일: **개발이 남긴 갭 후보 셋을 직접 재서 둘을 붙들고 하나를 넘겼다.** 테스트 **+3**
  (`tests/test_serve.py` 만) · 제품 `src/` **0줄** · **599 OK**(13.342초 · 맨몸·단독,
  `PYTHONPATH=src python3 -m unittest discover -b tests`).
- **후보 ①이 후보가 적은 것보다 나빴다 — 천장은 500 하나가 아니라 500/200 갈림이다.**
  설계서 4절은 `pages` 는 있는데 `html` 열이 없는 DB 를 *"기다린다고 안 낫는 상태라 500 이
  맞는 이름"* 이라고만 적었는데, 임시 DB 로 재니 **질의 내용으로 갈렸다**:
  `q=김치찌개` 는 `OperationalError: no such column: html` → **500**, `q=zzzznope` 와
  `q=%01` 은 루프가 한 번도 안 돌아 **200 `[]`**. 계획 53 이 테이블 째로 없는 DB 에서 닫은
  바로 그 고장이 **열 하나 아래에 그대로 살아 있다** — 가드가 테이블의 유무만 보기 때문이다.
  「500 이 맞는 이름」은 참이지만 **답의 절반에만 참**이다.
  → `TestPassagesWithoutHtmlColumn` 둘로 **오늘의 답을 그대로 못박았다**(바라는 답이 아니다).
  천장을 옮기는 날 이 둘이 빨개져 「그 갈림을 알고 바꾼다」가 되게 하는 것이 값이다.
- **후보 ③(화면 사다리를 안 넓힌 것)은 `serve.py` 주석의 실측값으로만 있던 것을 쟀다** —
  `pages` 없는 DB 의 `GET /?q=김치찌개` 가 **200 · 결과 있음**. `test_html_screen_still_answers_200`.
- **후보 ②(가드가 `search()` 뒤라는 순서)는 안 열었다 — 6점.** 실측: `pages` 없음 + 옛 색인
  이면 세 질의 전부 `StaleIndexError`(`NoCrawlDataError` 아님)이고, **둘 다 503 이라 HTTP
  표면에서는 구분이 없다.** 곁에서 두 갈래를 더 쟀다 — 「`pages` 있고 `docs` 없음(색인 전)」은
  `[]`(200), 「둘 다 없음」은 `NoCrawlDataError` 다. 셋 다 오늘의 계약과 맞아 `digest` 로 넘겼다.
- **변이 둘로 새 단언을 검증했다**(스크래치패드 사본 · `git checkout` 0회).
  ① **가드가 열까지 본다**(`sql LIKE '%html%'` 를 더한다 = 천장을 옮긴다) → `failures=3`
  으로 **새 테스트 둘만** 죽었다(나머지 596 초록). ② **가드를 `passages()` 에서 빼
  `search()` 로 옮긴다**(설계가 버린 「대칭」안) → `failures=2` — 새 화면 테스트와
  기존 `test_search_still_answers_200` 이 함께 죽었다.
- **화면 테스트는 고유한 킬러 변이가 없다는 것을 적어 둔다.** 변이 ②에서 기존 단언과 **같이**
  죽었고, 설계가 예고한 대로 「화면 사다리를 대칭으로 넓히는」 변이는 어느 쪽도 못 죽인다
  (`search()` 가 `NoCrawlDataError` 를 안 내므로 그 줄은 영영 안 닿는다). 남긴 이유는
  **두 번째 표면**이라는 것 하나다 — 화면이 근거 문단을 그리게 되는 날 이 줄만 빨개진다.
- **e2e 21종 전수 rc 0** (`PYTHONPATH=src python3 e2e/<name>.py`, 하나씩 rc 를 눈으로 봤다).
  `passage_eval` **정확도 100.0% · p95 1.52ms** · `quality_eval` 통과 · `design_check`·
  `pagination_ui_e2e` 4축 · `hidden_passage_e2e` 0/5 무변. 계획서 8절이 최대 위험으로 적은
  「임시 DB 를 `pages` 없이 만드는 e2e 가 있으면 전수 RED」는 **0건**으로 닫혔다.
- 범위: `data/crawl.db` sha256 `85c967…5bda18` 무변 · `docs/specs/` 무변 · `src/` **0줄** ·
  `e2e/` 0줄 · 새 파일 0 · **PR #7 무접촉**. `README.md` 는 `단위 596 → 599건` 한 줄뿐이고
  `tests/test_readme.py` 의 건수 단언과 **같은 커밋**이다.
- **러너 규율 위반 0회** — 단위·변이·e2e 어디에도 `2>&1`·`>/dev/null` 단독 사용 0,
  판정 줄(`OK`/`FAILED`/`rc=`)을 전부 눈으로 봤다. `pgrep -f websearch.serve` **0건**.
- 다음: **리뷰** phase.

## 2026-09-04 18:50 | passage-db-state | 리뷰 | 1/1 시도0

- 한 일: **계획 53 의 세 커밋(`a4a4da1..HEAD`)을 백지 패스부터 다시 읽고, 문서가
  「검증됨」으로 적어 둔 것을 전부 다시 쟀다.** 보고 **1건**(자동 수정 1 · 승인 필요 0) ·
  제품 `src/` **0줄** · **599 OK**(13.607초 · 맨몸·단독).
- **[R53-1] 자동 수정 — 세 질의가 갈리는지 재는 단언이 `subTest` 밖에 있었다.**
  `tests/test_serve.py` 의 `TestPassagesWithoutPagesTable.test_every_query_shape_is_503` 은
  세 질의를 `subTest` 로 돌면서 단언 셋은 `with` 블록 **밖**에 뒀다 — 첫 질의에서 멈추고
  어느 질의가 갈렸는지도 안 남는다. 설계서 3절이 *"세 질의가 한 테스트 안의 `subTest`
  셋이어야 「판정이 질의 내용에 안 달린다」가 하나의 축으로 잡힌다"* 고 적은 그 축이
  **실제로는 안 잡혀 있었다.** 실측으로 갈랐다 — 판정을 `hits` 에 매다는 변이에서
  고치기 전에는 라벨 없는 실패 **1건**, 고친 뒤에는 `(q='zzzznope')`·`(q='%01')` **2건**.
  같은 계약을 단위에서 재는 `test_db_without_pages_raises_for_every_query_shape` 는
  처음부터 둘을 냈다: **두 표면이 같은 축을 재는데 한쪽만 눈금이 있었다.**
- **변이 넷을 스크래치패드 사본에서 다시 돌렸다**(`git checkout` 0회 · 저장소 무변).
  ① 503 튜플에서 `NoCrawlDataError` 제거 → `failures=2` ·
  ② 가드 삭제 → `failures=3, errors=1` ·
  ③ 가드를 `hits` 에 매단다(`if hits and not …`) → `failures=3`(고친 뒤 **4**) ·
  ④ **화면 사다리를 `NoCrawlDataError` 로 넓힌다 → `599 OK`, 죽는 것 0.**
  ④ 가 값이다 — 설계 갈림길 3 이 「대칭으로 넓히면 어떤 테스트로도 RED 를 못 만드는 줄이
  생긴다」고 적고 `serve.py` 주석이 그것을 근거로 삼은 자리를 **리뷰가 처음 직접 쟀다.**
  테스트 phase 가 「화면 테스트는 고유한 킬러 변이가 없다」고 적어 둔 것도 같이 확인됐다.
- **열거형 완전성을 diff 밖 전수로 봤다**(`rules/review.md` 3절). `passages()` 의 비테스트
  호출자는 `serve` **한 곳**뿐이고 `indexer.main` 은 `passages` 를 안 부른다 — 새 예외가
  CLI 트레이스백으로 새는 경로 **0**. `NoCrawlDataError` 를 받는 자리는 `main`(rc 1)과
  JSON 사다리(503) 둘이고 화면 사다리는 **일부러** 안 받는다. 연결도 안 샌다 — 가드의
  `raise` 는 `finally: db.close()` 안이다.
- **버린 후보 5건**(80점 미만): ① `sqlite_master` 질의 두 벌을 헬퍼로 — 설계가 판정하고
  `ponytail:` 주석으로 천장을 남긴 자리라 승인 축이다 · ② `test_html_screen_still_answers_200`
  은 고유 킬러가 없으니 지운다 — 두 번째 표면의 계약을 적은 중복이라 `severity.md` 4절
  억제 항목 · ③ `passages()` docstring 이 새 예외를 안 적는다 — `search()` 도 안 적는
  저장소 관례(일관성만을 위한 변경) · ④ `TestPassagesWithoutHtmlColumn` 이 결함을 계약으로
  굳힌다 — docstring 이 *"바라는 답이 아니라 오늘의 답"* 이라고 먼저 적었고 `digest` 에
  여는 조건까지 있다 · ⑤ `docs/digest.md` 가 상한 200 을 넘겼다(207줄) — 기점 `a4a4da1`
  에서 이미 205 라 이 계획이 만든 것이 아니다(2줄만 이 계획 몫).
- `digest` 로 넘긴 6점 둘의 점수를 다시 봤다 — **둘 다 맞다.** 「`html` 열 없음」은 스키마를
  손으로 고쳐야 닿고(`store`·`indexer` 의 어느 경로도 그런 `pages` 를 안 만든다), 「판정
  셋의 우선순위」는 셋 다 503 이라 HTTP 표면에서 구분이 없다. 8점(정상 흐름에서 난다)은
  둘 다 아니다.
- 범위: 고친 파일은 `tests/test_serve.py` **하나**(단언 셋을 `with` 안으로 + 사유 주석).
  `src/` **0줄** · `e2e/` 0줄 · `README.md` 0줄 · 새 파일 0 · `docs/specs/` 무변 ·
  `data/crawl.db` sha256 `85c967…5bda18` 무변 · **PR #7 무접촉**(조회도 안 했다).
- **러너 규율 위반 0회** — 단위·변이 어디에도 `2>&1`·`>/dev/null` 단독 사용 0이고
  `Ran 599 … OK` 판정 줄을 눈으로 봤다. 서버는 `ServeTestCase` 안에서만 떴고
  `pgrep -f websearch.serve` **0건**.
- 다음: **e2e** phase. 완료 기준 8(21종 전수)은 테스트 phase 가 이미 rc 0 으로 닫았으니
  e2e 는 **계약 표면**을 실서버로 다시 재는 것이 몫이다 — `pages` 를 치운 DB 에서
  `/passages` 503 · `/search` 200 · 화면 200. 집안일 하나: `digest.md` 207줄(상한 200).
