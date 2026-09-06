---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 397
updated: 2026-09-06
ctx: 55
night_iterations: 193
night_red: 2
night_retries: 4
plan: spec-citation-anchor 계획 68 (e2e phase 완료 · DONE · 다음 계획은 아직 없다)
---

## 현재 상태

**계획 68 `spec-citation-anchor` 를 닫았다 — 통과 · DONE.**
전수 **`Ran 628 tests in 15.748s` · `OK` · rc 0** 1회 · 실물 e2e 스크립트 **2개**
실행(`design_check.py`·`perf_crawl.py`, 둘 다 rc 0) · 실물 사본 대조군 **3판**
(V0 성한 원본 + 변이 2판). 산출물은 `docs/e2e/spec-citation-anchor/result.md`.
**다음 계획은 아직 없다** — 다음 반복이 계획 phase 로 연다.

## 이번 phase 가 산 것

**계획 68 의 크기를 같은 변이의 숫자 차이로 샀다.** 사양 `concept.md` 에 줄 하나를
끼우는 변이(V1)는 계획 67 e2e(반복 392)에서 **12건**을 죽였다. 오늘 같은 자리에
같은 편집을 심으니 **20건**이다 — 인용 18자리 중 **17이 죽고 1이 산다.** 계획 68 이
앵커를 심은 열두 자리 중 **여덟이 새로 목록에 들어왔다**(`perf_crawl.py:1`·`:151`·
`:253`·`:275` · `quality_eval.py:34` 문구 · `test_serve.py:918`·`:936`·`:955`).
계획 1절이 「이 자리들은 조용히 산다」고 적은 문장이 실물 변이에서 뒤집혔다.

**착수 탐침 `M1` 도 이제 죽는다(완료 기준 3).** 계획 전 `OK` 로 살아 나가던
`e2e/perf_crawl.py` 1행 `:44`→`:45` 가 오늘 `failures=1` · 라벨
`[e2e/perf_crawl.py:1 문구]` 다.

**실행 경로 회귀도 실물로 봤다.** `design_check.py` 의 `print` 헤더가 바뀐 그대로
찍히고 4축 전부 통과 · `perf_crawl.py` 3시나리오 전부 통과. 위험했던 자리 하나 —
**실패할 때만 뜨는 `perf_crawl.py:275` 의 `assert` 메시지**는 통과 실행에서 한 번도
렌더되지 않아 인자가 어긋나도 초록이라, `ast` 로 그 노드를 뽑아 그대로 렌더했다.
포맷 인자 다섯이 맞고 앵커 문구가 산다.

## 남긴 것 (막지 않음 · 다음 계획의 입력)

**V1 에서 살아남은 하나는 `e2e/quality_eval.py:3`(`concept.md:22-23`)** 이다 —
범위 인용이라 21행 뒤에 한 줄이 끼면 옛 22행이 23행으로 가는데 **23이 아직 범위 안**이다.
반복 395 가 72조합을 정적으로 재서 「생존은 정확히 범위 인용 넷의 구조적 성질」이라고
적은 것과 글자 그대로 같고, **오늘 사양 쪽으로 미는 방향에서 실행으로 되샀다.**
처방(문구 축을 범위 전체가 아니라 **시작행**에서 찾기)은 `digest.md` 「다음 계획 후보」
`[5]` 에 이미 있다. `MIN_CHECKS 6` 잉여 건은 반복 396 이 적은 그대로다.

**계획서 숫자 하나를 정정했다** — 2·3절의 「앵커 없음 11」은 실측 **12** 다
(`e2e/quality_eval.py:34` 가 값 앵커를 가져 「있음 7」에 들어갔지만 문구 축에서도 새로
세어진다). 개발(394)·리뷰(396)는 이미 12 로 적었고 정정 자리 집합은 같아 판정 무영향.

## 검증

전수 **`Ran 628 tests` · `OK` · rc 0**(맨몸 1회) · `README.md:104` 의 `628`·`21` 과 일치 ·
`git diff --stat 274c0eb^ HEAD -- src/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` **무변** · 사본 변이 뒤 저장소
`git status --porcelain` **빈손** · `metrics.md` 「반복 397」 = 이 파일 `iteration: 397`.

## 다음

**계획 phase.** 계획 68 은 DONE 이고 `docs/plan_history_054.md` 로 아카이브했다.
다음 반복이 새 계획을 연다 — 오늘 V1 이 범위 인용 생존을 사양 쪽에서 처음 재현했으니
`digest [5]` 의 근거가 하나 굵어졌다.
