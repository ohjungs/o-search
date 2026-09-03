---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 289
updated: 2026-09-03
ctx: 46
night_iterations: 118
night_red: 1
night_retries: 0
plan: hidden-passage
---

# 현재 상태

**설계 1/1 끝. 다음은 개발 1/1.** 계획 51 `hidden-passage` 의 갈림길 넷을
`docs/design_hidden-passage.md` 가 닫았고 `VERSION` 판정까지 냈다.
브랜치 `loop/hidden-passage`, 기점 `d5367fa`(**`main` 아님** — 아래 「원격」 절).

## 설계가 고른 것 — A(블록 파서 전용 술어) · `VERSION` 유지

- **A**: `_NON_BLOCK_TAGS` 선례를 따라 `_BlockParser` 만 읽는 `_is_hidden(tag, attrs)` 로
  다섯 모양의 텍스트를 블록에 **안 담는다**. 색인 경로·스키마·`data/crawl.db` 무변경.
- **B 를 버린 이유가 계획서가 쓴 것보다 셌다** — `_SKIP_TAGS` 는 **태그 이름만** 보는
  집합이라 다섯 중 넷(속성 둘 · 인라인 스타일 둘)을 **아예 못 잡는다.** 가장 짧아 보이던
  안이 가장 적게 닫는다. **C**(감점)는 밀도가 높으면 여전히 이겨 0/5 를 보장 못 한다.
- **`VERSION` 은 안 올린다** — 필드 삭제 0 · `position` 의 **정의** 무변, 바뀌는 것은
  **값**이고 방향이 계약을 어기던 쪽에서 지키는 쪽이다. 같은 API 선례가 있다
  (계획 48 의 `MAX_PASSAGE_HTML` 캡도 같은 질의의 결과를 바꿨고 `VERSION` 은 1 유지).
  대신 `README.md` 의 `/passages` 절에 한 줄 적는 것을 개발 계약에 넣었다.

## 설계가 오늘 직접 잰 것 (2026-09-03 · 반복 289 · 제품 `src/` 0줄)

시제품은 `extract._BlockParser` **상속**으로 만들었다 — 색인 경로는 구조적으로 안 지난다.

| 잰 것 | 값 |
|---|---|
| **가장 위험한 가정 — 거짓이었다** | 종료 태그 없는 요소(`<img aria-hidden="true">` 등)가 숨김 스택을 못 닫아 **4/4 모양에서 3블록 → 1블록**. 설계 안에서 `_VOID_TAGS` 가드로 닫고 다시 쟀다 |
| `indexer.passages()`(임시 DB) | 숨은 텍스트 **5/5 → 0/5** · 본문 문단 **0/5 → 5/5** · `position` **1 → 0** |
| 숨은 블록만 매치인 문서 | 문단 **1건 → 0건**(첫 블록으로 안 대신한다) |
| 오탐 방향 — 자 셋 | 코퍼스 64문서(블록 253) 차이 **0** · `tests/` HTML 리터럴 263개(블록 298) 차이 **0** · 음성 6종 **6/6 안 문다** |
| 불변식 | 숨김 있는 HTML 에서 **세 번째 예외** · 정상 HTML 64문서 전수 **True** |

## 품질·성능 축 — 기준선 그대로 (앞 반복 실측)

ko **20/20** · en **19/20** · 순위 1위 39 · 매치 평균 14.0(최소 11) ·
문단 정확도 **100.0%** · 채택률 99.5% · p95 **1.48ms** · `perf_search` p95 **8.97ms** ·
`search_api` p95 2.11ms · 처리량 [열림] **10.24/s** · [차단] **10.23/s** ·
문서집합 sha1 `541d455a…c078654b` · 디자인 4축(외부 0 · JS 0 B · 텍스트 4.87:1 · 링 3.56:1).

## 저장소 불변

