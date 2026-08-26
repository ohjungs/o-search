---
signal: GREEN
mode: night
plan: quality-eval
phase: 테스트
step: 4/4
attempt: 0
iteration: 52
night_iterations: 21
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 52)
ctx: 72% / 200k
rules: rules/test.md
---

# 현재 상태

**`quality-eval` 개발 4/4 완료 — 스텝 전부 끝. 다음은 테스트 phase.**
164/164 통과. `e2e/quality_eval.py` 종료 코드 0 (ko 17/20 85% · en 18/20 90%).

## 설계의 열린 가정을 실측으로 닫았다 — 숫자의 성격이 바뀐다

```
순위 분포(40질의):  1위 35건 · 2~10위 0건 · 매치 없음 5건
→ recall@1 == recall@10.  "상위 10" 이라는 창이 아무 일도 하지 않는다
절제(방해 문서 제거, 정답 40문서만): 포함률 35/40 그대로, G2 만 38/40 발화
```

- **포함률이 높은 건 측정이 후해서가 아니다** — 창을 10에서 1로 좁혀도 같은 숫자다
- **동시에 랭킹이 좋아서도 아니다** — 방해를 다 빼도 숫자가 안 오른다. bm25 정렬은
  이 fixture 에서 한 번도 시험되지 않았다. 매치되면 1위, 아니면 미검출인 **이진 상태**다
- 미포함 5건은 전부 `unicode61` 한계: 복합어 뒷부분 2 · 띄어쓰기 1 · 영어 굴절 2
- → `docs/design_quality-eval.md` `## 가정` 에 "닫힘" 으로 기록, `digest.md` 후보 3건 등록

## 이번 반복에 확인한 것 (남의 관찰이 아니라 직접)

| 변이 | 기대 | 실제 |
|---|---|---|
| 정답 URL 오타 | 2 (G1) | 2 |
| 질의 19개 | 2 (G3) | 2 |
| 방해 문서 제거 | 2 (G2 측정 불능) | 2 |
| 정답 2건에서 질의어 삭제 | 1 (미달) | 1 — ko 75% / en 90% |
| 무변이 | 0 | 0 |

## 다음 (테스트 phase — `rules/test.md`)

- 전체 164/164 + 기존 e2e 5개 회귀 확인
- 갭 찾기: `quality_eval` 의 `--corpus/--queries` 경로 오류·깨진 JSON 경로,
  `report()` 의 `//` 내림(digest [4]), `build_index` 가 색인 실패를 삼키지 않는지
- e2e 는 아직 `미정` — e2e phase 에서 `docs/e2e/quality-eval/result.md` 를 쓴다.
  개발 4/4 는 계획서가 예상 파일로 적은 result.md 를 **일부러 안 썼다** — 시나리오
  판정은 e2e phase 것이고, 여기서 미리 쓰면 같은 실행을 두 번 기록하게 된다

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

`recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다.
`robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
