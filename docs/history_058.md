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

## 2026-09-05 03:00 | db-state-invariant | 계획 1/1 시도0

일: 계획 55 를 열었다(`docs/plan_db-state-invariant.md` · 브랜치 `loop/db-state-invariant`
  · 기점 `09b642e`). **먼저 밀린 문서 집안일부터 했다** — `history_current.md` 가 상한
  300줄에 정확히 닿아 자기 항목을 붙이기 **전에** 회전시키고(→ `history_057.md`, 계획 53
  e2e 부터 계획 54 전체까지 일곱 항목) `digest.md` 명부·회전 서술·포인터를 갱신했다.
  **밀려 있던 계획서·설계서 넉 벌도 같이 돌렸다**: 계획 53 것이 자기 차례(계획 54 탐색)에
  안 돌아 두 계획분이 `docs/` 에 남아 있었다 — `plan_history_039`·`design_history_039`
  (=53) · `plan_history_040`·`design_history_040`(=54). 옛 이름을 가리키던 `digest.md`
  5곳·`index.md` 2곳을 새 이름으로 돌렸고(살아 있는 문서에 남은 옛 이름 **0**), 아카이브
  안의 옛 이름은 **수정·삭제 금지**라 그대로 뒀다.
  탐색은 **5순위**(`digest ## 다음 계획 후보` 의 `[5]` — `pages.url` 축)이고 1~4순위는
  전부 0건이다. 임시 디렉터리에서 `store.upsert`→`index_pages` 로 만든 DB 를 열 하나씩
  빼며 `indexer.passages()` 를 직접 불러 **다섯 상태 × 세 질의**를 다시 쟀다
  (`data/crawl.db` 는 **열지도 않았다**).
결과: 단위 **603 OK**(13.301초 · 맨몸·단독 · rc 0). 실측 — 정상 3/0/0 · **`url` 열 없음
  `OperationalError: no such column: url` / 0건 / 0건**(갈림 살아 있다) · `status` 없음
  3/0/0 · `fetched_at` 없음 3/0/0 · `url`+`html` 없음 `no such column: html` ×3.
  **후보의 서술은 글자 그대로 맞았고 처방 후보 하나가 그 자리에서 죽었다** — `PRAGMA
  table_info` 로 `store.SCHEMA` 전 열을 요구하는 안은 오늘 **정상**인 `status`·
  `fetched_at` 두 상태를 500 으로 만드는 오탐이다(`passages()` 가 그 열들을 안 읽는다).
  「기록된 답을 실행 전에 다시 재라」의 일곱 번째 적용이고, **처방이 죽은 것은 두 번째**다.
  중복 방지 5곳 전수 대조 통과(계획 행에 `pages.url` **열** 계획 0개 · `digest ## 완료`
  에 `url` 축 없음 · 보류 0건 · 활성 `plan_*.md` 0개 · `docs/patches/` 없음).
  `git ls-remote origin main` = `c0be72f` · HEAD `09b642e` · **PR 무접촉(조회도 안 했다)**.
다음: **설계** — 계획서 6절의 갈림길 둘을 만들어 잰다. ①`store.SCHEMA` 파싱 · ②손으로 적은
  표 · ③상태마다 클래스 × A `SELECT url, html FROM pages LIMIT 0` · B `PRAGMA table_info`
  (오늘 실측이 반대한다) · C 제품 0줄. ①+A 가 유력하지만 **①의 파싱 비용을 아직 안 쟀다** —
  열을 하나 더한 스키마 사본에 ①·②를 둘 다 먹여 가른다.

