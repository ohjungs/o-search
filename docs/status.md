---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 322
updated: 2026-09-05
ctx: 58
night_iterations: 144
night_red: 2
night_retries: 0
plan: db-state-invariant # 계획 55 — 설계 완료(`docs/design_db-state-invariant.md`) · 다음은 개발 1/1
---

# 현재 상태

**계획 55 `db-state-invariant` 의 설계가 끝났다.** 설계서는
`docs/design_db-state-invariant.md`, 브랜치는 `loop/db-state-invariant`.
**다음 phase 는 개발 1/1** — 설계 5절 계약을 그대로 TDD 로 돈다.

## 설계가 고른 것

**갈림길 1(자의 눈금) → ①' `PRAGMA table_info(pages)`.** 계획서가 연 셋(① `SCHEMA`
파싱 · ② 손 표 · ③ 상태마다 클래스)에 넷째를 더해 그것을 골랐다. 스키마를 읽는
파서는 이미 sqlite 안에 있어 **우리가 쓸 파서가 0줄**이고, 소스 문자열이 아니라
**실제로 만들어진 표**를 잰다. 열을 뺀 `pages` 를 다시 만들 때 쓰는 **선언 타입까지
`PRAGMA` 가 준다**(`r[1]`·`r[2]`) — 손으로 적는 타입 표 0개.

**갈림길 2(제품 처방) → A `SELECT url, html FROM pages LIMIT 0`.** 계획 54 가 심은
줄을 한 낱말 넓힌다. 제품이 읽는 열은 `url`·`html` 둘뿐이고 A 는 **읽는 것만**
요구한다.

## 이 반복이 직접 잰 것 (반복 322 · 임시 DB · `data/crawl.db` 무접촉)

**①' 자를 실물로 세워 돌렸다.** 눈금 `['url','html','status','fetched_at']` 4칸 ·
오늘 코드에서 **RED 정확히 1행**(`url`) · 처방 A 사본에서 **4행 전부 PASS** ·
정상 DB **오탐 0**. ① 파싱도 같은 넷을 냈다 — 오늘 눈금은 같고 갈리는 것은 유지비다.

**첫 초안의 자가 틀린 것을 실측이 잡았다** — 세 질의의 **반환값**을 비교했더니 정상
DB 가 `n=2/n=0/n=0` 으로 **거짓 RED** 였다. 자가 재는 단위는 결과가 아니라 **판정**
(예외 클래스 이름 또는 `ok`)이다. 이 한 줄이 자의 전부다.

**B 를 죽인 것은 오탐이 아니라 expand 함정이었다.** 계획 phase 가 적은 사유(`status`·
`fetched_at` 오탐)를 다시 재서 확인했고, **더 센 사유를 새로 깼다** — 사본의
`store.SCHEMA` 에 `lang TEXT` 를 더하고 **기존 정상 DB** 를 새 코드로 다시 열었더니
`CREATE TABLE IF NOT EXISTS` 가 열을 안 더해 세 질의가 전부
`OperationalError: no such column: lang` 이 됐다. **B 는 열 추가를 사실상 `contract`
단계로 바꾼다** — 읽을 수 있는 DB 를 전면 500 으로 만드는 배포 사고다. A 는 새 열이
질의에 안 들어가 이 함정이 없다.

**탐침 비용**(1,000행 · 행당 6,826바이트 · 200회 × 7반복 최소):
`SELECT html … LIMIT 0` **0.0014ms** · `SELECT url, html … LIMIT 0` **0.0015ms** ·
`LIMIT 1` **0.0087ms**. 넓히는 값은 잡음이고, 계획 54 의 `LIMIT 0` 선택은 유효하다.

## 개발이 지킬 계약 (설계 5절)

제품은 `src/websearch/indexer.py` `passages()` 의 그 줄 **한 낱말** — 자리(가드 직후 ·
루프 앞)·시그니처 무변. **그 줄 위 `ponytail:` 주석 두 문장이 거짓이 되므로 같은
커밋에서 고친다**(계획 54 리뷰가 잡은 두 건이 전부 새로 쓴 주석의 거짓이었다).
자는 `tests/test_indexer.py` `TestPassages` 옆 새 클래스 하나 — HTTP 안 띄운다.
**`tests/test_serve.py` 에 새 클래스 0개**: `url` 축이 더하는 것은 새 *상태*지 새
*매핑*이 아니고 `OperationalError → 500` 은 `TestPassagesWithoutHtmlColumn` 이 이미
붙들고 있다. **자의 자기검사 단언**(열 4칸 이상 · `url`·`html` 포함)이 「0행을 재고
조용히 초록」을 막는다.

## 범위 (하드 제약 확인)

단위 **603 OK**(13.559초 · 맨몸·단독 · rc 0 · 새 설계 문서 포함해 `DocCitationTest`
통과) · 제품 `src/` **0줄**(설계 phase) · `main` 직접 커밋 0 ·
`--no-verify`·`--force` 0 · **PR 무접촉(조회 0회)** · `docs/specs/` 무변 ·
`data/crawl.db` sha256 `85c96744…5bda18` **무변**(실측은 전부 임시 디렉터리의 사본) ·
스키마·마이그레이션·재색인 0 · 새 의존성 0 · stdlib 만 · 띄운 서버 0개 ·
**러너 규율 위반 0회**(모든 실행이 맨몸, 판정 줄과 rc 까지 봤다).

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **브랜치 병합** — 원격 `main` 은 `c0be72f`, 계획 54(PR #9)까지 들어 있다.
   `loop/db-state-invariant` 의 병합은 사람 몫이고 `main` 직접 커밋은 하지 않는다.
   **이 반복도 PR 을 조회조차 안 했다.**

## 정지 사유

없음 — 계획 55 **개발 1/1** 로 이어간다.
