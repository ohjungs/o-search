---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 290
updated: 2026-09-03
ctx: 58
night_iterations: 119
night_red: 1
night_retries: 0
plan: hidden-passage
---

# 현재 상태

**개발 1/1 끝. 다음은 테스트 1/1.** 계획 51 `hidden-passage` 의 설계 A 를
`src/websearch/extract.py` 에 심었고 단위 **585건 OK** 다.
브랜치 `loop/hidden-passage`, 기점 `d5367fa`(**`main` 아님** — 아래 「원격」 절).

## 개발이 심은 것 — 파일 1개 · 제품 약 45줄

- `_VOID_TAGS`(HTML void 14개) · `_ZERO_FONT` · `_is_hidden(tag, attrs)` 모듈 셋과
  `_BlockParser` 의 메서드 셋 — `handle_starttag` 에서 **`super()` 뒤에** 열고,
  `handle_endtag` 에서 `_open` 과 **같은 관용구**(`del [뒤에서 찾은 자리:]`)로 닫고,
  `handle_data` 에서 숨김 영역의 텍스트를 **애초에 안 담는다**(블록을 사후에 안 버린다).
- **설계가 지목한 무변경 지점을 지켰다** — `_SKIP_TAGS`·`_INLINE_TAGS`·`_NON_BLOCK_TAGS`·
  `_normalize`·`_TextParser` 는 `git diff` 에 한 줄도 안 나온다. 그래서 색인 본문·스키마·
  `data/crawl.db` 가 **구조적으로** 안 움직이고 재색인이 0 이다.
- **TDD** — 새 단언만 먼저 넣어 `FAILED (failures=14)` 을 눈으로 보고 구현했다.
- 계약이던 문서 두 줄도 같은 커밋이다 — `README.md ## 품질 기준` 아래 「`/passages` 는
  화면에 안 보이는 텍스트를 근거로 내지 않는다」 한 문단(`VERSION` 을 안 올리는 대신
  조용한 변경을 막는 것 · 설계 5절)과 단위 건수 **579 → 585**.

## 변이 8건 — 양방향 전부 RED 를 눈으로 봤다

`.mutation-lock` 걸고 매번 원복, 마지막에 `git diff -- src/` 로 확인 · **커밋된 변이 0**.

| 방향 | 변이 | 죽은 자리 |
|---|---|---|
| 좁아짐 5 | 다섯 모양을 각각 지운다 | **그 모양의 새 단언만** 빨개진다(각 2~4건) |
| 넓어짐 ⓐ | `_is_hidden` 이 늘 True | **기존 `TestExtractBlocks` 가 무너진다** — 오탐이 제일 위험이라는 것을 스위트가 증명한다 |
| 넓어짐 ⓑ | `_ZERO_FONT` → `"font-size:0" in style` | 음성 단언 `font-size:0.9em` **하나만** |
| 넓어짐 ⓒ | `_VOID_TAGS` 가드 제거 | void 4모양 전부 「앞 문단만 남는다」 |

설계가 예고한 자리와 죽은 자리가 정확히 같다.

## 품질·성능 축 — 기준선 그대로 (앞 반복 실측 · 이번 반복은 안 쟀다)

ko **20/20** · en **19/20** · 순위 1위 39 · 매치 평균 14.0(최소 11) ·
문단 정확도 **100.0%** · 채택률 99.5% · p95 **1.48ms** · `perf_search` p95 **8.97ms** ·
`search_api` p95 2.11ms · 처리량 [열림] **10.24/s** · [차단] **10.23/s** ·
문서집합 sha1 `541d455a…c078654b` · 디자인 4축(외부 0 · JS 0 B · 텍스트 4.87:1 · 링 3.56:1).
**테스트 1/1 이 이 축들을 실제로 다시 잰다** — 스위트 밖이라 개발이 안 닫았다.

## 저장소 불변

