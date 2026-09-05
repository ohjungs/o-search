---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 331
updated: 2026-09-05
ctx: 58
night_iterations: 153
night_red: 2
night_retries: 0
plan: loader-isolation — 계획 56 **DONE** (e2e phase 완료 · 다음은 새 계획 탐색)
---

# 현재 상태

**계획 56 을 닫았다 — e2e 21종 전부 rc 0, 완료 기준 다섯 전부 오늘 실측으로 충족.**
저장소 코드는 계획 전체를 통틀어 `tests/test_readme.py` **한 낱말 + 주석 넉 줄**이고
제품 `src/` 는 **0줄**이다. 이번 반복이 고친 것은 `docs/` 뿐이다.

## 완료 기준 대조 (계획 56 4절 · 전부 오늘 다시 쟀다)

| # | 기준 | 오늘 실측 | 판정 |
|---|---|---|---|
| 1 | `-k Readme` → `OK` · rc 0 | `Ran 5 tests` · `OK` · rc 0 | 충족 |
| 2 | 전수 → `Ran 605 tests` · `OK` · rc 0 | `Ran 605 tests in 13.4s` · `OK` · rc 0 | 충족 |
| 3 | 전역 패턴을 손으로 심어도 센 값이 605 | 고친 줄 **605** · 되돌린 줄 **5** | 충족 |
| 4 | `README.md` 의 `단위 605건` 무수정 | `fe4dd0d..HEAD` 에 `README.md` **0줄** | 충족 |
| 5 | `tests/test_readme.py` 외 코드 파일 0개 | 계획 전체 diff 의 코드 파일 **그 한 개** | 충족 |

## e2e 21종 전수 — **rc 0 × 21**

하나씩 따로 돌렸다(`for` 루프 안에서 러너를 돌리지 않았다). 판정 줄과 `rc=` 를 전부 봤다.

```
crawl_e2e 0 · crawl_delay_e2e 0 · crawl_politeness_e2e 0 · deadline_e2e 0 ·
design_check 0 · domain_key_e2e 0 · hidden_passage_e2e 0 · indexer_e2e 0 ·
indexer_interrupt_e2e 0 · interrupt_e2e 0 · noindex_e2e 0 · non_ascii_e2e 0 ·
pagination_ui_e2e 0 · passage_eval 0 · perf_crawl 0 · perf_search 0 ·
quality_eval 0 · retry_interval_e2e 0 · search_api_e2e 0 · tokenizer_e2e 0 ·
url_normalize_e2e 0
```

기준선(회귀 비교용): 정확도 **100.0%**(398/398) · 채택률 99.5% · `/passages` p95 **1.53ms** ·
`perf_search` p95 **8.95ms**(예산 300ms 의 3.0%) · `search_api` p95 2.12ms ·
품질 ko **20/20**·en **19/20** · 크롤 처리량 **10.30/s**(차단 10.27/s) · 디자인 4축 전부 OK.
계획 54 e2e(p95 1.5ms · 100.0%)와 나란하다 — **회귀 0**.

## 리뷰 지적의 「더 싼 처방」 — **안 넣는다. 값이 0 으로 측정됐다**

리뷰가 `tests/test_design_check.py`·`test_quality_eval.py`·`test_passage_eval.py` 세 자리에
`if E2E not in sys.path` 한 줄씩을 제안했다. **넣기 전에 만들어서 먹여 봤다.**
저장소 밖 사본 둘(가드 없음 A · 가드 있음 B)에 같은 변이(`e2e/tempfile.py` 로 stdlib 가리기)를
심고 전수를 돌렸다:

```
A(가드 없음)  Ran 605 · FAILED(failures=23) · rc 1
B(가드 있음)  Ran 605 · FAILED(failures=23) · rc 1   ← 실패 목록이 파일·줄까지 동일
```

**가드는 중복 칸만 막고 첫 insert 를 안 막는다.** 위험이라고 지목된 것은
「`e2e/` 가 전수 내내 `sys.path[0]` 에 앉아 있다」인데 가드는 그것을 한 칸도 안 건드린다.
게다가 계획 56 5절이 「다른 테스트의 전역 상태 감사 — 넓히면 별건」으로 이 자리를 미리 잘라 뒀다.
**`digest ## 다음 계획 후보` `[5]` 에 이 실측과 함께 등재를 유지했다(5점).**

