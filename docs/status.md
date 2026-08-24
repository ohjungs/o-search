---
signal: GREEN
mode: night
plan: search-api
phase: 개발
step: 3/5
attempt: 0
iteration: 33
night_iterations: 2
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 33)
ctx: 75% / 200k
rules: null
---

# 현재 상태

**스텝 3 완료 — 신뢰 경계가 `_parse()` 한 곳에 모였다.** 115/115 통과.

## 진행 중인 스텝 — 이어받는 세션이 읽을 것

- 할 일: **개발 스텝 4 — p95 측정 명령과 기준선** (`rules/dev.md`)
- 근거: `docs/plan_search-api.md` 스텝 4. `docs/project.md` 품질 기준의
  "성능 측정: 없음"·"기준선 파일: 없음" 을 채우는 것이 이 계획의 절반이다
  (계획서 근거 절). 컨셉 성능 1 = p95 300ms 지만 **100만 문서 기준**이라
  지금 나오는 숫자는 합격 판정이 아니라 **회귀를 잡을 기준선**이다
- 완료 기준: `e2e/perf_search.py` 가 임시 색인 + `--port 0` 로 서버를 띄우고
  질의 셋을 N회 돌려 p50·p95 와 그때의 문서 수를 출력한다. 네트워크를 타지 않는다.
  숫자를 `docs/project.md` 품질 기준에 적는다
- 이미 한 것: 스텝 3 커밋 `9268374` 까지. 서버 쪽은 손댈 것이 없다 —
  측정 스크립트만 신설한다
- 건드릴 파일: `e2e/perf_search.py`(신설), `docs/project.md`

## 남은 스텝

4 p95 측정·기준선 → 5 e2e

## 다음 행동

`/loop-harness night` 을 다시 부르면 개발 스텝 4 부터 이어진다.
계획이 DONE 되면 다음은 **`crawl-delay` 존중**(`docs/digest.md` 크롤 윤리) — 사용자가
이미 정한 순서다.

## 정지 조건

ctx 71% · 5h 66% · 7d 40% — 걸린 것 없음. 계속 진행 중.