## 2026-09-05 04:20 | db-state-invariant | 설계 0/1 시도0
한 일: `docs/design_db-state-invariant.md` 를 썼다. 갈림길 1 에 **넷째 안 ①'** 를 더해
  골랐다 — 눈금을 `store.SCHEMA` 문자열에서 파싱하지 않고 **정상 DB 의
  `PRAGMA table_info(pages)`** 에서 받는다(우리가 쓸 파서 0줄 · 열을 뺀 표를 다시 만들
  선언 타입까지 `PRAGMA` 가 준다). 처방은 **A**(한 낱말). 임시 디렉터리에 제품 사본 셋
  (오늘·A·B)을 만들어 4열 × 3질의를 직접 쟀다(`data/crawl.db` 무접촉).
결과: 단위 **603 OK**(13.559초 · 맨몸·단독 · rc 0) · 제품 `src/` **0줄**.
  ①' 자 실물: 눈금 4칸 · 오늘 **RED 정확히 1행(`url`)** · A 사본 **4행 PASS** · 정상 DB
  오탐 0. **자의 첫 초안이 틀린 것을 실측이 잡았다** — 반환값을 비교하니 정상 DB 가
  `n=2/0/0` 으로 거짓 RED 였다. 자가 재는 단위는 결과가 아니라 **판정**이다.
  **B 를 죽인 진짜 사유는 오탐이 아니라 expand 함정이다**(새로 깬 가정): 사본 `SCHEMA` 에
  `lang TEXT` 를 더하고 기존 정상 DB 를 다시 열자 `CREATE TABLE IF NOT EXISTS` 가 열을 안
  더해 세 질의 전부 `no such column: lang` — 읽을 수 있는 DB 를 전면 500 으로 만든다.
  비용: `LIMIT 0` 한 열 0.0014ms · 두 열 **0.0015ms** · `LIMIT 1` 0.0087ms(1,000행·6.8KB).
  `data/crawl.db` sha256 무변 · `docs/specs/` 무변 · **PR 무접촉(조회 0회)** · 서버 0개.
다음: **개발 1/1** — 설계 5절 계약대로 자를 먼저 세워 `url` 행 RED 를 보고(자가 0행을 재거나
  RED 0행이면 그 자체가 결함), 제품 한 낱말로 GREEN. 같은 커밋에서 그 줄 위 `ponytail:`
  주석 두 문장의 거짓을 고친다. `test_serve.py` 새 클래스 0개.

## 2026-09-05 05:10 | db-state-invariant | 개발 1/1 시도0
한 일: 자(`TestPassagesColumnAxisInvariant`, `tests/test_indexer.py`)를 세워 RED 를 눈으로
  보고 처방 한 낱말(`SELECT url, html FROM pages LIMIT 0`)로 GREEN. 그 줄 위 거짓이 된
  `ponytail:` 주석 두 문장을 같은 커밋에서 새 천장으로 갈았다. `test_serve.py` 새 클래스 0개.
결과: **RED 정확히 1행**(`url`: `OperationalError/ok/ok`) → 4행 GREEN · 단위 603 → **604 OK**
  (13.671초 rc 0) · 오탐 0(정상·`status`·`fetched_at` 셋 다 `1/0/0`) · 눈금이 `SCHEMA` 를
  따라간다(사본에 `lang` 더하니 4→5) · 눈금 0칸이면 RED · 변이 ① RED · 변이 ② **RED 2행** ·
  HTTP 표면 `/passages` 500 셋 · `/search`·화면 200 · 서버 잔여 0 · `data/crawl.db` sha 무변.
다음: **테스트** — 자가 잡는 축과 안 잡는 축(타입 변경·권한·`docs` 파손)의 경계를 재고,
  `README` 숫자 가드처럼 자 자신이 낡는 자리가 있는지 본다.

## 2026-09-05 06:05 | db-state-invariant | 테스트 1/1 시도0
한 일: 전수를 맨몸·단독으로 다시 돌리고(**604건 OK · 13.320초 · rc 0** — 직전 반복이 적어
  둔 숫자가 참이었다) 변이 넷을 저장소 밖 사본에 다시 심었다. 갭 탐색에서 8점 하나를 닫아
  `tests/test_indexer.py` `TestPassagesColumnAxisInvariant` 에 **자기검사 2**
  (`test_the_three_queries_really_have_different_shapes`)를 더했다. `src/` **0줄**,
  `README.md` 의 `단위 604건` → `605건`.
