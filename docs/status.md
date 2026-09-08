---
signal: GREEN
phase: 개발
step: 1/3
attempt: 0
iteration: 471
updated: 2026-09-08
ctx: 34
night_iterations: 3
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 개발 1/3 완료.** 크롤이 팝 지점에서 「저장돼 있나」 대신 **「아직 신선한가」**
를 묻는다 — 사양 기능 5 의 재방문이 여기서 열렸다. 전수 **695 OK**.

다음 반복은 **개발 2/3** — 워터마크 루프의 **갱신**. 계약은 `docs/design_recrawl.md`
3절(판정 순서 2·4번 갈래)과 4절(워터마크가 있을 때만 돈다)이다.

## 이번 스텝이 놓은 것

- `store.is_fresh(url)` — 시각 비교를 **SQLite 가** 한다
  (`datetime('now', CASE WHEN status BETWEEN 200 AND 299 THEN ? ELSE ? END)`).
  `store.has` 는 안 건드렸다 — 리다이렉트 도착지 검사(`crawl.py:337`)는 뜻이 다르다.
- `store.FRESH_DAYS`=30 · `RETRY_DAYS`=15. `project.md` 「품질 기준」이 값까지 인용해
  `ProjectConstTest` 가 문다. **되돌리기는 이 상수 한 줄이다**(플래그가 아니라).
- 테스트 10건(신선도 6 · 크롤 배선 4)을 먼저 빨갛게 보고 초록으로 만들었다.

## 다음 반복이 알아야 할 것 둘

1. **`TestCooldownBurn` 의 가짜가 이제 `is_fresh` 를 가린다.** 팝 지점의 문을 또 옮기면
   그 이음매도 같이 옮겨야 한다 — 안 옮기면 「안 보낸 URL 이 쿨다운을 태웠다」가 뜬다.
2. **변이 검사에는 `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX` 를 반드시 건다.**
   이번에 `RETRY_DAYS`→`FRESH_DAYS` 변이가 **길이가 같아** 파일 크기가 안 변했고 되돌림이
   같은 초에 일어나, 되돌린 뒤에도 낡은 pyc 가 20분 동안 빨간불을 냈다.

## 아직 안 건드린 것 (스텝 2·3)

`indexer.py` 는 그대로다 — `pages.status` 를 여전히 안 읽고, 워터마크 루프의 `SELECT` 에
`html IS NOT NULL` 도 없다. **이 스텝이 그 잠복 크래시로 가는 길을 열었으므로**
(404 재수집 → `html` NULL) 스텝 2 에서 `html IS NULL` 갈래를 `is_noindex` **앞**에 둔다.

전문: `docs/design_recrawl.md` · 스텝: `docs/plan_recrawl.md` 4절
