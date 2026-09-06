---
signal: DONE
phase: e2e
step: 2/2
attempt: 0
iteration: 392
updated: 2026-09-06
ctx: 63
night_iterations: 190
night_red: 2
night_retries: 4
plan: spec-citation-address 계획 67 (e2e phase 완료 · DONE · 다음 계획은 아직 없다)
---

## 현재 상태

**계획 67 `spec-citation-address` 를 닫았다 — 통과 · DONE.**
전수 **`Ran 627 tests in 15.860s` · `OK` · rc 0** 1회, 실물 사본 대조군 **4판**
(U0 성한 원본 + 변이 3판). 산출물은 `docs/e2e/spec-citation-address/result.md`.
**다음 계획은 아직 없다** — 다음 반복이 계획 phase 로 연다.

## 이번 스텝이 한 일

**U1 — 사양에 줄 하나를 끼우니 12건이 죽는다.** 사본의 `docs/specs/concept.md` 21행 자리에
항목 한 줄을 넣어 아래 주소를 통째로 한 칸 밀었다. `test_spec_citations_point_at_real_lines`
다수와 `test_spec_quotes_match_cited_lines` 가 함께 울고, 라벨에 `tests/test_serve.py:914` ·
`e2e/design_check.py:2` 처럼 **고칠 파일과 줄이 통째로** 찍힌다. **앞 phase 들이 잰 변이
(C1~C7)는 전부 인용 쪽을 비트는 것이었고, 사양 쪽을 미는 변이는 오늘이 처음이다** — 이 계획이
존재하는 이유로 적은 전제를 그 방향에서 처음 샀다.

**U2·U3 — 리뷰 스텝(`e8291e9`)이 산 것을 실행으로 갈랐다.** `PHRASE` 의 따옴표 종류를
`"` → `'` 로 바꿔 문구 축을 통째로 죽이는 같은 편집을, 하한만 다르게 두 판 돌렸다.
`MIN_CHECKS 6` 이면 **`FAILED (failures=1)` · rc 1**(「대조를 5건밖에 못 했다」 ·
`5 not greater than or equal to 6`)이고, 리뷰 이전 값 `5` 로 되돌리면 **`Ran 30 · OK · rc 0`
으로 그대로 나간다.** 리뷰가 「하한이 값 축의 크기(5)와 같아 문구 추출기만 죽는 날 조용하다」고
정적으로 적은 판정이 오늘 실행으로 확인됐다 — **생존→사망이 뒤집힌 자리를 눈으로 봤다.**

**U0 — 오탐 0.** 성한 원본에서 `Ran 30 tests in 0.020s` · `OK` · rc 0.

**면제 근거를 갈아끼웠다.** 계획 61~66 은 「`git diff … -- src/ e2e/` 가 빈손」을 근거로 21종
재실행을 0회로 뒀는데, **이 계획은 `e2e/` 를 건드렸다.** 그래서 빈손 논법을 복사하지 않고
네 줄을 세어서 댔다 — `e2e/design_check.py` 셋(docstring · `JS_BUDGET` 주석 · `print` 헤더
라벨)과 `e2e/quality_eval.py` 하나(`TOP_N` 주석)뿐이고 **판정 로직·임계값·HTTP 표면은 0줄**,
그 문자열을 읽는 소비자는 새 가드 `SpecCitationTest` 하나이며 627 안에서 초록이다.
`src/`·`docs/specs/`·`data/` 는 빈손이고 `data/crawl.db` sha256 `85c96744…5bda18` 무변.

**안 산 것도 적는다.** 값 축(`_has_number` 부분일치, `[R67-2]`)은 오늘 다시 안 쟀다 —
테스트 phase(반복 390)가 변이 3판으로 이미 샀고, 예산 안에서 값이 남은 것은 아직 아무도 안 민
축(U1)과 어제 정적으로만 닫은 판정(U2·U3)이었다. 21종 개별 재실행도 0회다.

**범위**: `src/` 0줄 · `tests/` 0줄 · `e2e/` 0줄 · `README.md` 0줄 · `docs/specs/` 무변 ·
`data/crawl.db` 무변 · 재색인 0 · 스키마 0 · 새 의존성 0(stdlib) · PR #7 무접촉(`gh` 0회) ·
전수 1회 · 변이 3판 · `--no-verify`·`--force`·`--amend`·`rebase` 0회 · `main` 직접 커밋 0회.
바꾼 것은 문서뿐이다(`e2e/spec-citation-address/result.md` 신규 · `status`·`history`·
`metrics`·`index`·`digest` · 계획서를 `plan_history_053.md` 로 아카이브).

## 다음

**다음 계획은 아직 없다.** 다음 반복이 계획 phase 로 열어 후보를 고른다.
`digest ## 후보` 와 `index.md` 11번(속도 제한 — 사람이 시점을 정한다)이 그 입력이다.
