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

## 2026-09-05 02:59 | loader-isolation | 계획 0/1 | 시도0

- 계획 55 아카이브(`plan/design_history_041.md`) · 새 기점 `main`(`fe4dd0d`, PR #10 병합 확인 ·
  열린 PR 0) · `history_current` 회전 없음(187줄 < 300).
- 탐색 1~5순위 0건 → 6순위 `digest [5]`③. **기록된 처방(전역 저장·복원 두 줄)보다 작은 답을
  탐침이 냈다** — `unittest.TestLoader()` 새 인스턴스(필터 아래 605 vs 5), 호출처는 한 곳뿐.
  실패 메시지가 README 를 틀리게 고치라고 지시하는 **함정**인 것이 새로 보였다.
- 러너 규율 **위반 1회(누적 35)** — `for` 루프로 `-k` 일곱 번을 `2>&1 | tail -6` 에 넣어 `rc` 를 잃었고
  즉시 맨몸 재실행했다. 새 방아쇠: 「한 번에 여러 번 돌린다」. 전수 **605 OK · rc 0** · 제품 0줄.
- 다음: 개발 1/1 (`tests/test_readme.py` 한 줄 + 주석 · 완료 기준은 계획서 4절).

## 2026-09-05 05:05 | loader-isolation | 개발 1/1 | 시도0

- 한 일: `tests/test_readme.py` 의 `test_verification_counts_match_reality` 가 세는 자를
  모듈 수준 싱글턴 `unittest.defaultTestLoader` 에서 **새 인스턴스 `unittest.TestLoader()`**
  로 바꿨다(실질 한 줄 + 왜인지 적는 주석 넉 줄). 제품 `src/` **0줄** · `e2e/` 0줄 ·
  저장소 코드 파일 **1개**. 착수 전에 계획서의 값을 맨몸으로 다시 쟀고 한 글자도 안 달랐다.
- 결과: **RED 를 눈으로 봤다** — `-k Readme` 가 `AssertionError: (605, 21) != (5, 21)` ·
  `Ran 5` · rc 1. 고친 뒤 `-k Readme` **`Ran 5 · OK · rc 0`**, 전수 **`Ran 605 tests · OK ·
  rc 0`**(13.579초 · 맨몸·단독 · 고치기 전 605 와 같다). 기전 실측: 전역에
  `testNamePatterns=["*Readme*"]` 를 심으면 `defaultTestLoader` **5** · `TestLoader()` **605**.
  호출처는 저장소 전체에 **한 곳뿐**(다시 셌다).
  **완료 기준 3 을 변이 셋으로 쟀다**(전부 저장소 밖 사본): ①검사 안에서 전역을 손으로
  오염 → `OK` rc 0(고친 줄이 막아 냈다) · ②그 위에서 `TestLoader()` 를 되돌림 →
  **`FAILED` rc 1**(확인이 살아 있다) · ③`README` 의 `단위 605건`→`604건` →
  **`FAILED` rc 1**(자가 안 멀었다).
  `README.md` 무변(완료 기준 4) · `git status --short` 에 계획 밖 코드 파일 **0개**(기준 5).
  `data/crawl.db` sha256 `85c96744…5bda18` 무변 · `docs/specs/` 무변 · 서버 잔여 0 ·
  **PR 무접촉(조회 0회)** · `--no-verify`·`--force` 0 · 러너 규율 위반 **0회**.
- **핵심 발견 — 함정이 사라진 것을 변이 ③이 같이 보여 줬다.** 고친 뒤엔 같은 실패가
  `-k` 아래에서도 「실제는 **(605, 21)**」라고 말한다. 고치기 전 그 자리의 문구는
  「실제는 (5, 21)」이었고, 그것을 믿고 README 를 고치면 전수가 뒤집혔다.
  **이 계획의 산출물은 「검사가 산다」가 아니라 「검사가 참말을 한다」였다.**