## 바로잡은 문장

- **`digest.md` `[5]` 의 「`sys.path` 에 **네 칸**을 남긴다」→ **여섯 칸**.** 공식 진입점
  (`unittest.main(module=None, argv=[…,'discover','-b','-s','tests'])`)으로 앞뒤를 대조하니
  `e2e` 0→3 · `src` **1→3** · `tests` 0→1 이다. 빠져 있던 둘은 `e2e/quality_eval.py:28` 과
  `e2e/passage_eval.py:48` 이 in-process 임포트될 때 넣는 `src` 다.
  **저장소 몫은 `e2e`×3 + `src`×2 = 다섯 칸, stdlib 몫이 `tests`×1.**
  재는 자를 두 반복 연속 다시 재서 두 번 다 숫자가 움직였다.
- 「누출이 프로세스 경계를 넘는다」는 리뷰(반복 330)가 이미 `digest.md` 에서 고쳤고,
  아카이브(`history_<NNN>.md`)는 수정 금지라 **이번 append 가 정정을 싣는다**.

## 문서 회전 (이번 반복 첫 일)

`history_current.md` **298줄 → 140줄** — 계획 55 `db-state-invariant` 의 여섯 반복을
**`docs/history_058.md`**(188줄)로 밀어냈다. `digest.md` «아카이브 명부» 줄에 등록했고
(`ArchiveIndexTest` 초록) 회전 서술은 새 줄을 안 만들고 기존 회전 줄에 이어 붙였다.
`digest.md` 는 **202줄 → 200줄** — 가장 오래된 완료 항목 둘(계획 44 `focus-ring-presence` ·
계획 48 `passage-api`)을 지웠다. 결과는 `index.md` 와 `plan_history_*.md` 가 그대로 갖고 있고
계획 48 의 숫자들(`MAX_PASSAGE_HTML` 35,000 · p95 199.9ms)은 `project.md ## 품질 기준` 에 산다.

## 다음 행동

**새 계획 탐색.** `digest ## 다음 계획 후보` 의 7점짜리(`[7]` 태그 밀도 축)와 5점 셋이 후보다.
**아카이브(`plan_loader-isolation.md` → `plan_history_042.md` · `index.md` 줄 추가)는 다음
반복이 한다** — 이 스텝은 e2e 하나만 돌고 멈춘다. 병합은 사람 몫이다.

## 러너 규율 — **이번 반복 0회 (누적 35회)**

러너를 스물다섯 번 돌렸다(e2e 21 · 전수 2 · `-k` 1 · 사본 변이 2, 그 밖에 탐침 3).
**전부 맨몸이고 파이프 왼쪽에 둔 적 0회 · `2>&1`·`2>/dev/null`·`>/dev/null` 0회 ·
백그라운드 0회.** 판정 줄과 `rc=` 를 전부 화면에 남겼다.

## 한도

제품 `src/` **0줄** · 저장소 코드 **0줄**(이번 반복은 `docs/` 만) · 새 파일은 회전 산물
`docs/history_058.md` 하나 · `data/crawl.db` **무변**(sha256 `85c96744…5bda18` 대조를
e2e 전수 앞뒤로 두 번 통과) · `docs/specs/` 무변 · `README.md` 무변 · 새 의존성 0 ·
스키마·마이그레이션·재색인 0 · `pgrep -f websearch.serve` **0건** · `__pycache__` 0개 ·
`--no-verify`·`--force` 0 · `main` 직접 커밋 0 · **PR 무접촉(조회·생성·병합 0회)** ·
브랜치 병합·삭제 0 · 변이 재현은 **스크래치패드 사본**에서 돌고 지웠다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **3시간 자동 스냅샷 잡을 루프 작업 중에도 세울 것인가**(반복 328 의 사고).
   **이번 반복에는 끼어들었다** — 문서 회전 직후 `73a93bd 자동 스냅샷 2026-09-05 10:50` 이
   회전 세 파일을 커밋하고 원격까지 밀었다. 초록 상태였고 되돌리지 않았다(`--force` 금지).
   RED 중간을 덮치면 깨진 상태가 원격에 올라간다는 위험은 그대로다.
   루프가 도는 동안 `.mutation-lock` 을 켜 두는 안이 있다.

## 정지 사유

없음 — **계획 56 DONE.** 다음 반복은 아카이브 + 새 계획 탐색.
