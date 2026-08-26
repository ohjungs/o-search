---
signal: DONE
mode: night
plan: quality-eval
phase: 완료
step: 4/4
attempt: 0
iteration: 55
night_iterations: 24
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 55)
ctx: 55% / 200k
rules: rules/discover.md
---

# 현재 상태

**`quality-eval` 완료 (계획 6번째).** 170/170 통과, 기존 e2e 5개 회귀 없음,
`plan_history_006.md` · `design_history_006.md` 로 아카이브.

## 이 계획이 남긴 숫자

- **컨셉 기능 2 를 처음 쟀다** — ko 17/20 (85%) · en 18/20 (90%) ≥ 80% **합격**
- 명령: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 e2e/quality_eval.py` (0.1s 미만)
- 종료 코드 계약: `0` 합격 / `1` 품질 미달 / `2` fixture 결함·사용법 (네 갈래 전부 실행으로 확인)

## 이 계획이 남긴 **한계** — 다음 계획이 반드시 읽을 것

e2e 시나리오 3(방해 문서 절제)이 **반증됐다.** 방해 문서를 전부 빼도 포함률이
35/40 그대로다. 순위 분포가 `1위 35 · 2~10위 0 · 미검출 5` 라 **`recall@1` 과
`recall@10` 이 같다** — 상위 10 이라는 창이 한 번도 판정을 가르지 않았다.
**이 85/90% 는 랭킹 품질이 아니라 매치 품질의 숫자다.** 러너가 이제 매 실행
그 한 줄을 스스로 찍는다. 근거: `docs/e2e/quality-eval/result.md`

## 다음 (계획 탐색 — `rules/discover.md`)

유력 후보 둘. 근거는 `digest.md`·`index.md` 에 있다.

1. **`search-ui`** (`index.md` 사양 분할 6번) — 컨셉 4축 중 **경량·디자인이 아직 측정
   명령 `없음`** 이다. 품질·성능·윤리는 자가 다 생겼고 이 축만 비었다
2. **토크나이저** (`digest.md` [8]) — 미포함 5건이 전부 이것이고 랭킹 손실은 0건이다.
   기준선(ko 85 / en 90)이 방금 고정됐으니 이제 비교가 된다

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

`recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다.
`robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
