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