결과: 단위 604 → **605건 OK**(13.448초 · rc 0). 변이 ①(처방 되돌리기) **RED 1건** —
  604건 중 새 자의 `missing='url'` 하나뿐이다. ②(눈금 0칸) RED. ③(`SCHEMA` 에 `lang`)
  눈금 4→5 자동 확장 + 자는 GREEN. ④(`except OperationalError: return []`) **RED 8건인데
  전부 계획 53·54 의 클래스이고 새 자는 안 죽는다.** 새 자기검사는 `DOC` 의 `김치찌개` 를
  `된장찌개` 로 바꾼 사본에서 `[False, False, False]` 로 RED(본 자는 GREEN).
  `data/crawl.db` sha 무변 · `docs/specs/` 무변 · 서버 잔여 0 · **PR 무접촉(조회 0회)**.
  **핵심 발견: 「53·54 클래스가 이제 중복인가」는 아니다** — ①은 새 자만, ④는 53·54 만
  죽는다. 일관성을 재는 자와 값을 재는 자는 서로를 대체하지 않는다.
  안 한 것(8점 미만): `url` 축 HTTP 클래스 5점(같은 매핑의 두 벌 · 변이 ④가 증명) ·
  2열 이상 조합 4점 · 열 타입 축 4점 — 설계 6절 천장 그대로.
다음: **리뷰** — 새 자기검사가 본 자의 물음을 좁히지 않았는지, 그리고 계획 55 가
  「자리를 넓히는 대신 원칙을 세운다」를 실제로 했는지 백지에서 본다.

## 2026-09-05 01:44 | db-state-invariant | 리뷰 1/1 | 시도0
한 일: `c0be72f`(원격 `main`)부터 HEAD `b660c9d` 까지 **여섯 커밋 전부**를 백지 패스 먼저로
  봤다(README 재작성 `c8827e9` 도 범위 안이다 — 앞 반복들이 이 커밋을 안 세었다).
  적힌 숫자를 하나도 안 믿고 전수·변이·실서버를 다시 쟀다. 지적 넷 중 둘을 그 자리에서
  고쳤다 — `tests/test_indexer.py` `_drop_column` 의 거짓 천장 주석 4줄, `README.md`
  품질 표의 비텍스트 명암비 셀 1줄. `src/` **0줄**.
