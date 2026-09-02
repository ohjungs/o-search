# 아카이브 — 계획 47 `db-open-atomic` 의 개발 두 반복 (2026-09-02)

<!-- 회전으로 `history_current.md` 에서 밀려났다. 수정·삭제 금지.
     `digest.md` 의 `## 완료` 절에 1~2줄 요약이 있다. -->

## 2026-09-02 04:50 | db-open-atomic | 개발 1/2 | 시도0

- 한 일: **DB 를 여는 자리를 하나로 만들었다.** `src/websearch/indexer.py` 에
  `_connect(db_path)` 를 신설하고(`file:…?mode=rw` URI · `timeout=30`) 세 호출부
  (`index_pages`·`_doc_count`·`search`)의 `os.path.exists` + `sqlite3.connect` 짝을
  전부 그것으로 갈았다. `tests/test_indexer.py` 에 `TestDbOpenIsAtomic` 6건 신설.
  `README.md` 의 단위 건수 495 → 501. 제품 `src/` **+31 / -8줄**, 파일 1개.
- **RED 를 눈으로 봤다** — 레이스 3건이 먼저 각자 다른 방식으로 죽었다.
  `search` 는 `FileNotFoundError not raised`(빈 DB 를 만들어 놓고 `[]` 를 냈다) ·
  `_doc_count` 는 값은 0 인데 **`빈 DB 파일이 남았다`** · `index_pages` 는
  `NoCrawlDataError`(만든 빈 DB 에 `pages` 가 없으니까). **세 자리가 한 뿌리인데
  증상은 셋으로 갈라져 보인다** — 그래서 계획이 「없는 파일을 절대 만들지 않는다」
  하나를 완료 기준으로 삼은 것이 옳았다.
- **레이스 훅은 `-wal`·`-shm` 까지 지운다** (`rm crawl.db*` 와 같다). 본 파일만 지우면
  `store.py` 가 켠 WAL 의 사이드카가 남아 «남은 `-wal` 이 무슨 일을 하는가» 가 변수로
  끼어든다 — 재는 것이 흐려지느니 사람이 실제로 하는 동작에 맞췄다.
- **변이 넷을 실제로 심어 죽는 것을 봤다**(사본 아님 · 제자리에서 심고 즉시 원복,
  `PYTHONDONTWRITEBYTECODE=1`). M1 `mode=rw`→`rwc`: 신규 6건 중 3건 + **기존
  `test_missing_db_raises` 2건까지** 죽어 6실패다. M2 `pathname2url` 제거:
  `a b#c?d.db` 하나만 죽는다 — **한글 경로(`남의.db`)를 지나는 기존 테스트는 멀쩡하다**.
  설계가 «인용 없이도 우연히 돌아간다» 로 적어 둔 그대로였다. M3 사후 `exists` 삭제:
  디렉터리를 준 자리가 `FileNotFoundError`(→503)로 오분류돼 죽는다. M4 `_doc_count` 의
  `except` 삭제: 2건. **넷 다 사망.**
- **M2·M3 를 재는 두 건은 RED 를 안 지난다** — 오늘 코드에도 초록이라 «심어 보기»
  말고는 물릴 이빨이 있는지 알 방법이 없다. 새 갈래를 안 만들고 **새 구현이 열 수 있는
  구멍**을 막는 단언이라 그렇다. 변이를 안 심었으면 장식 둘을 커밋할 뻔했다.
- 계획 46 의 번역표(`serve.py`)는 **0줄**이다. `_connect` 가 던지는 것이
  `FileNotFoundError`(→503)와 `sqlite3.OperationalError`(→500) 둘뿐이라 표가 그대로 참이다.
- 결과: 단위 **501건 OK · 12.400초**(맨몸). 러너 호출 6회 · **출력 조작 0회**
  (변이 4회는 `tests.test_indexer` 만, 앞뒤로 `discover tests` 전체 1회씩).
  의존성 0(`urllib.request` 는 stdlib) · `data/crawl.db` 무변경 · 스키마 무변경.
- 회전 1회: `json-contract` e2e 반복을 `history_028.md` 로 밀어냈다(**315줄 → 247줄**).
  상한 300 을 넘긴 그 반복에서 바로 돌렸다.
- 다음: **개발 스텝 2/2** — `if not match: return []` 를 옛 색인 검사 **뒤**로 옮긴다.

