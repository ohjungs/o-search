---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 409
updated: 2026-09-07
ctx: 72
night_iterations: 1
night_red: 0
night_retries: 0
plan: index-e2e-verdict
---

## 현재 상태

**계획 71 `index-e2e-verdict` 착수 — 계획서 `docs/plan_index-e2e-verdict.md` 작성 완료.**
브랜치 `loop/index-e2e-verdict`(기점 `main`). 다음 반복은 **개발 phase 스텝 1/1**.
야간 모드 시작이라 `night_*` 셋을 0 으로 리셋하고 이번 반복을 1 로 셌다.

## 이번 phase 가 산 것

**탐색 1~5순위가 빈손이라는 것을 명령으로 확인하고, 6순위 대신 직전 반복이 남긴 입력을 샀다.**

- **1순위** 전수 `Ran 639 tests in 15.798s` `OK` rc 0 — 실패 0
- **2순위** 린트·타입체크 **없음**(`project.md`) — 해당 없음
- **3순위** `src/`·`e2e/`·`tests/`·`scripts/` 의 `TODO|FIXME|HACK` **1건**이고 그것은
  `tests/test_indexer.py` 의 **HTML 픽스처 문자열 안**이다 — 실행되는 코드가 아니라 근거가 아니다
- **4순위** `docs/candidates.md` **파일 없음** · **5순위** `digest ## 보류` **빈 절**
- **6순위** 후보 두 절의 열린 항목 상위는 전부 **여는 조건이 안 찼다** — `[9]` 는 실물 크롤
  코퍼스, `[8]` 뒷절반(`<nav>` 인라인 연접)은 `_INLINE_TAGS` 가 색인 경로와 공유라 **재색인**
  (야간 금지), `[7]` 페이지네이션은 파일 자신이 *"루프가 열 계획이 아니라 사람이 정할 갈림길"*,
  계획 69 리뷰의 `</head>` 컷은 recrawl 증분 뒤 예산을 밟는 날이 조건이다

**근거는 직전 반복(408)이 `## 다음` 에 적어 둔 둘 중 하나다** — `index.md` 의
`plan_noindex-entity-prefilter` 행이 **e2e 칸에 판정이 아니라 날짜**(`2026-09-07`)를 담고 있고
재는 자가 없다. 실물로 확인했고(그 계획의 진짜 판정은 `docs/e2e/noindex-entity-prefilter/result.md`
에 `통과` 로 있다 — 일이 아니라 기록이 틀렸다) 같은 표의 스텝 칸은 계획 60, 상태 칸은 계획 70 이
이미 재고 있어 **다섯째 칸만 비어 있다**.

**착수 탐침이 설계 갈림길을 죽였다** (읽기 전용 · 워킹트리 무변경). 계획 행 47개를 파싱:
날짜뿐인 칸 **1** · `통과` 라는 낱말이 없는 행 **7**. 뒤의 여섯은 `없음(…)` 둘과
`**새 e2e 0개**(…)` 넷으로 **전부 정당한 판정**이라, 「e2e 칸은 `통과` 로 시작해야 한다」안은
**오탐 6건**으로 탈락한다. 남은 안은 하나 — **어휘를 요구하지 않고 날짜를 거절한다**
(오늘 실물 오탐 0 · 진탐 1). 저울질이 아니라 측정이 골랐으므로 **설계 생략**이다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 639 tests in 15.798s · OK · rc 0
```

계획서 초안이 `index.md` 를 **줄번호로 5자리** 인용해 `DocCitationTest` 에 걸렸다(계획 42 가
세운 자 · 계획 70 에 이은 두 번째 사례). 전부 이름 인용으로 바꿨고, 가드가 안 무는
산문 속 행번호(`57행`·`26~31행`)도 슬러그로 갈아 끼웠다 — **행이 늘면 썩는 주소**라 같은 결함이다.

`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** · 새 의존성·스키마·
마이그레이션·재색인 **0** · 바깥 네트워크 0 · `main` 직접 커밋 0 · PR #7 무접촉.

## 다음

**개발 phase 스텝 1/1** — `rules/dev.md` 0절대로 **먼저 빨갛게 만든다**:
`tests/test_docs.py` 에 `verdict_gap` + `VerdictSyncTest`/`VerdictGapTest` 를 심어 실물
`docs/index.md` 에서 `plan_noindex-entity-prefilter` 를 이름으로 대고 실패하는 것을 본 뒤,
그 행의 다섯째 칸을 `docs/e2e/noindex-entity-prefilter/result.md` 의 판정으로 고친다.
완료 기준 7판(M0~M6)은 계획서 4절에 있다.

**이 반복이 회전을 밟았다** — append 후 `history_current.md` 가 315줄이라 상한 300(`rules/docs.md`
3절)을 넘겨 반복 400~403(계획 69 개발~e2e)을 `docs/history_071.md` 로 밀어냈다.
남은 **192줄** · `digest.md` 아카이브 명부에 이름 등재 · 원본 무손실.

**사람 몫으로 남긴 것 하나** — `digest.md` 는 **214줄로 상한 200 을 여전히 넘는다**.
직전 회전이 같은 자리에서 못 지운 이유에 하나가 더 붙었다: ① 지울 수 있는 완료 항목이
**여덟 줄**뿐이라 14줄이 산술적으로 안 나오고 ② **무인 모드는 파일·데이터를 삭제하지 않는다**.
무엇을 버릴지는 아침에 사람이 정한다 — 야간 보고서에 올린다.
