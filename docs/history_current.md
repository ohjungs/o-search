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
