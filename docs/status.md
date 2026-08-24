---
signal: DONE
mode: night
plan: null
phase: 계획
step: 3/3
attempt: 0
iteration: 28
night_iterations: 7
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 28)
ctx: 71% / 200k
rules: null
---

# 현재 상태

**noindex-respect 계획 DONE — e2e 통과, 아카이브 003 완료.**
세 번째 계획이 닫혔다. 전체 90/90 통과, 야간 RED 0·재시도 0.
`docs/digest.md` 보류 [85](색인이 meta noindex 를 무시)를 닫았다 —
크롤 윤리 축이 robots.txt(001) 에 이어 meta robots 까지 덮인다.

이제 색인 명령은 `<meta name="robots">` 의 noindex·none 을 존중한다.
이미 색인된 문서가 뒤늦게 거부를 선언해도 다음 실행에서 빠지고, 그 사실을 출력한다.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **다음 계획 착수 — `search-api`** (`docs/index.md` 사양 분할 4번).
  질의 → 랭킹 결과 API. 컨셉 성능 1(p95 300ms)의 측정이 여기서 시작된다
- 근거: `docs/index.md` 의존 순서상 남은 것 중 가장 앞. `indexer.search()` 가
  이미 (url, title, snippet) 을 bm25 순으로 돌려주므로 HTTP 껍데기 + 측정이 핵심이다
- 완료 기준: 계획 phase 이므로 `rules/plan.md` 로 `docs/plan_search-api.md` 를 쓴다.
  중복 확인은 `docs/index.md` + `docs/digest.md`
- 이미 한 것: 없음 (착수 전)

### 계획을 쓸 때 반드시 반영할 것 (digest 에 근거 있음)

- `search()` 의 질의 재작성은 신뢰 경계다. HTTP 파라미터가 붙는 순간 NUL·제어문자
  경로가 실제로 도달 가능해진다 — 이미 막아뒀지만 API 계층에서 다시 확인
- "판단 필요" 의 [8] 증분이 재크롤 갱신 미반영 — API 가 옛 본문을 서빙하게 되므로
  recrawl 계획을 앞당길지 판단
- **반복 실패 3회째 주의**: CLI 진입점마다 방어를 따로 쓰는 문제(digest "반복 실패").
  HTTP 핸들러는 세 번째 진입점이다 — 같은 부류가 또 나온다
- 크롤 윤리 잔여 항목: robots `crawl-delay` 존중(digest, 높음),
  `X-Robots-Tag` 헤더(스키마 expand 필요라 무인 보류)

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 이어진다.
DONE 처리는 끝났으므로 다음 세션은 계획 phase 부터 시작한다.

## 정지 사유

(진행 중)