- **사고 — 3시간 자동 스냅샷 잡이 스텝 중간을 덮쳤다.** launchd
  `com.ohjungs.osearch-autocommit`(`StartInterval 10800`)이 04:50 에 작업 트리의 코드
  변경을 `bfaa3d8 자동 스냅샷 … 미커밋 작업 보존` 으로 커밋하고 **원격에 밀었다**.
  되돌리려면 `push --force` 인데 한도가 금지해 **고치지 않고 뒀다** — 브랜치의 코드는
  계획대로고 값도 같지만 **스텝 커밋이 둘로 갈렸다**(코드 `bfaa3d8` · 기록 이번 커밋).
  계획 45 의 `.mutation-lock` 관례가 이 잡을 세우려고 있던 것인데, 그 관례는 «변이를
  심는 동안» 만 덮고 **정상 작업 중간**은 안 덮는다. 다음에 RED 중간을 덮치면 깨진
  상태가 원격에 올라간다 — `status.md` 사람 결정 4번으로 올렸다.
- 다음: **테스트 phase.** 개발이 이미 변이 셋으로 재고 왔으니 볼 것은 「그 셋이 충분한
  축인가」다. 안 잰 축 하나가 보인다 — 오늘 센 것은 **호출처**(1곳)인데 안 센 것은
  **오염원**이다(`unittest.main` 말고 `defaultTestLoader` 에 상태를 심는 진입점이 또 있나).

## 2026-09-05 07:40 | loader-isolation | 테스트 1/1 | 시도0

- 한 일: 개발이 남긴 단서(*"센 것은 호출처(1곳)인데 안 센 것은 **오염원**"*)를 본체로 삼아
  **모듈 수준 싱글턴을 건드리는 자리를 저장소 전체에서 세고, 새는지를 실측으로 갈랐다.**
  저장소 코드 **0줄** · 새 파일 0(탐침 넷은 전부 스크래치패드).
- 결과 — **오염원 후보 7종 12자리 중 실제로 새는 것은 1종**: `sys.path`(4자리 전부 안
  되돌린다 — `test_design_check.py:25`·`test_quality_eval.py:17`·`test_passage_eval.py:184`,
  그리고 **`TestLoader.discover` 자신**). 나머지는 되돌리거나(`signal.SIGINT` 2자리 ·
  `PAGES` 의 `mock.patch.dict` · `sys.stdout/stderr` 의 `with`) 단위 스위트 밖이거나
  (`urllib` 전역 opener 는 `e2e/` 3자리) 저장소 코드에 **0자리**다
  (`logging`·`socket`·`sqlite3`·`warnings`·`locale`·`decimal`·`os.environ`).
- **「진입점이 또 있나」에 CPython 을 세어 답했다** — `defaultTestLoader` 에 쓰는 자리는
  표준 라이브러리 **전체에 한 곳**(`unittest/main.py:151`, 3.9.6 실측)이고 대상은
  `testNamePatterns` 뿐이다. 그것은 **클래스 속성**인데 `main` 은 **인스턴스**에만 쓰므로
  새 인스턴스는 구조적으로 면역이다. 도달 가능한 CLI 경로 넷을 다 때려 **전부 GREEN**:
  `discover -k Readme`(5 OK) · `-k '*counts*'`(3 OK) · `python3 tests/test_readme.py -k
  counts`(1 OK · `unittest.main` 직행) · `-m unittest -k counts test_readme`(1 OK).
  **다섯째 가설은 실측이 지웠다** — 「`-t .` 로 최상위를 루트로 두면 검사가 테스트 모듈을
  두 번 임포트한다」를 세웠는데 `tests/` 에 `__init__.py` 가 없어 **경로 자체가 안 열린다**
  (`ImportError: Start directory is not importable`).
- **순서 뒤집기 네 방향 전부 605 OK**: 역순(13.438초) · 무작위 seed=1 · seed=20260905 ·
  **모듈 단독 17회**(17/17 OK · rc 0 · 건수 합 **정확히 605**). 역순은 순열 하나뿐이라
  무작위 둘을 얹었고, 가장 센 자는 모듈 단독이다 — 「A 가 심은 것을 B 가 먹고 산다」면
  B 혼자 돌릴 때 죽는데 **한 건도 안 죽었다**.
