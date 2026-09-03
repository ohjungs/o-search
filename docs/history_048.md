# 반복 기록 아카이브 — 계획 51 `hidden-passage` 설계 1(반복 289)과 개발 1(반복 290)

<!-- history_current.md 에서 밀려난 원본. 수정·삭제 금지. -->

## 2026-09-03 17:35 | hidden-passage | 설계 1 | 시도0

- 한 일: **`docs/design_hidden-passage.md` 를 세워 갈림길 넷을 닫고 `VERSION` 을 판정했다.**
  제품 `src/` **0줄** — 시제품은 `extract._BlockParser` 를 **상속**해 만들었고(탐침 파일은
  저장소 밖 scratchpad), 판정을 `extract` 모듈에 꽂아 `indexer.passages()` 를 진짜 임시 DB
  위에서 불렀다. `git diff` 빈 출력으로 원복이 아니라 **애초에 안 고친 것**을 확인했다.
- **결론: A(블록 파서 전용 술어).** `_NON_BLOCK_TAGS` 선례를 따라 `_BlockParser` 만 읽는
  `_is_hidden(tag, attrs)` 로 다섯 모양의 텍스트를 블록에 안 담는다. 색인 경로·스키마·
  `data/crawl.db` 무변경, 되돌리기는 커밋 하나 revert(플래그를 안 쓰는 사유도 적었다).
- **B 를 버린 이유가 계획서가 쓴 것보다 셌다.** 계획서는 「가장 짧지만 재색인」이라 적었는데,
  실제로 `_SKIP_TAGS` 는 **태그 이름만** 보는 집합이라 다섯 중 넷(속성 둘 · 인라인 스타일 둘)을
  **아예 못 잡는다** — 가장 짧아 보이던 안이 가장 적게 닫는다. C 는 감점이라 밀도가 높으면
  여전히 이겨 완료 기준 1번(0/5)을 보장 못 하고, 블록 튜플 폭까지 바꿔야 한다.
- **가장 위험한 가정을 깼고, 거짓이었다**(설계 룰 3-2). «시작 태그에서 열고 종료 태그에서
  닫는 스택이면 충분하다» → **종료 태그가 없는 요소가 문서 나머지를 통째로 삼킨다.**
  `<img aria-hidden="true">`(장식 아이콘) · `<hr hidden>` · `<input hidden>` ·
  `<br style="display:none">` **4/4 에서 3블록 → 1블록**. 개발로 넘기지 않고 설계 안에서
  `_VOID_TAGS` 가드(HTML void 14개)를 넣어 다시 쟀다 — 4/4 무해.
- 결과: 다섯 모양 각 **2블록 → 1블록**(숨은 블록 1 → 0 · 본문 문단 5/5 생존) ·
  `indexer.passages()` 가 고른 숨은 텍스트 **5/5 → 0/5**, 본문 문단 **0/5 → 5/5** ·
  숨은 블록만 매치인 문서의 문단 **1건 → 0건**. **오탐 방향은 세 자로 쟀다** —
  평가 코퍼스 64문서(블록 253) 차이 **0** · `tests/` 의 HTML 리터럴 263개(블록 298) 차이 **0** ·
  음성 6종(`aria-hidden="false"`·`font-size:0.9em`·`font-size:10px`·`class="hidden-md"`·
  `display:block`·문단 안 인라인 숨김) **6/6 안 문다**.
- **`font-size:0` 이 이 판정에서 오탐이 가장 가까운 자리다** — 부분문자열로 보면
  `font-size:0.9em`(보이는 작은 글씨)을 문다. 뒤에 숫자·점이 오면 안 물게 정규식으로 못 박고,
  그것을 부분문자열로 되돌리는 변이가 새 단언을 죽이도록 개발에 넘겼다.
- **`VERSION` 은 안 올린다.** 사양 기능 9 는 «필드 삭제·뜻 변경» 인데 필드 0개 삭제,
  `position` 의 정의(«결과의 순번») 무변이고 바뀌는 것은 **값**(실측 1 → 0)이다. 방향이
  계약을 어기던 쪽에서 지키는 쪽이고, 같은 API 안에 선례가 있다 — 계획 48 의
  `MAX_PASSAGE_HTML` 캡도 같은 질의의 결과를 바꿨지만 `VERSION` 은 1 그대로였다.
  대신 「조용한 변경」이 안 되게 `README.md` 의 `/passages` 절에 한 줄 적는 것을 계약에 넣었다.