## 2026-09-02 04:50 | db-open-atomic | 개발 2/2 | 시도0

- 한 일: `src/websearch/indexer.py` 의 `search()` 에서 무토큰 조기 반환
  (`if not match: return []`)을 **DB 를 여는 자리와 옛 색인 검사 뒤**로 옮겼다.
  제품 **+6 / -2줄** · 파일 1개 · 의존성 0. 테스트 3건 추가
  (`tests/test_indexer.py` 2 · `tests/test_serve.py` 1) · `README.md` 카운트 1줄.
- **RED 를 눈으로 봤다 — 셋 다 실패했고 세 번째가 구멍을 그대로 찍어 냈다.**
  손상 DB + `q=%01` 이 `200 {'results': []}` 를 냈다(`test_serve.py` 의
  `test_corrupt_db_is_500_for_a_tokenless_query_too` 실패 메시지에 그 JSON 이 통째로
  찍혔다). 옛 색인 + `q=%01` 은 `StaleIndexError` 가 안 났고, 손상 DB + `q=%01` 은
  `sqlite3.DatabaseError` 가 안 났다.
- **판정이 질의 내용에 달려 있었다는 것이 이 스텝의 전부다.** 같은 파일, 같은 고장인데
  `q=김치` 면 500, `q=%01` 이면 200 이었다. `test_corrupt_db_is_500_not_503` 이
  *"손상은 기다린다고 낫지 않는다"* 며 500 을 못박아 뒀지만 **그 단언이 질의어 하나에만
  걸려 있었다** — 계약을 재는 단언도 재는 입력이 좁으면 우회된다.
- **변이 둘을 제자리에 심어 죽는 것을 봤다**(`.mutation-lock` 걸고, 즉시 원복 ·
  `PYTHONDONTWRITEBYTECODE=1`). M5(조기 반환을 `_connect` **앞**으로 되돌림): 신규 3건
  전부 사망. M6(조기 반환을 **옛 색인 검사 앞**에 둠): **정확히 1건**만 사망
  (옛 색인 + `q=%01`) — 설계가 «앞에 두면 구멍이 절반 남는다» 로 예측한 그 한 건이다.
  **M6 이 이 스텝에서 유일하게 값을 낸 변이다** — 손상 DB 쪽 두 건은 M6 아래에서도
  초록이라, 자리를 «`_connect` 뒤» 까지만 옮기고 멈췄으면 절반짜리 수정을 초록불 위에서
  커밋할 뻔했다.
- **되돌림에서 실물 사고가 하나 났고 `git diff` 가 잡았다** — M6 원복 편집이 주석 블록을
  **두 벌** 남겼다(`if not match: return []` 이 연달아 둘). 테스트는 504건 전부 초록이라
  스위트로는 안 보였다. **변이 원복은 초록이 아니라 `git diff` 로 확인한다** —
  등가 중복은 통과하면서 남는다.
- 결과: 단위 501 → **504건 OK · 12.335초**(맨몸). e2e **7종 실행 전부 통과** —
  `search_api`(p95 2.10ms) · `indexer` · `tokenizer` · `pagination_ui`(4축 통과) ·
  `non_ascii` · `noindex` · `indexer_interrupt`. 성능 `perf_search` p95 **8.92ms**
  (기준선 8.71ms · 예산 300ms 의 3.0%) · 품질 ko **20/20** · en **19/20**(합격선 80%).
- **README 카운트 가드가 두 반복 연속 울었다** — 테스트 +3 에 `test_readme` 즉시 FAILED.
  `README.md` 의 `단위 501건` → `504건` 한 곳(`e2e/*.py` 19 그대로).
- 러너 호출 **6회 · 출력 조작 0회**(전체 `discover tests` 3회 · 변이 2회는
  `tests.test_indexer tests.test_serve` 로 범위만 좁혔다 · e2e·성능·품질은 각각 맨몸 1회).
  `.mutation-lock` 은 지웠고 `git status` 로 `src/` 에 커밋된 변이 0 을 확인했다.
  의존성 0 · `data/crawl.db` 무변경 · 스키마 무변경 · `serve.py` **0줄**.
- **계획 47 의 두 스텝이 끝났다.** 계획서 4절이 세운 기대 결과 다섯 칸이 전부 참이다.
- 다음: **테스트 phase** — 갭 탐색(계약 표의 남은 칸을 재는 단언이 있나).
