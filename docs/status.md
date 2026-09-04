---
signal: GREEN
phase: e2e
step: 1/1
attempt: 0
iteration: 325
updated: 2026-09-05
ctx: 52
night_iterations: 147
night_red: 2
night_retries: 0
plan: db-state-invariant # 계획 55 — 리뷰 1/1 완료(지적 4 · 자동수정 2) · 다음은 e2e
---

# 현재 상태

**계획 55 `db-state-invariant` 의 리뷰 1/1 이 끝났다.** 원격 `main` `c0be72f` 부터
HEAD 까지 **여섯 커밋 전부**를 백지 패스 먼저로 봤고, 지적 넷 중 둘을 그 자리에서
고쳤다(`src/` **0줄**). 브랜치는 `loop/db-state-invariant`. **다음 phase 는 e2e 다.**

## 이 반복이 직접 잰 것 (반복 325)

적힌 숫자를 하나도 안 믿고 다시 쟀다. **전수** `PYTHONPATH=src python3 -m unittest
discover -b -s tests` 를 맨몸·단독(러너를 파이프 왼쪽에 안 둔다)으로 **605건 OK ·
13.494초 · rc 0**. 리뷰가 고친 뒤 다시 **605건 OK · 13.504초 · rc 0**.

**변이 재측** — 전부 저장소 밖 **전체 사본**(`rsync`)에서 · `PYTHONDONTWRITEBYTECODE=1`.

| 변이 | 결과 |
|---|---|
| ① 처방 되돌리기 (`SELECT url, html` → `SELECT html`) | **RED 1/605** — `missing='url'`, `{'김치찌개': 'OperationalError', 'zzzznope': 'ok', '\x01': 'ok'}` |
| ② 눈금 0칸 (`_columns` → `[]`) | **RED** — `0 not greater than or equal to 4` |
| ③ `DOC` 을 `된장찌개` 로 | **RED** — 자기검사 2 만, `[False, False, False]` |
| ⑤ **새로 심었다** — 루프를 `SELECT html, status … WHERE url = ?` 로 넓히고 탐침은 그대로 | **RED 1/605** — 그 하나가 새 자(`missing='status'`) |

**⑤가 이 계획의 앞날 주장을 실증한다.** 코드 주석이 *"셋째 열을 읽게 되면 그 열을 여기
더한다 — 자가 그날을 잡아 준다"* 라고 적었는데, 그 날을 흉내 내니 605건 중 **오직 새 자**가
울었다. 계획 55 가 「자리를 넓히는 대신 원칙을 세운다」를 실제로 한 것이 맞다.

**실서버 실측** — `--port 0` 으로 띄우고 `url` 열이 없는 DB(저장소 밖)를 먹였다.
`/passages` 는 세 질의 전부 **500**이고 본문이 셋 다
`{"version": 1, "error": "검색 중 오류가 났다"}` 다. `/search` 는 같은 DB 에서 200 셋인데
**이것이 정상이다** — FTS `docs` 는 `content=` 없는 독립 표라 `pages` 를 안 읽는다
(`indexer.py:15`). 같은 DB 에 `indexer` CLI 는 rc 1. 서버는 끝내기 전에 죽였다.

**보안(CSO) 통과** — sqlite 문구는 응답 본문에 **안 실린다**. 서버 stderr 로그에만
`/passages 실패: OperationalError('no such column: url')` 로 남는다. 경로·스키마 노출 0.

## 지적 넷 (자동수정 2 · 보고만 2)

- **[R55-1] low · 고침** — `_drop_column` 이 다시 만드는 표가 `PRIMARY KEY`·`NOT NULL`·
  `DEFAULT` 를 잃는다(실측: `url` 뺀 표가 `html TEXT, status INTEGER, fetched_at TEXT`).
  `PRAGMA table_info` 는 이름·타입까지만 준다. 판정 영향은 0 이지만 주석이 *"실제로
  만들어진 표를 잰다"* 라 절반만 참이었다 → `ponytail:` 천장 네 줄을 더했다.
- **[R55-2] low · 고침** — README 재작성(`c8827e9`)이 품질 표에서 **비텍스트 명암비
  3:1** 을 지웠다. `e2e/design_check.py` 는 계속 잰다(`MIN_CONTRAST_NONTEXT = 3.0`)이고
  아래 「사람 결정 대기」 2번이 바로 그 기준 얘기다 → 셀 한 줄 복원.
- **[R55-3] low · 보고만** — 같은 재작성이 `/passages` 응답 스키마
  `{url,title,position,text}` 와 rc 표의 「어디서」 열도 지웠다. 쉬운 말로 옮긴 편집
  의도가 분명해 되돌리지 않는다. 되살릴 거리는 다음 문서 반복 몫이다.
- **[R55-4] low · 보고만** — 설계 5절이 `README.md` 를 범위 **밖**으로 적었는데 테스트
  스텝은 고칠 수밖에 없었다(`tests/test_readme.py` 의 `UNIT_COUNT` 가 숫자를 강제한다).
  **계약 문구가 반증됐다** — 다음 계획서는 *"README 는 숫자 가드가 강제하는 줄만"* 이다.

**거짓양성으로 버린 것 하나.** 「자가 일관성만 재니 «일관되게 틀린» 상태를 통과시킨다」를
변이로 확인했다(탐침 삭제 + 루프에서 `except OperationalError: continue`). 새 자는 초록인데
**계획 53·54 클래스 8건이 죽었다** — 저장소가 이미 덮고 있어 `severity.md` 의 「이미 충분히
덮는 단언을 더 조일 수 있다」에 걸린다. `metrics.md` 가 같은 것을 이미 적어 두었다.

## 범위 (하드 제약 확인)

`src/` **0줄** · `serve.py`·`store.py`·스키마·마이그레이션·재색인 **0** · 새 의존성 0 ·
stdlib 만 · 고친 파일 **둘**(`tests/test_indexer.py` 주석 +4줄 · `README.md` 셀 1줄) ·
`docs/specs/` 무변 · `data/crawl.db` sha256 `85c96744…5bda18` **무변**(변이는 전부
저장소 밖 전체 사본) · 서버 잔여 0(`pgrep -f websearch.serve` 0건) · `main` 직접 커밋 0 ·
`--no-verify`·`--force` 0 · **PR 무접촉(조회 0회)** · 브랜치 병합 시도 0 ·
e2e 21종 전수는 **e2e phase 몫**.

**푸시 대조** — 아래 「푸시」 절에 실측을 적는다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **브랜치 병합** — 원격 `main` 은 `c0be72f`, 계획 54(PR #9)까지 들어 있다.
   `loop/db-state-invariant` 의 병합은 사람 몫이고 `main` 직접 커밋은 하지 않는다.
   **이 반복도 PR 을 조회조차 안 했다.**

## 정지 사유

없음 — 계획 55 **e2e** 로 이어간다.