결과: 전수 **605건 OK · 13.494초 · rc 0**(고친 뒤 재확인 605 OK · 13.504초 · rc 0).
  변이 재측(전부 저장소 밖 전체 사본 · `PYTHONDONTWRITEBYTECODE=1`): ①처방 되돌리기
  **RED 1/605**(`missing='url'`: `OperationalError/ok/ok`) · ②눈금 0칸 RED(`0 not greater
  than or equal to 4`) · ③`DOC` 을 `된장찌개` 로 RED(`[False,False,False]`) — 세 주장 참.
  **새로 심은 변이 ⑤가 계획 55 의 앞날 주장을 실증했다**: 루프 질의를
  `SELECT html, status … WHERE url = ?` 로 넓히고 탐침은 그대로 두자 **RED 1/605** 이고
  그 하나가 새 자(`missing='status'`)다 — *"셋째 열을 읽게 되면 자가 그날을 잡아 준다"* 는
  주석이 참이다. **실서버 실측**(`--port 0` · `url` 열 없는 DB): `/passages` 세 질의
  **500·500·500**, 본문은 셋 다 `{"version": 1, "error": "검색 중 오류가 났다"}` —
  **CSO 통과, sqlite 문구는 서버 stderr 로그에만**(`/passages 실패:
  OperationalError('no such column: url')`). `/search` 는 같은 DB 에서 200 셋인데
  **정상이다** — FTS `docs` 는 `content=` 없는 독립 표라 `pages` 를 안 읽는다(indexer.py:15
  확인). 같은 DB 에 `indexer` CLI 는 rc 1(`DB 를 열 수 없다: … no such column: url`).
  `data/crawl.db` sha256 `85c96744…5bda18` **무변** · `docs/specs/` 무변 · 서버 잔여 0 ·
  **PR 무접촉(조회 0회)** · `main` 직접 커밋 0 · `--no-verify`·`--force` 0.
  지적: **[R55-1] low 자동수정** — `_drop_column` 이 다시 만드는 표가 `PRIMARY KEY`·
  `NOT NULL`·`DEFAULT` 를 잃는다(실측: `url` 뺀 표가 `html TEXT, status INTEGER,
  fetched_at TEXT`). 판정 영향 0 이지만 주석이 *"실제로 만들어진 표를 잰다"* 라 절반만
  참이었다 → 천장 한 줄 추가. **[R55-2] low 자동수정** — README 품질 표가 비텍스트
  명암비 **3:1** 을 잃었는데 `e2e/design_check.py` 는 계속 잰다(`MIN_CONTRAST_NONTEXT
  = 3.0`)이고 `status.md` 의 사람 결정 대기 2번이 바로 그 기준 얘기다 → 셀 복원.
  **[R55-3] low 보고만** — 같은 재작성이 `/passages` 응답 스키마
  `{url,title,position,text}` 와 rc 표의 「어디서」 열도 지웠다. 쉬운 말로 옮긴 편집 의도가
  분명해 되돌리지 않는다. **[R55-4] low 보고만** — 설계 5절이 `README.md` 를 범위 **밖**
  으로 적었는데 테스트 스텝은 고칠 수밖에 없었다(`tests/test_readme.py` 의 `UNIT_COUNT`
  가 숫자를 강제한다). 계약 문구가 반증됐다 — 다음 계획서는 *"README 는 숫자 가드가
  강제하는 줄만"* 으로 적는다. **거짓양성으로 버린 것 하나**: 「자가 일관성만 재고
  «일관되게 틀린» 상태를 통과시킨다」를 변이로 확인했더니(탐침 삭제 + 루프에서
  `except OperationalError: continue`) 새 자는 초록인데 **53·54 클래스 8건이 죽었다** —
  저장소가 이미 덮고 있다(`severity.md` 「이미 충분히 덮는 단언」).
다음: **e2e 1/1** — 계획 53·54 는 새 e2e 파일 0개였다. 21종 전수를 돌려 판정하고,
  `url` 열 없는 DB 의 실서버 500 셋은 이 반복이 이미 쟀으니 새 파일이 필요한지부터 가른다.

## 2026-09-05 02:10 | db-state-invariant | e2e 1/1 | 시도0

- 한 일: 계획 55 의 마지막 phase. **앞 반복이 적어 둔 숫자를 하나도 그대로 안 받았다** —
  `status.md` 가 「rc 0 확인됨」으로 적어 둔 것까지 전부 다시 돌렸고, 앞 phase 들이 단위
  실패 건수로만 재고 넘긴 완료 기준 3·4·5·6 도 저장소 밖 전체 사본(`rsync` · `.git` 없는
  트리)에서 **다시 심어 다시 쟀다**. `e2e/*.py` **21종을 하나씩 따로** 맨몸으로 돌려 각
  rc 를 눈으로 봤다. 결과 문서 `docs/e2e/db-state-invariant/result.md` 를 새로 만들었다
  (이 phase 가 만든 저장소 파일은 그 하나 · `src/` **0줄** · `e2e/` **0줄**).
