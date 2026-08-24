---
signal: GREEN
mode: night
plan: search-api
phase: 설계
step: 0/5
attempt: 0
iteration: 29
night_iterations: 8
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 29)
ctx: 71% / 200k
rules: null
---

# 현재 상태

**`plan_search-api.md` 작성 완료 — 설계 phase 로 넘어간다.**
직전 계획 noindex-respect(003)는 DONE·아카이브 완료다. 전체 90/90 통과 상태에서 출발한다.
이 계획의 절반은 API 자체이고 절반은 **성능 축 측정의 시작**이다 —
`docs/project.md` 품질 기준의 "성능 측정: 없음" 을 채운다.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **설계 phase — `docs/design_search-api.md` 작성** (`rules/design.md`).
  `docs/plan_search-api.md` "설계" 절에 트리거 3개와 결정할 것 4개를 적어놨다
- 근거: 트리거 ① 새 모듈(`src/websearch/serve.py`) ② 공개 인터페이스 변경
  (`indexer.search()` 에 offset 이 필요한데 지금은 `limit` 만 받는다)
  ③ 대안 갈림(요청마다 새 sqlite 연결 vs 재사용 — `http.server` 는 요청마다 스레드이고
  sqlite 연결은 스레드를 넘지 못한다. p95 에 직접 영향)
- 완료 기준: 대안 비교와 채택 사유, 응답 JSON 키 이름, 연결 전략, 측정 스크립트의
  측정 방식(질의 셋·반복 횟수)이 확정돼 스텝 1·2·4 가 그대로 구현에 들어갈 수 있다.
  `rules/design.md` 3-2절대로 **가장 위험한 가정 하나를 탐침으로 깨보고** 결과를 적는다
- 이미 한 것: 계획서 작성·`docs/index.md` 갱신·브랜치 `loop/search-api` 생성.
  코드는 한 줄도 안 건드렸다

### 설계에서 반드시 볼 것

- **CLI 진입점 방어가 반복 실패 2회로 기록돼 있다**(`docs/digest.md` "반복 실패").
  HTTP 핸들러는 세 번째 진입점이다. 방어를 한 자리에 모으는 구조를 설계에서 정한다
- `indexer.search()` 의 질의 재작성(`_fts_query`)은 이미 NUL·제어문자·FTS5 문법 문자를
  막는다. HTTP 파라미터가 붙으면 그 경로가 **실제로 도달 가능**해지므로 테스트로 다시 고정
- 컨셉 경량 3: 새 의존성 없이 `http.server` 로 간다. 안 되는 것이 실측으로 나오면 그때 연다

## 다음 행동

`/loop-harness night` 또는 `/loop-harness` 를 다시 부르면 설계 phase 부터 이어진다.

## 정지 사유

(진행 중)
