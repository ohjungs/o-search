# 반복 기록 아카이브 — 계획 48 `passage-api` 의 테스트 1 (반복 255)

<!-- history_current.md 에서 밀려난 원본. 수정·삭제 금지. -->
## 2026-09-02 13:20 | passage-api | 테스트 1 | 시도0
- 한 일: **설계 변이 표 M1~M8 을 전수 재확인하고, 스텝 3 산출물(`e2e/passage_eval.py`)의
  갈래를 붙드는 테스트를 새로 세웠다**(`tests/test_passage_eval.py`, 9건). 제품 `src/` **0줄**.
- **M1~M8 여덟 전부 제자리에 다시 심어 RED 를 눈으로 봤다**(`.mutation-lock` 걸고,
  각 변이마다 되돌린 뒤 **`git diff -- src/` 0줄로** 확인 · 커밋된 변이 0):
  M1(버퍼 비우기 삭제) `test_join_equals_body` 외 14건 · M2(마지막 flush 삭제)
  **`test_last_block_survives_broken_html` 단 1건** — 설계가 *"정상 HTML 은 닫는 태그가
  flush 를 대신해 살아남는다"* 고 적은 그대로다 · M3(블록 마커를 `_normalize` 경로에)
  **기존 `TestExtractText` 8건이 죽는다 — 대조군이 색인 경로를 지킨다** ·
  M4 `test_document_with_no_matching_block_is_not_returned` + `..._crosses_a_block_boundary...`
  둘 · M5 `test_position_counts_only_non_empty_blocks`(7≠1) 외 12건 ·
  M6 `test_page_two_is_400...` + 스키마 · M7 **`TestPassagesSchemaVersion` — 대조군** ·
  M8 `test_passage_is_cut_at_max`(5999≠2000).
- **표의 «M4 → passage_eval 정확도 하락» 칸을 실측으로 다시 판정했다.** M4 를 심고
  러너를 돌리니 정확도 100.0% → **99.5%**, 채택률 99.5% → **100.0%**, **rc 는 그대로 0**.
  즉 **러너는 M4 를 안 죽인다** — 죽이는 것은 단위 둘이다. 직전 반복이 *"근거가 아니라
  관측 기록"* 이라고 적은 것이 맞았고, 표는 이미 그렇게 적혀 있다.
- **갭 탐색에서 결함 하나를 찾아 닫았다(중요도 9).** `passage_eval.main()` 의
  `assert serve.PAGE_SIZE == serve.PASSAGE_LIMIT` 는 **`assert` 라서 파이썬 기본 종료
  코드 1 로 죽는다** — 1 은 «미달»(정확도<90% 또는 p95>500ms)에 예약된 값이라, 설정이
  갈린 것이 **«사양 미달» 로 보인다**. W 변이가 G7 에서 드러내고 `--repeat` 가드가
  되풀이한 *«측정 불능이 미달 코드로 샌다»* 와 **같은 원인의 형제 자리**가 안 고쳐진 채
  남아 있었다. 실측(`PASSAGE_LIMIT=7`): rc **1** + 트레이스백. 세 줄 가드로 **rc 2** 로
  돌렸다(`e2e/passage_eval.py` +8/-4, 제품 아님).
- **G7 은 닿을 수 없는 가드였다** — `" ".join(wrap(b)) == b` 는 `split(". ")`/`join` 의
  **대수적 항등식**이라 어떤 본문에도 참이다(합성 12종 · 코퍼스 64/64 · 무작위 2만종
  위반 **0건**). 러너 설명의 *"`wrap` 의 단언이 매 실행 확인한다"* 는 아무것도 확인하지
  않는다. 값이 0이라 안 지우고, 판단 근거를 테스트로 남겼다(`digest` 에 올렸다).
- **새 테스트도 변이로 이빨을 확인했다**(같은 `.mutation-lock` 아래, 전부 원복):
  PAGE_SIZE 가드를 `assert` 로 되돌리니 rc **1**(RED) · `--repeat` 가드를 `if False` 로
  하니 **`UnboundLocalError` rc 1** 둘 다 RED(개발이 만난 그 오류가 그대로 재현됐다) ·
  G4 를 비우니 G4 테스트 RED(**G6 가 뒤를 받쳐 rc 2 는 유지** — 방어가 두 겹이다).
- 결과: **단위 553건 OK(13.304초)** — 맨몸·단독, 파이프·리다이렉션 0회.
  `e2e/passage_eval.py` 단독 rc **0**(정확도 100.0% · p95 1.73ms · 채택률 99.5%).
  **README 카운트 가드가 제 일을 했다** — 544→553 이 안 맞아 빨개졌고 README 를 고쳤다.
- 실측: 제품 `src/` **0줄**(`git diff -- src/` 0) · 새 파일 1개(`tests/test_passage_eval.py`)
  · 의존성 0 · 변이 **12회**(M1~M8 + W 넷) 전부 원복 · 커밋된 변이 0 ·
  `data/crawl.db`·스키마·`docs/specs/` 무변경.
- 다음: **리뷰 phase.** 볼 자리 — 종료 코드 1/2 의 갈림이 이제 러너 세 곳(`--repeat`·
  fixture·PAGE_SIZE)에 흩어져 있다. 한 벌로 묶을지가 판단거리다.


