---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 355
updated: 2026-09-06
ctx: 62
night_iterations: 172
night_red: 2
night_retries: 1
plan: index-step-sync 계획 60 (e2e 완료 · 완료 기준 6/6 충족)
---

## 현재 상태

**계획 60 을 닫는다 — e2e 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 6/6 을 오늘 다시
재서 충족했다.** 이 phase 가 한 일은 셋이다: **면제 판정**(새 e2e 를 안 만든다), 21종 전수,
변이 열 종(M2·M3·M4a·M4b·G1~G6)을 **저장소 밖에서** 다시 재기. 증거는
`docs/e2e/index-step-sync/result.md` 에 있다.

## 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획이 만진 것은 `tests/test_docs.py`(+165줄) · `docs/` · `README.md` 의 단위 건수 한 줄이고
제품 `src/` 는 **0줄**이다. 세운 것은 **기록 문서 둘을 서로 대조하는 가드**라 크롤러·색인·
서버·화면 어디도 안 지난다 — **프로세스 밖에서 달라지는 동작이 0** 이다. e2e 가 낼 값이
「안 달라졌다」의 확인뿐이라 시나리오를 새로 만들지 않았다. 만든 e2e 파일 0 · 고친 e2e 파일 0.

**대신 이 커밋 자신이 새 검사의 첫 실사용 대상이다** — 검사가 읽는 두 문서가 `status.md` 와
`index.md` 이기 때문이다. 그래서 M2·M3 를 실물 복사본 위에서 **양방향으로** 다시 쟀다.

## e2e 21종 — 전부 `rc 0` · 기준선 회귀 **0**

정확도 **100.0%**(=) · `/passages` p95 **1.52ms**(1.51) · `perf_search` p95 **9.01ms**(8.80) ·
품질 ko **20/20**(=) · en **19/20**(=) · 매치 14.0/11/28(=) · 크롤 **10.20/s**([차단]
10.20 · 반복 349 는 10.24) · 숨은 텍스트 **0/5**(=) · 디자인 4축 통과(JS 0 B · 최저 대비
4.87:1). **움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도 안 갱신했다** —
제품 0줄인 계획이라 기대한 결과 그대로다. p95 두 줄의 흔들림은 예산의 0.3%·3.0% 안쪽이고
스크립트 자신의 합격선이 통과 판정을 냈다.

## 완료 기준 6/6 — 오늘 실측

1. 전수 `Ran 614 tests in 16.098s` · `OK` · rc 0 (맨몸)
2. M2 — `index.md` 스텝 칸 `1/1`→`0/1` 에서 `StepSyncTest failures=1` 이고 메시지가
   **`0/1 ≠ 1/1`** 을 적는다 · 무변이 대조군 `run=1 failures=0`
3. M3 — `status.md` 의 `step` 만 `0/1` 로 비틀면 같은 검사가 **`1/1 ≠ 0/1`** 로 죽는다.
   방향이 반대라 **한쪽만 재는 검사가 아니다**
4. M4a(슬러그를 안 보고 아무 행이나) **5건 사망** · M4b(접두 일치로 넓힘) **3건 사망** ·
   무변이 대조군 `run=9 failures=0`
5. `README.md` 의 러너 줄이 `단위 614건` — `tests/test_readme.py` 가 전수 안에서 초록
6. `git diff 61e82e7 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** · `data/crawl.db`
   sha256 무변 · `git status --short` 빈손 · 재색인·스키마·새 의존성 0

**덤** — 반복 353 이 세운 갈래 변이 6종(G1~G6)을 다시 재 **6/6 사망**. `step_gap` 을 순수
함수로 뺀 판단이 하루 뒤에도 유효하다.

## 다음

**계획 60 DONE.** 다음 반복은 계획 phase — 계획 60 마감(`plan_index-step-sync.md`·
`design_index-step-sync.md` 를 `*_history_046.md` 로 회전 · `index.md` 의 계획 60 행을
`진행 1/1` → `완료 1/1` 로 닫고 결과 칸을 채움 · `digest.md` 의 `## 반복 실패` 항목
「스텝을 커밋하면서 `index.md`·`metrics.md` 의 숫자를 안 올린다」에 처방이 들어갔음을 표시 ·
`## 완료` 절에 계획 60 줄)과 새 후보 탐색을 함께 돈다. 리뷰가 `digest` 로 넘긴 항목 둘
(`IterationSyncTest` 의 같은 자기비교 구멍 · 닫힌 계획 행은 두 번 다시 안 본다)이
후보 목록에 있다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59·60 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- 변이는 **저장소 밖에서** 건다 — 문서 변이는 `docs/` 를 임시 디렉터리로 복사해 비틀고
  `test_docs.DOCS` 를 그쪽으로 돌렸고, 소스 변이는 원문을 문자열로 치환해 메모리에서
  `exec` 했다(원문 존재를 `count(...) == 1` 로 먼저 단언). 저장소 파일 무접촉.
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 만진 파일은 `docs/` 뿐이다 — `src/`·`tests/`·`e2e/`·`README.md`·`docs/specs/`·
  `data/crawl.db` 무접촉.
