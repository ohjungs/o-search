---
signal: GREEN
mode: night
plan: quality-eval
phase: 리뷰
step: 4/4
attempt: 0
iteration: 53
night_iterations: 22
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 53)
ctx: 78% / 200k
rules: rules/review.md
---

# 현재 상태

**`quality-eval` 테스트 phase 완료. 다음은 리뷰 phase.**
전체 **166/166 통과**(164 → +2), 기존 e2e 5개 회귀 없음, `quality_eval.py` 종료 코드 0 유지.

## 테스트 phase 가 결함 하나를 잡았다 — 오타가 품질 회귀로 둔갑했다

`--corpus`/`--queries` 경로 오타나 깨진 JSON 이 **트레이스백 + 종료 코드 1** 로 나갔다.
이 러너의 `1` 은 **"검색 품질 80% 미만"** 으로 예약된 값이라, CI 가 돌리면 사람 실수가
품질 회귀로 보고된다. 계약(`design_quality-eval.md` `## 계약`)은 사용법 오류도 `2` 라고
적혀 있었으니 **코드가 계약을 어긴 것**이다. 재현 테스트 2건 → 실패 확인 → `main` 에서
`(OSError, ValueError)` → 2, `_load` 는 메시지에 파일 경로를 붙인다(깨진 JSON 의 원
메시지에는 파일 이름이 없어 두 fixture 중 어느 쪽인지 알 수 없었다).

변이 2종으로 새 테스트가 진짜 잡는 것까지 확인했다(`return 2`→`1`: 2건 실패 / 경로
붙이기 제거: 1건 실패). 8점 미만 1건은 digest 로 — G3 가 ko·en 만 세서 `lang: ja` 가 조용히 사라짐[4].

## 실측 요약 (개발 4/4 에서 확정, 변동 없음)

- ko 17/20 (85%) · en 18/20 (90%) → 기능 2 **합격**
- 순위 분포 `1위 35 / 2~10위 0 / 매치 없음 5` → `recall@1` == `recall@10`
- 절제(방해 문서 제거)로도 포함률이 오르지 않는다 → 미포함 5건은 랭킹이 아니라 **매치 실패**

## 다음 (리뷰 phase — `rules/review.md`)

- 대상 diff: `e2e/quality/*.json`(fixture) · `e2e/quality_eval.py` · `tests/test_quality_*.py`
- 백지 패스(서브에이전트에 계획·설계를 주지 않고) 권장 — 반복 45 에서 지적 10건이 전부 실재했다
- 그 뒤 e2e phase 에서 `docs/e2e/quality-eval/result.md` 작성 (시나리오 3 = 절제, 이미 실측치 있음)

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

`recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다.
`robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
