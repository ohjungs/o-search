---
signal: GREEN
mode: night
plan: noindex-respect
phase: 설계
step: 0/3
attempt: 0
iteration: 22
night_iterations: 1
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 22)
ctx: 72% / 200k
rules: null
---

# 현재 상태

**`plan_noindex-respect.md` 작성 완료 — 설계 phase 로 넘어간다.**
indexer(002) DONE 이후 다음 계획으로 `search-api` 가 아니라 `noindex-respect` 를 골랐다.
근거: `docs/digest.md` 보류 [85·높음] 이 실측(noindex 페이지가 검색 1위)으로 남아 있고,
`docs/specs/concept.md` 갈림길 우선순위에서 **크롤 윤리가 1순위**라 검색 API 보다 위다.
윤리 결함 위에 API 를 올리면 나중에 걷어내는 비용이 커진다. 이 계획을 닫고 search-api 로 간다.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **설계 phase — `docs/design_noindex-respect.md` 작성** (`rules/design.md`).
  `docs/plan_noindex-respect.md` 의 "설계" 절이 결정할 것 3가지를 이미 적어놨다:
  ① 판정 함수의 시그니처와 위치 ② 이미 색인된 문서를 빼는 방식 ③ 그 선택의 성능 천장
- 근거: 설계 트리거 2개에 걸린다 — 대안 갈림(색인 시점 판정 A vs 수집 시점 차단 B),
  공개 인터페이스 추가(`src/websearch/extract.py` 에 판정 함수 하나)
- 완료 기준: `design_noindex-respect.md` 에 대안 A/B 비교와 채택 사유가 있고,
  스텝 1·2 가 그대로 구현에 들어갈 수 있는 계약(함수 시그니처·판정 규칙)이 확정된다
- 이미 한 것: 계획서·`docs/index.md` 갱신·브랜치 `loop/noindex-respect` 생성까지.
  코드는 한 줄도 건드리지 않았다

### 설계에서 반드시 볼 것 (이미 실측으로 확인한 사실)

- `src/websearch/indexer.py:22-30` 의 증분 조건이 `url NOT IN (SELECT url FROM docs)` 라
  **이미 색인된 문서는 다시 쳐다보지 않는다.** "이미 색인된 noindex 를 뺀다"는 이
  조건을 우회하는 경로가 따로 필요하다 — 전수 재판정이면 매 실행 O(전체 문서) 파싱이므로
  값싼 사전 필터(문자열 포함 검사)를 저울질할 것
- `src/websearch/fetcher.py:13-17` 의 `FetchResult` 는 헤더를 버린다 →
  `X-Robots-Tag` 는 스키마 변경 없이는 불가. 야간 금지 항목이라 계획에서 범위 밖으로 뺐다
- `src/websearch/extract.py` 에는 이미 `_TextParser`(html.parser) 가 있다.
  새 파서를 만들기 전에 이걸 재사용할 수 있는지 먼저 본다 (ponytail 2번)

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 설계 phase 부터 이어진다.

## 정지 사유

(진행 중)