이 반복은 **문서만** 고쳤다 — 제품 `src/` **0줄** · `e2e/` 무변 · `docs/specs/` 무변 ·
`data/crawl.db` sha256 `85c96744…75bda18` **무변경** · 새 의존성 0 ·
`README.md` 무변경(단위 **579건** · e2e **20종** 이 이 기점에서 그대로 참이다).
탐침은 저장소 **밖** scratchpad 에서 돌았고, 되돌림은 초록이 아니라 `git diff` 로 확인했다.

## 러너 규율 — 이번 반복 0회 (누적 30회)

러너 호출 **1회**(단위 1) 맨몸·단독, `PYTHONPATH=src python3 -m unittest discover -b -s tests`
가 `Ran 579 tests / OK` rc 0. **열세 반복 연속 0회다.** 러너가 아닌 곳(`git`·`grep`·`wc`·
`sed`·탐침·heredoc)에서 `&&` **0회** · `;` **약 6회** · 파이프 **0회** — 계수 밖이지만 남긴다.

## 문서 마감

`status.md`(이 문서 — `iteration` **289** · `phase` **개발**) · `metrics.md`(`반복` **289** ·
`## phase 분포` 설계 **18**) · `index.md`(51번 행에 설계 결과) · 새 설계서
`docs/design_hidden-passage.md` · `history_current.md` append(설계 1 항목).
**회전을 돌렸다** — 항목을 붙인 뒤 세니 **325줄**이라 계획 50 `runner-quiet` 전체(282~286)를
`history_046.md` 로 밀었다(→ **138줄**). 명부(`digest ## 완료`)에 이름을 더하고 회전 서술을
그 줄에 이어 붙였으므로 **새 색인 구멍 0**. `digest.md` **195줄**(상한 200 안).
`반복` 은 `status.md` 의 `iteration` 과 함께 움직인다(`IterationSyncTest`).

## 다음 — 개발 1/1

`src/websearch/extract.py` 에 `_VOID_TAGS`·`_ZERO_FONT`·`_is_hidden` 과 `_BlockParser` 의
메서드 셋(설계 6절 계약), `tests/test_extract.py` 에 새 단언. TDD 로 RED 를 먼저 보고
변이는 **양방향**으로 심는다 — 좁아지는 쪽 5(다섯 모양 각각) · 넓어지는 쪽 3
(`_is_hidden` 늘 True · `font-size:0` 부분문자열 · `_VOID_TAGS` 가드 제거).

## 원격 — `origin/main` 은 계획 47 까지다

- **PR #7** — `loop/merge-48-50` → `main`, 계획 48·49·50 을 한 PR 로 담았다. **OPEN·미병합.**
  병합은 **사용자가 처리한다** — 이 반복은 PR 을 열지도 닫지도 않았고 그 브랜치에 커밋하지도 않았다.
- **그래서 계획 51 의 기점은 `main` 이 아니다.** `origin/main`(`687a159`)에는 계획 48·49·50 이
  없어 `README.md` 의 「단위 579건 · e2e 20종」과 `tests/test_readme.py` 의 건수 단언이
  거기서는 RED 다. `d5367fa`(`loop/merge-48-50` HEAD)에서 `loop/hidden-passage` 를 땄다.
- 앞선 병합: PR #6 = 계획 44~47(`687a159`). 충돌 0.

## 사람이 정할 것 — 다섯 (PR #7 이 붙었다)

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
2. **`--focus` 는 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 이 0 일
   때만 이웃이 되고, 검사기가 매 실행 offset > 0 을 확인한다(실측 2px).
3. **반응형 360px 미검증** — 브라우저가 없어 이 저장소의 누구도 그 화면을 못 그린다.
4. **회전 규약·러너 규율의 저장소 밖 절반**과 **사양이 남긴 둘**(`docs/specs/concept.md` 의
   `## 사람이 정할 것` — 속도 제한 시점, 사양 숫자 90%·500ms·60회/분이 초안이라는 것).
5. **PR #7 병합** — 위 「원격」 절.