- 불변식 `" ".join(blocks) == extract_text()[1]` 에는 **세 번째 예외**를 적는다(숨김 있는
  HTML). 정상 HTML 에서는 그대로다 — 코퍼스 64문서 전수 **True**.
- 결과: 단위 **579건 OK** rc 0(맨몸·단독 1회) · 제품 `src/` 0줄 · `e2e/`·`docs/specs/`·
  `data/crawl.db` 무변경 · 새 의존성 0 · 러너 규율 위반 **0**(열세 반복 연속).
- 다음: **개발 1/1** — `src/websearch/extract.py` 에 `_VOID_TAGS`·`_ZERO_FONT`·`_is_hidden`
  과 `_BlockParser` 의 메서드 셋, `tests/test_extract.py` 에 새 단언(설계 6절 목록).
  TDD 로 RED 를 먼저 보고, 변이는 좁아지는 쪽 5 · 넓어지는 쪽 3 을 양방향으로 심는다.

## 2026-09-03 18:20 | hidden-passage | 개발 1 | 시도0

- 한 일: **설계 A 를 그대로 심었다** — `extract.py` 에 `_VOID_TAGS`(HTML void 14개) ·
  `_ZERO_FONT` · `_is_hidden(tag, attrs)` 와 `_BlockParser` 의 메서드 셋(`handle_starttag`
  에서 열고 `handle_endtag` 에서 `_open` 과 **같은 관용구**로 닫고, `handle_data` 에서
  **애초에 안 담는다**). **TDD — RED 를 먼저 봤다**: 새 단언만 `FAILED (failures=14)`,
  구현 뒤 `Ran 585 tests / OK` rc 0(맨몸·단독). 제품 순증 **약 45줄**, 파일 1개.
- **설계가 지목한 무변경 지점을 지켰다** — `_SKIP_TAGS`·`_INLINE_TAGS`·`_NON_BLOCK_TAGS`·
  `_normalize`·`_TextParser` 는 `git diff` 에 **한 줄도 안 나온다.** 그래서 색인 본문·
  스키마·`data/crawl.db` 가 구조적으로 안 움직이고 재색인이 0 이다.
- **변이 8건을 양방향으로 심어 전부 RED 를 눈으로 봤다**(`.mutation-lock` 걸고 매번 원복,
  마지막에 `git diff -- src/` 로 확인 · 커밋된 변이 0). 좁아지는 쪽 5 는 다섯 모양을
  각각 지우니 **그 모양의 단언만** 빨개졌다(각 2~4건, 전부 새 단언). 넓어지는 쪽 셋 —
  ⓐ `_is_hidden` 이 늘 True → **기존 `TestExtractBlocks` 가 무너진다**(오탐이 이 계획의
  제일 위험이라는 것을 스위트가 증명한다) · ⓑ `_ZERO_FONT` → `"font-size:0" in style`
  → 음성 단언 `font-size:0.9em` **하나만** 죽는다 · ⓒ `_VOID_TAGS` 가드 제거 → void
  4모양 전부 «앞 문단만 남는다». 설계가 예고한 자리와 죽은 자리가 정확히 같다.
- **계약이던 문서 두 줄도 같은 커밋이다** — `README.md ## 품질 기준` 아래에 «`/passages` 는
  화면에 안 보이는 텍스트를 근거로 내지 않는다» 를 적고(`VERSION` 을 안 올리는 대신 조용한
  변경이 안 되게 한 것 · 설계 5절), 단위 건수를 **579 → 585** 로 고쳤다(`test_readme.py`
  자신이 그 숫자를 잰다 — 안 고치면 첫 실행이 RED 다).
- 결과: 단위 **585건 OK**(13.476초) rc 0 · 새 단언 **6건**(extract 5 · indexer 1) ·
  `e2e/`·`docs/specs/`·`data/crawl.db` 무변경 · 새 의존성 0(`re` 는 stdlib) ·
  러너 호출 **11회 전부 맨몸·단독**(변이 8회는 `python3 -B` — 선례 `history_042`).
- 다음: **테스트 1/1** — 완료 기준의 「그대로여야 할 것」 중 스위트 밖 축(코퍼스 64문서
  블록 목록 차이 0 · `passage_eval` 정확도·p95 · `quality_eval` ko/en)을 실제로 재고,
  갭 탐색으로 새 단언이 못 잡는 자리를 찾는다.