- **전역 대조 24축 중 3축만 움직인다**(전수를 한 프로세스에서 돌리고 앞뒤를 찍었다):
  `sys.path` **+4** · `logging.Logger.manager.loggerDict` 0→3(`asyncio`·`concurrent`·
  `concurrent.futures` — `import concurrent.futures` 부산물이고 **root 로거의 level·handlers
  무변**) · `tempfile.tempdir` None→경로(`gettempdir()` 의 stdlib 메모이제이션).
  **안 움직인 21축에 `defaultTestLoader` 축 셋이 전부 들어 있다**
  (`testNamePatterns`·`_top_level_dir`·`errors`) — 지금까지 「`-k` 아래 값이 옳다」로
  간접 확인하던 것을 **싱글턴 자체가 안 움직인다**로 처음 직접 쟀다.
- **변이 재판 둘(전부 저장소 밖 사본)**: **D** 사본에서 `TestLoader()`→`defaultTestLoader`
  되돌림 → 움직이는 축이 **3 → 4** 로 정확히 하나 늘고 그것이 `_top_level_dir` 이다,
  같은 사본의 `-k Readme` 는 `(605, 21) != (5, 21)` · `Ran 5` · **FAILED rc 1**(함정 재현).
  **E** 사본 `e2e/tempfile.py` 로 표준 `tempfile` 을 가림 → 전수 `Ran 605` ·
  **FAILED(failures=22)** · rc 1.
- **핵심 발견 — `sys.path` 누출은 실재하고 하위 프로세스까지 전파된다.** 변이 E 의 실패
  22건은 전부 **자식 프로세스의 `import tempfile`** 트레이스백이었다 — 러너들이
  `sys.path.insert(0, E2E)` 를 자식 부트스트랩에 그대로 넘기기 때문이다. 그런데도
  **[5]점으로 등재만 했다**(룰 4절): ① 지금 겹치는 이름이 **0개**다(`tests/`+`e2e/` 모듈
  이름 **38개**를 표준 라이브러리와 대조, 충돌 0 · 서로도 안 겹친다) ② **터질 때 시끄럽게
  터진다** — 거짓 초록이 아니라 즉시 22 FAILED 이고, 이 저장소가 8점을 매겨 온 것은 언제나
  「조용히 초록인 것」이었다 ③ **강제할 규칙을 저장소가 못 지킨다** — 「`sys.path` 에
  남기지 마라」를 검사로 세우면 `TestLoader.discover`(stdlib `loader.py:285`)가 자기도
  위반한다. **고친 줄 자신이 그 규칙의 첫 위반자다.**
- **일반화 — grep 은 「저장소가 쓴 코드」만 보고 전역 대조는 「실제로 움직인 전역」을 본다.**
  이번에 저장소 코드 0자리로 판정한 일곱 축(`logging`·`socket`·`sqlite3` 등)은 grep 만으로는
  «안 쓴다» 까지밖에 못 말한다 — 저장소가 부른 표준 라이브러리가 몰래 바꾼 것은 앞뒤 대조가
  아니면 안 보인다. 실제로 `logging` 과 `tempfile` **둘이 그렇게 잡혔고 둘 다 무해로 판정**됐다.
- 러너 규율 **0회(누적 35)** — 스물여덟 번 전부 맨몸·단독. 모듈 단독 17회에 `for` 루프를
  썼으나 방아쇠가 겨냥한 것은 루프가 아니라 **판정을 가리는 것**이라 러너를 맨몸으로 두고
  `echo "rc=$?"` 를 뒤에 붙여 판정 줄 17개와 rc 17개를 전부 남겼다.
- 한도: 제품 `src/` 0줄 · 저장소 코드 **0줄** · `README.md` 무변 · `data/crawl.db` sha256
  `85c96744…5bda18` 무변 · `docs/specs/` 무변 · `pgrep -f websearch.serve` 0건 ·
  `__pycache__` 0개 · PR 무접촉 · `--no-verify`·`--force` 0 · **자동 스냅샷 안 끼어들었다**.
