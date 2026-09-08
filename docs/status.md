---
signal: GREEN
phase: 개발
step: 0/3
attempt: 0
iteration: 470
updated: 2026-09-08
ctx: 38
night_iterations: 2
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 `recrawl` 설계 완료.** 다음 반복은 **개발 1/3** — `store.is_fresh()` +
`crawl.py:250` 배선. 계약은 `docs/design_recrawl.md`, 스텝은 `docs/plan_recrawl.md` 4절.

## 설계가 고른 것 — 새 구조를 안 만든다

재방문은 `store` 술어 **하나**, 갱신·삭제는 계획 78 이 만든 **워터마크 루프 안**에서
`p.status` 열 하나를 더 든다. 스키마·마이그레이션 0줄 · 새 파일 0개.

**C(플래그)를 버린 이유가 이 설계의 요지다** — TTL 30일이라 실물 코퍼스(2026-09-07 수집)는
**10월 7일까지 요청을 한 건도 더 안 보낸다.** 기능은 켜는 순간 잠들어 있어 되돌릴 것이
없고, 되돌리기는 플래그가 아니라 상수 `FRESH_DAYS` 한 줄이 준다.

## 설계 중에 잰 것 둘

- **신선도 SQL 을 실제로 돌렸다** — `datetime('now', CASE WHEN status BETWEEN 200 AND 299
  THEN ? ELSE ? END)`. 31일 200 낡음 · 29일 신선 · 16일 404 낡음 · 14일 신선 ·
  없는 URL 낡음. 시계를 SQLite 하나로 두는 이유는 계획 78 이 그 자리에서 빨개져서다.
- **재추출 비용을 실물 60문서로 쟀다** — 문서당 **23.81ms**(`is_noindex` 만은 10.70ms).
  10만 환산 **39.7분**이라, 워터마크 없는 전수에서 재추출하면 계획 78 이 35배로 줄인
  고정비가 두 배로 돌아온다. **그래서 갱신·삭제는 워터마크가 있을 때만 돈다** —
  `store.upsert` 가 언제나 `fetched_at` 을 박으므로 「안 바뀐 것」이 보장된다.

## 설계가 찾은 잠복 크래시 하나

`is_noindex()` 첫 줄이 `html_text.lower()` 인데 워터마크 루프의 `SELECT` 에는
`html IS NOT NULL` 이 없다. **`html` 이 NULL 이 되는 유일한 길이 재크롤(404 재수집)이라
오늘은 안 터지고, 이 계획이 그 길을 여는 순간 터진다.** 판정 순서에서 `html IS NULL`
갈래를 `is_noindex` **앞**에 둔다(계약 3).

## 천장 하나를 적어 두고 간다

**갱신 건수는 아무도 안 센다** — 세려면 `index_pages()` 반환 계약을 바꿔야 하고 호출자가
**10파일 65곳**이다. 밤에 그 리팩터링은 안 연다. 재크롤이 실제로 도는 날 올린다.

전문: `docs/design_recrawl.md`
