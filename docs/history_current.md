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