- 다음: **리뷰 phase.** 리뷰가 볼 것은 「등재 판정 셋, 특히 ③(«stdlib 도 위반한다») 이
  변명이 아닌가」다.

## 2026-09-05 09:00 | loader-isolation | 리뷰 1/1 | 시도0

- **판정은 유지, 근거 둘이 무너졌다.** 백지 패스로 `fe4dd0d..HEAD` 를 다시 읽고 러너 인자 여섯(`-k`×2·`-p`·`--locals`·`-f`·`-t`)을 직접 때렸다 — 전수 `Ran 605 · OK · rc 0`(13.489초), `-k` 둘 다 OK, `-t .` 는 `ImportError` 로 도달 불가(재현). **열거형을 diff 밖에서 셌다**: `unittest.main` 이 로더에 심는 상태는 `testNamePatterns`(`main.py:151`)와 `_top_level_dir`(`loader.py:286`) **정확히 둘**이고 새 인스턴스가 둘 다 닫는다. 전역 대조도 재현(`sys.path` +4 · `defaultTestLoader` 축 셋 무변).
- **[R56-1] 「누출이 프로세스 경계를 넘는다」는 틀린 문장이었다(medium·95·고침).** `sys.path` 는 자식에게 상속되지 않는다 — 마커를 심고 `subprocess.run` 으로 확인해 `CHILD_HAS_MARKER=False`. 자식에 `E2E` 가 있는 이유는 `tests/test_passage_eval.py:47` 이 `-c` 소스에 `sys.path.insert(0, E2E)` 를 **직접 써 넣기** 때문이고, 부모가 완벽히 깨끗해도 똑같이 들어간다.
- **[R56-2] 변이 E 는 누출을 잰 적이 없다(medium·90·고침).** 사본에 `e2e/tempfile.py` 를 다시 심으니 실패가 자식 9건(`<string>` 프레임)과 **같은 프로세스 13건**(`test_quality_eval`, 프레임 없음)으로 갈리는데 **어느 쪽도 «남은 칸» 이 원인이 아니다** — 후자는 `test_quality_eval.py:17` 의 **살아 있는** insert 다. **일반화 — 「전역이 오염됐다」를 재려면 오염이 *남은 뒤*를 재야 한다. 오염이 *켜져 있는 동안* 터지는 것을 재면 다른 현상을 재고 그 값을 원래 항목에 적게 된다.** 항목의 틀도 그래서 틀렸다: 셋 중 둘이 **임포트 시점**(=`discover()` 중, 첫 테스트 전)에 돌아 위험은 「끝에 네 칸 남는다」가 아니라 **`e2e/` 가 전수 내내 `sys.path[0]` 에 앉아 있다**는 쪽이다.
- **[R56-3] ③ 은 사실이나 과장이다(low·85·고침).** `discover` 가 `loader.py:285` 에서 안 빼는 것은 원문 확인으로 참인데 그것이 「검사 불가」를 세우지는 못한다 — 앞뒤 대조가 저장소 몫 `e2e`×3 과 stdlib 몫 `tests`×1 을 **경로로** 가르고, 더 싼 처방(`if E2E not in sys.path` 세 줄)이 따로 있다. **`e2e` 칸이 셋으로 중복되는 것이 그 가드가 없다는 증거다.** `[5]` 값은 유지하고 문장만 고쳤다.
- **판정 ①은 축을 넓혀도 버틴다** — 38파일·고유 스템 38, 충돌이 stdlib **0** · `src/` 스템 **0** · `site-packages` **0**(테스트 phase 는 stdlib 만 봤다). 한도: 저장소 코드 **0줄** · `README.md`·`docs/specs/` 무변 · `data/crawl.db` sha256 `85c96744…5bda18` 무변 · `__pycache__` 0 · `pgrep -f websearch.serve` 0 · PR 무접촉 · 러너 규율 0회(누적 35). 고친 파일은 `docs/digest.md` 문장 둘뿐. 다음: **e2e phase**(21종 전수 회귀).