- 결과: **e2e 21종 전수 rc 0**(합계 약 171초 — 오래 걸리는 넷은 전부 실시계를 일부러
  기다리는 것들이다: `perf_crawl` 28s · `deadline` 19s · `interrupt` 18s ·
  `retry_interval` 15s. 폭주 0). **단위 605 OK · 13.526초 · rc 0**(맨몸·단독).
  **완료 기준 9/9 통과 — 뒤집힌 행 0개**(계획 54 는 9+1 이었다).
  **① 자의 눈금이 스키마를 따라 저절로 컸다**(기준 3) — 사본의 `store.SCHEMA` 에
  `title TEXT` 한 줄을 더하니 자가 도는 눈금이 `url·html·status·fetched_at` **4칸 →
  5칸**이 됐고 테스트 파일은 한 글자도 안 고쳤다. 눈금 0칸이면 조용한 초록이 아니라
  `0 not greater than or equal to 4` 로 죽는다(기준 4, `_columns` 를 눈멀게 해 확인).
  **② 새로 안 것 — 변이 ①과 ②는 동치가 아니다. ②가 더 넓다**: `url,` 삭제는
  `missing='url'` **1건**을 죽이는데, 탐침을 `hits` 루프 안으로 옮기면 `missing='url'`·
  `missing='html'` **2건**이 죽는다. 계획 54 e2e 가 「둘은 HTTP 표면에서 열다섯 칸이 한
  칸도 안 다르다」고 적은 것은 그 측정이 `html` **한 축**만 봤기 때문이고, 열 축 전체를
  도는 자로 재니 **②는 계획 54 가 닫은 자리까지 함께 되돌린다**. 자리를 하나 더 넓히는
  안이었다면 그 회귀를 아무도 못 봤다 — **자를 세운 값이 여기서 실측으로 나왔다.**
  **③ 실서버 두 대**(`--port 0` · 임시 DB · 저장소 `data/crawl.db` 는 열지도 않았다):
  `url` 열 없는 DB 의 `/passages` 세 질의 **500·500·500**(착수 500/200/200) · 같은 DB 의
  `/search` 세 질의와 화면 **200 넷** · 정상 대조군 **7칸 전부 200**(가드 오탐 0).
  **CSO 통과** — 500 본문에 `sqlite`·`OperationalError`·`no column`·DB 경로 **0건**,
  원인은 서버 stderr 에만. **새 e2e 파일 판정 0개** — 결정적 근거는 계획 53·54 때와
  다르다: 손으로 적는 e2e 는 스키마를 따라 안 커서 **이 계획이 없애러 온 취약성(「다섯
  번째 열이 생기는 날 알아차리는 기계가 0개」)을 e2e 디렉터리에 새로 만든다**. 원칙을
  세운 계획이 그 원칙을 어기는 파일을 남기지 않는다. 품질·성능 **전 축 무변**
  (`passage_eval` 100.0%/398 · 채택률 99.5% · p95 1.65ms · `quality_eval` ko 20/20 ·
  en 19/20 · `perf_search` p95 8.81ms · `perf_crawl` 10.24/s · `design_check` 4축).
  `data/crawl.db` sha256 `85c96744…5bda18` — **계획 54 e2e 가 적어 둔 값과 같다** ·
  `docs/specs/` 무변 · 서버 잔여 0 · **PR 무접촉(조회 0회)** · `--no-verify`·`--force` 0 ·
  러너 규율 위반 0(러너를 파이프 왼쪽에 둔 적 없다).
- 다음: **계획 55 DONE.** 다음 반복은 계획 탐색이다. 이어받을 것 셋은 result.md 8절 —
  `sqlite_master` 질의 두 곳(세 번 연속 미룬 자리) · `passages()` 가 셋째 열을 읽는 날
  탐침에 그 열을 더한다(리뷰 55 의 변이 ⑤가 자가 그날을 잡는 것을 실증) · 자가 못 보는
  축(타입 변경·제약·권한)은 `sqlite_master.sql` 이 필요하다.