`e2e/` 무변 · `docs/specs/` 무변 · `data/crawl.db` sha256 `85c96744…75bda18` **무변경** ·
새 의존성 **0**(`re` 는 stdlib) · 새 파일 **0** · 스키마·마이그레이션 없음 · `VERSION` 1 유지.
고친 제품 파일은 `src/websearch/extract.py` **하나**라 되돌리기가 커밋 하나 revert 다.

## 러너 규율 — 이번 반복 0회 (누적 30회)

러너 호출 **11회 전부 맨몸·단독**. 정식 3회(`PYTHONPATH=src python3 -m unittest discover
-b -s tests` — RED 확인 · 구현 뒤 · 마감) 는 각각 `FAILED (failures=14)` / `Ran 585 tests
/ OK` / `Ran 585 tests / OK` rc 0. 변이 8회는 `python3 -B` 를 붙였다(선례 `history_042`
— 편집 직후 재실행이라 바이트코드를 안 믿는다). **열네 반복 연속 0회다.**
러너가 아닌 곳(`git`·`grep`·`ls`·`wc`·`touch`·`rm`)에서 `&&` **0회** · `;` **2회** ·
파이프 **0회** — 계수 밖이지만 남긴다.

## 문서 마감

`status.md`(이 문서 — `iteration` **290**) · `metrics.md`(`반복` **290** · `## phase 분포`
개발 **69**) · `index.md`(51번 행에 개발 결과) · `history_current.md` append(개발 1 항목) ·
`README.md`(단위 **585건** · `/passages` 한 문단). `history_current.md` **166줄**
(상한 300줄/20회 안 — 회전 없다) · `digest.md` **195줄**(상한 200 안, 무변).
`반복` 은 `status.md` 의 `iteration` 과 함께 움직인다(`IterationSyncTest`).

## 다음 — 테스트 1/1

완료 기준의 「그대로여야 할 것」 중 **스위트 밖 축**을 실제로 잰다 — 평가 코퍼스 64문서의
블록 목록 차이 0 · `passage_eval` 정확도·채택률·p95 · `quality_eval` ko/en · 문서집합 sha1.
그리고 갭 탐색으로 새 단언 6건이 **못 잡는 자리**를 찾는다(설계 3절이 적어 둔 천장 —
외부 CSS·클래스·`visibility`/`opacity`·안 닫힌 숨김 컨테이너 — 은 고칠 것이 아니라 잴 것이다).

## 원격 — `origin/main` 은 계획 47 까지다

- **PR #7** — `loop/merge-48-50` → `main`, 계획 48·49·50 을 한 PR 로 담았다. **OPEN·미병합.**
  병합은 **사용자가 처리한다** — 이 반복은 PR 을 열지도 닫지도 않았고 그 브랜치에 커밋하지도 않았다.
- **그래서 계획 51 의 기점은 `main` 이 아니다.** `origin/main`(`687a159`)에는 계획 48·49·50 이
  없어 `README.md` 의 단위 건수와 `tests/test_readme.py` 의 건수 단언이 거기서는 RED 다.
  `d5367fa`(`loop/merge-48-50` HEAD)에서 `loop/hidden-passage` 를 땄다.
- 앞선 병합: PR #6 = 계획 44~47(`687a159`). 충돌 0.

## 사람이 정할 것 — 다섯 (PR #7 이 붙었다)

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
2. **`--focus` 는 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 이 0 일
   때만 이웃이 되고, 검사기가 매 실행 offset > 0 을 확인한다(실측 2px).
3. **반응형 360px 미검증** — 브라우저가 없어 이 저장소의 누구도 그 화면을 못 그린다.
4. **회전 규약·러너 규율의 저장소 밖 절반**과 **사양이 남긴 둘**(`docs/specs/concept.md` 의
   `## 사람이 정할 것` — 속도 제한 시점, 사양 숫자 90%·500ms·60회/분이 초안이라는 것).
5. **PR #7 병합** — 위 「원격」 절.
