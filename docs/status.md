---
signal: DONE
plan: null
mode: night
phase: null
step: null
attempt: 0
iteration: 117
night_iterations: 28
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 117 · 018 DONE)
ctx: 72% / 200k
rules: 1411a37
---

# 현재 상태

**계획 018 `url-normalize` DONE.** 브랜치 `loop/url-normalize` (기점 `e08bc8f`).
계획서는 `docs/plan_history_016.md`, e2e 결과는 `docs/e2e/url-normalize/result.md`.

같은 문서를 가리키는 표기가 여럿이어도 **서버는 한 번만 받고** `pages` 에 한 행이
남는다. `urls.normalize` 가 RFC 3986 6.2.2 의 다섯(스킴·호스트 소문자 · 스킴별
기본 포트 제거 · 빈 경로 `/` · 퍼센트 3연 hex 대문자) + 프래그먼트 제거를 **URL 이
태어나는 세 경계**(`links.extract`·시드·리다이렉트 최종 URL)에 건다.
`to_ascii` 는 안 건드렸다 — 그 계약("ASCII 는 한 글자도 안 바꾼다")이 멱등성과
이중 인코딩 방지를 한 규칙으로 사고, 회귀 위험이 전부 거기 있다.

**실측.** 단위 **379건 OK**. e2e **7종 전부 rc=0** — 새 `url_normalize_e2e.py` 는
표기 7개가 문서 4개로 접히고(`/p` 수신 3회 → 1회), 변이 3종이 각각 **다른
시나리오는 통과시키면서** 자기 단언에서만 죽는다. `domain_key_e2e.py` 는 018 이
그 축을 접어 크게 실패해 **userinfo 축**으로 옮겼고, 되돌리기 변이로 여전히 017
회귀 탐지기임을 확인했다(간격 0.001초).

## 판단 필요 — 사람에게 묻는다

1. **이 변경은 새 DB 에서만 목적을 달성한다.** 기존 `data/crawl.db` 에는 018 이전에
   정규화 안 된 열쇠로 저장된 행이 남고, `store.has(정규화된 URL)` 이 그것을 못 찾아
   같은 문서를 다시 받고 다시 저장한다(재현: `upsert('http://A.com:80/p')` →
   `has('http://a.com/p')` **False** → `pages` 2행 · `docs` 2행 · 검색 결과 2건).
   일회성 통합은 **마이그레이션이라 야간이 안 한다.** recrawl 계획과 같은 수술이다
2. **URL 에 실린 자격증명이 `pages.url` PK 이자 검색 결과 링크가 된다.** `normalize`
   가 userinfo 를 되붙이는 것 자체는 옳지만(떼면 요청 내용이 바뀐다) 그 URL 이 그대로
   DB 열쇠가 되고 `serve.py` 가 렌더한다. **보안 경계라 줄 수 무관 야간 금지**
3. `loop/url-normalize` 브랜치 **머지 판단** (야간은 `main` 에 직접 안 쓴다)

## 다음에 할 일 — 계획 없음

`docs/digest.md ## 다음 계획 후보` 와 `## 판단 필요` 에서 고른다. 지금 위에 있는 것:
recrawl(`store.has` 상태 불문 스킵 + indexer 증분 + **옛 열쇠 행 통합** — 셋이 같은
수술이다) · `--deadline`(Ctrl-C 최악 대기와 총 크롤 시간 예산이 같은 답이다) ·
`X-Robots-Tag` 헤더.

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합 ·
옛 표기로 저장된 기존 행의 마이그레이션(데이터 변경).
