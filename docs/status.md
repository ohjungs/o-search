---
signal: GREEN
phase: 설계
step: 0/3
attempt: 0
iteration: 469
updated: 2026-09-08
ctx: 38
night_iterations: 1
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 `recrawl` 계획 phase 완료.** 다음 반복은 **설계**다 — 트리거 3개 해당
(파일 3개 이상 · 대안 갈림 · 신선도 판정의 정본 자리). `docs/plan_recrawl.md` 4절이 스텝 셋.

## 탐색이 이것을 고른 근거

1~4순위 **0건** — 전수 **685 OK rc 0** · 린터 없음 · 코드 `TODO` 0건(유일 히트
`tests/test_indexer.py:824` 는 픽스처 문자열) · `docs/candidates.md` 없음.
5·6순위에서 **여는 조건이 오늘 열린** 항목을 잡았다: digest `[8]` + `[high]`(재크롤).

`concept.md:31` 기능 5 는 `index.md` 사양 분할 **8번 중 유일하게 남은 미착수**고,
막던 사유 둘이 다 사라졌다 — ① 스키마·마이그레이션은 반복 462 가 재서 **0줄**이고
② 정책 셋은 **2026-09-08 사용자가 위임해 digest 에 답이 적혔다**.

## 실물로 다시 잰 것 (계획을 추측으로 쓰지 않는다)

`data/crawl.db` — `pages` **400** · `docs` **361** · status 분포 **`200: 400`** ·
`html NULL` 0 · `fetched_at` 400/400(`09-07 09:09:12`~`09:11:01`) · 30일 초과 **0건** ·
`index_meta` **아직 없음**(`index_pages()` 가 만든다).

**실패 행이 0건이라는 것이 계획을 하나 좁혔다** — 연속 실패 백오프는 눈금이 없어
「하지 않을 것」으로 갔다. 실패 재시도는 15일 고정으로 시작한다.

## 결함 셋은 오늘도 그대로다

- **재방문 0** — `crawl.py:250` `store.has(url)` 이 상태·시각 불문 스킵
- **갱신 0** — `pages.html` 을 갈고 재색인하면 새 본문 영영 0건 · 옛 본문 1건
- **삭제 0** — `indexer.py` 가 `pages.status` 를 **한 번도 안 읽는다**(`indexer.py:404`)

전문: `docs/plan_recrawl.md`
