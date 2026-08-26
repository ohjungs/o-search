---
signal: GREEN
mode: night
plan: search-ui
phase: 설계
step: 0/2
attempt: 0
iteration: 73
night_iterations: 10
night_red: 0
night_retries: 0
night_self_amendments: 1
updated: 2026-08-27 (반복 73)
ctx: 83% / 200k
rules: rules/plan.md, rules/design.md
---

# 현재 상태

**`search-ui` 계획 phase 완료.** 브랜치 `loop/search-ui` (기점 `loop/crawl-throughput` —
`main` 이 없는 저장소다). 계획서: `docs/plan_search-ui.md`. 다음은 **설계 phase**.

## 보류를 푼 근거 (반복 72 의 판정을 뒤집는다)

반복 72 는 `search-ui` 를 **사람 판단 대기**로 세웠다. 사유는 "경량·디자인 축의
측정 명령이 없음". **그 판정이 틀렸다.**

`project.md` 의 그 두 줄은 이렇게 적혀 있었다:

> **번들 크기**: 없음 — search-ui 계획에서 JS 50KB(gzip) 측정 명령 추가 예정
> **디자인 검사**: 없음 — search-ui 계획에서 추가 예정

"없음"을 **승인 대기**로 읽었는데, 문장이 실제로 말하는 것은 **"아직 안 만들었고,
만드는 것은 search-ui 계획의 일"** 이다. `rules/e2e.md` 4절이 바로 그 경우를 다룬다 —
측정 수단이 없으면 계획이 만든다. 사람에게 물을 것이 없다.

**교훈(digest 후보):** `project.md` 에 "없음"이라고 적을 때는 **누가 채우는지**를
같은 줄에 적어야 한다. 안 적으면 다음 discover 가 그것을 차단 사유로 읽는다.
이번에는 마침 적혀 있었는데도 헤더의 "없음"만 보고 막혔다.

## 계획 요약

**문제**: `concept.md:5-6` 이 제품으로 정의한 "브라우저로 접속해 검색"이 없다.
지금 있는 것은 `GET /search` 의 JSON 뿐이다(`src/websearch/serve.py:68-76`).
그리고 `concept.md:49-54` 의 디자인 4축(LCP 1.5s · JS 50KB gzip · 대비 4.5:1 ·
360px 가로 스크롤 없음)을 **기계가 판정할 수단이 하나도 없다.**

**스텝 2개** (작업 그래프: A → B, 곁가지 없음. 병렬 없음)

| 스텝 | 노드 | 건드릴 파일 | 완료 기준 |
|---|---|---|---|
| 1 | HTML 검색 화면 | `src/websearch/serve.py`, `tests/test_serve.py` | 전체 테스트 통과 · XSS 단언 4자리 |
| 2 | 디자인 4축 측정 | `e2e/design_check.py`(신규), `docs/project.md` | `design_check.py` 종료 0 · `project.md` 실측 갱신 |

**타협하지 않는 것**: 이스케이프(질의어·제목·URL·스니펫 4자리 전부 — 남이 쓴
문자열이 HTML 로 다시 나가는 자리다), 접근성 기본(라벨·대비 4.5:1·키보드),
**JSON API 무손상**(`e2e/search_api_e2e.py`·`e2e/perf_search.py` 회귀).

**범위 밖**: 랭킹/검색 품질, 페이지네이션 UI, 정적 파일 서빙, 실제 네트워크.

## 다음 phase — 설계

`rules/design.md` 1절 트리거 **4개** 걸림(새 파일 · 새 공개 엔드포인트 ·
3파일 이상 · 대안 2개 이상). 설계가 고를 갈림길 둘:

1. **HTML 을 어디로 내나** — (가) `/search` 에서 `Accept` 협상 · (나) `/` HTML +
   `/search` JSON 유지 · (다) 정적 HTML + `fetch()`.
   판정 기준: 되돌릴 수 있나 · 기존 JSON 계약을 깨나 · `concept.md:49`("화면은 둘뿐").
2. **대비 4.5:1 을 무엇에 대고 재나** — CSS 캐스케이드를 재현하지 않고 색 쌍을
   얻어야 한다. 검사기가 기대값을 따로 들면 CSS 와 **드리프트**한다(색을 고쳐도
   검사기는 옛 값을 본다). 드리프트하지 않는 쪽을 고른다.

**LCP 는 브라우저 없이 직접 못 잰다.** 야간에 의존성(헤드리스 브라우저)을 추가하는
것은 정지 조건이다. 그래서 대리 지표(외부 서브리소스 0 · 문서 gzip 크기 · 서버 왕복)로
간다 — **천장을 아는 타협이다.** 설계가 이 천장을 문서에 명시한다.

## 참고 — 시안이 이미 있다

스크래치패드의 `demo_ui.py`(151줄): 서버 렌더 HTML · JS 0KB · 폼 GET ·
`html.escape()` · `prefers-color-scheme` 다크. **형태는 맞지만 그대로 복사하지 않는다** —
자체 `build_db`, 하드코딩된 예시 링크, `real.db` 탐색은 저장소가 쓰지 않는 것이다.

## 직전 계획

**`crawl-throughput`(008) DONE** — 초당 0.5문서 → **10.25문서**(기준 5.0의 2배).
간격 위반 0 · 중복 0. 1,700문서에서 크롤을 죽이던 `database is locked` 를 WAL +
`timeout=30` 으로 닫았다. e2e 4/4 · 테스트 213/213.
자세한 것은 `docs/plan_history_008.md`, `docs/design_history_008.md`,
`docs/e2e/crawl-throughput/result.md`.
