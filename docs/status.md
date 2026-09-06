---
signal: GREEN
phase: review
step: 1/1
attempt: 0
iteration: 401
updated: 2026-09-06
ctx: 48
night_iterations: 196
night_red: 2
night_retries: 4
plan: noindex-entity-prefilter 계획 69 (테스트 1/1 완료 · 리뷰 phase 대기)
---

## 현재 상태

**계획 69 `noindex-entity-prefilter` 테스트 1/1 끝냈다 · GREEN.**
브랜치 `loop/noindex-entity-prefilter` · 계획서 `docs/plan_noindex-entity-prefilter.md` ·
전수 **632건 `OK`** · e2e `noindex_e2e.py` rc 0 · 이번 phase 의 `src/` 변경 **0줄**.

## 이번 phase 가 산 것

**넓은 필터를 좁히면 미탐으로 되돌아간다는 것을 단언으로 못박았다.**

갭 탐색에서 실제로 쓰이는 인코딩 변형 넷을 실측했다 — `&#82;OBOTS`(대문자 R) ·
`&#0114;`(0 패딩) · `&#114obots`(세미콜론 없음) · `content="&#110;oindex"`(content 쪽
인코딩). **넷 다 이미 True 였다** — 제품은 안 고치고 `test_entity_encoded_name_is_a_directive`
안에 단언 4줄만 더했다. 중요도 **8**: 미탐은 남의 색인 거부를 무시하고 색인하는 것이다.

새 메서드가 아니라 있는 메서드에 붙였으므로 **건수는 632 그대로**고 `README.md:104` 는
손댈 것이 없다.

## 변이 3판 — 전부 사망, 생존 0

저장소 밖 `mktemp -d` + `rsync` 사본에서만 돌렸다. 워킹트리는 무변으로 뒀다.

1. `extract.py` 사전 필터에서 `and "&#" not in lowered` 제거 → `FAILED (failures=3)`
2. `indexer.py` 제거 질의에서 `OR p.html LIKE '%&#%'` 제거 → `FAILED (failures=1)`
3. 필터를 `&#[0-9]+;` 로 **좁히는** 변이 → `FAILED (failures=2)`

**1번과 2번이 각각 다른 단언을 죽였다** — 계획서 예측대로 두 자리는 따로 운다.
3번은 이번에 심은 「세미콜론 없음」 단언이 실제로 재는 자를 증명했다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
→ Ran 632 tests · OK · rc 0
PYTHONPATH=src python3 e2e/noindex_e2e.py
→ e2e 통과 · rc 0
```

`git status --porcelain` 은 `M tests/test_extract.py` 하나뿐(사본 삭제 확인) ·
`data/crawl.db` 무변 · 스키마·마이그레이션·재색인·새 의존성 **0** · `docs/specs/` 무접촉.

## 다음

**리뷰 phase 1/1.** 볼 자리는 두 곳이다 — ① `&#` 판별자의 천장 주석이 실제 천장과
같은 말을 하는가(명명 엔티티로 `r` 을 못 낸다는 근거), ② 제거 질의를 넓힌 것이
전수 조인 비용에 얼마나 얹히는가(`indexer.py` 의 ponytail 주석이 이미 그 축을 적어 뒀다).
