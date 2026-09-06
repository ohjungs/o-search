---
signal: GREEN
phase: 개발
step: 2/2
attempt: 0
iteration: 389
updated: 2026-09-06
ctx: 42
night_iterations: 190
night_red: 2
night_retries: 4
plan: spec-citation-address 계획 67 (개발 2/2 완료 · 다음은 테스트 phase)
---

## 현재 상태

**계획 67 `spec-citation-address` 의 스텝 2/2(인용문 축)를 닫았다 — 개발 phase 끝.**
같은 수집기 위에 문구·값 대조를 얹고, 인용 쪽 네 자리를 고쳤다.
전수 **627건 · `OK` · rc 0**.

## 이번 스텝이 한 일

**가드.** `SpecCitationTest` 의 수집을 `_citations()` 로 빼고(주소 축과 공유)
`test_spec_quotes_match_cited_lines` 를 더했다. 인용 **뒤**에 따옴표로 옮겨 적은
문구는 대상 줄 범위 안에 실재해야 하고, 인용을 주석으로 단 상수는 값 표기 중
하나가 그 범위 안에 있어야 한다(`5.0` 은 사양에 `5` 로 적혀 정규화한다).
대조 건수 **≥ 5** 도 단언한다 — 추출기가 깨지면 0건 대조 위에서 초록이 된다.
따옴표를 인용 **앞**에서 안 보는 것이 핵심이다: 인용을 통째로 품은 실패 메시지
(`"JS 0KB 계약 위반 (concept.md:51)"`)를 사양 문구로 오인하지 않는다.

**TDD RED.** 가드만 심은 판이 **3자리 4건** RED —
`e2e/design_check.py:33`(값 `50`·`1024` 가 50행에 없다) ·
`e2e/quality_eval.py:34`(문구 「상위 10건」 + 값 `10`) ·
`tests/test_quality_eval.py:153`(문구 「80% 이상」). 계획서 2절 P2 가 정적 판독으로
예고한 넷과 파일·줄까지 같다. 맞는 인용은 한 건도 안 빨개졌다 — 오탐 0.

**네 자리를 고쳤다.** `:50` → `:51` ×2(JS 예산은 51행) · `:22` → `:23` ×2
(합격선 문구는 23행). `e2e/design_check.py:33` · `tests/test_serve.py:918` ·
`e2e/quality_eval.py:34` · `tests/test_quality_eval.py:153`.
`tests/test_serve.py:918` 은 가드가 못 무는 자리지만(메시지가 인용을 품는다)
정적으로 틀린 것이 확인돼 같이 고쳤다. **`docs/specs/concept.md` 는 무변.**

**변이 2판, 둘 다 죽었다(완료 기준 C4·C5).** C4 주소 되돌리기(`:51`→`:50`) rc 1 ·
C5 인용문만 바꾸기(「상위 10건」→「상위 20건」) rc 1 · 복구 후 `OK`.
C6·C7 은 테스트 phase 가 잰다.

**건수 못이 또 물었다.** 새 단언 1개라 626 → **627**. 첫 전수를
`test_verification_counts_match_reality` 가 `(626, 21) != (627, 21)` 로 잡았고
`README.md:104` 을 627 로 고쳐 초록으로 갔다(같은 커밋).

**범위**: `src/` 0줄 · `docs/specs/` 무변 · `data/crawl.db` 무변 · 재색인 0 ·
스키마 0 · 새 의존성 0(stdlib) · PR #7 무접촉(`gh` 0회) ·
`--no-verify`·`--force`·`--amend`·`rebase` 0회 · `main` 직접 커밋 0회.
바꾼 것은 `tests/test_docs.py`(+52/-11) · `e2e/design_check.py`·`e2e/quality_eval.py`·
`tests/test_serve.py`·`tests/test_quality_eval.py` 각 1줄 · `README.md` 1줄.

## 다음

**테스트 phase.** 완료 기준 C6(가드의 빈 줄 검사만 지우면 C1 이 되살아나야 한다)·
C7(수집 정규식을 못 물게 깨면 하한 단언이 문다)을 변이로 잰다. 문구 축에도 같은
질문이 있다 — `MIN_CHECKS` 하한과 「인용 뒤만 본다」 규칙을 깨는 변이다.
`docs/history_current.md` **정확히 300줄 = 상한**. 다음 반복은 한 줄이라도 더 쓰기 전에
`docs/history_068.md` 로 회전하고 `digest.md` 아카이브 명부에 등재한다.
