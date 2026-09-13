# 프로젝트 정보

<!-- 확인 안 된 명령은 적지 않는다 — 여기 있는 것은 전부 한 번 돌려 보고 적었다. -->

## 명령

**아래 명령은 전부 맨몸으로 돈다** — 파이프·`grep`·`head`·`tail`·리다이렉션을 붙이지 않는다.
붙이면 종료 코드와 판정 줄이 잘려 **실패가 통과로 보인다**(`digest ## 반복 실패` 최다 재발 ·
방아쇠는 언제나 「이미 초록일 것 같은 실행」이다). `-b` 가 **통과한** 것의 출력만 삼키므로
화면이 짧다 — 어길 이유가 없고, 실패한 것의 stdout/stderr 는 보고서에 그대로 나온다.

- **테스트(전체)**: `PYTHONPATH=src python3 -m unittest discover -b tests`
  (2026-09-03 실행 확인 · 오늘 782건 약 19초라 빠름/전체 구분 없음 · 린트·타입체크는 없다)
- **변이 검사**: `PYTHONDONTWRITEBYTECODE=1` **과** `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를
  **함께** 준다. 앞엣것만으론 부족하다 — 이 기계의 시스템 파이썬은 캐시를 **저장소 밖**
  (`~/Library/Caches/com.apple.python`)에 쌓고 그 플래그는 쓰기만 막지 **읽기는 안 막는다**
  (계획 57 리뷰가 실제로 속았다 · 경위는 `baselines.md`)
- **e2e 18종**: `PYTHONPATH=src python3 e2e/<이름>.py` — `crawl_e2e` `indexer_e2e` `noindex_e2e` `search_api_e2e`
  `crawl_delay_e2e` `non_ascii_e2e` `hidden_passage_e2e` `design_check` `tokenizer_e2e` `domain_key_e2e` `deadline_e2e`
  `interrupt_e2e` `indexer_interrupt_e2e` `crawl_politeness_e2e` `pagination_ui_e2e` `recrawl_e2e` `retry_interval_e2e` `url_normalize_e2e`.
  **종료 2 는 실패가 아니라 측정 불능이다.** 명부가 낡으면 `test_docs.py` 가 문다 · 나머지는 **`docs/baselines.md`**
- **측정**: `e2e/perf_crawl.py`(처리량) · `e2e/perf_search.py [문서수] [반복]`(검색 지연) ·
  `e2e/quality_eval.py` · `e2e/passage_eval.py`. 합격선은 아래, 기준선은 `baselines.md`

## 브랜치·소유자

- 기본 브랜치: `main` (보호 — 루프는 `loop/<slug>` 브랜치에서 작업)
- 소유자 파일: 없음 (혼자 쓰는 저장소)

## 품질 기준 <!-- docs/specs/concept.md 4축의 실행 명령판 -->

**기준선 숫자·변이 확인 기록·캡 설계 논증은 `docs/baselines.md` 로 옮겼다**(계획 97) —
예산 밖이라 **그 도구를 실제로 쓰는 반복에만** 편다. 여기 남은 것은 칠 명령과 합격선뿐이고,
**어느 숫자가 합격 판정이고 어느 것이 회귀용 기준선인지는 그쪽이 축마다 적었다.**

| 축 | 명령 (`PYTHONPATH=src python3 …`) | 합격선 |
|---|---|---|
| 검색 품질 | `e2e/quality_eval.py` | recall@10 이 ko·en **둘 다 80%** 이상 (기능 2) |
| 근거 문단 | `e2e/passage_eval.py` | 정확도 **90%** (기능 8) · p95 **500ms** (성능 5) |
| 검색 지연 | `e2e/perf_search.py` | `GET /search` p95 **300ms** (성능 1) |
| 디자인 4축 | `e2e/design_check.py` | JS gzip **50KB** · 대비 **4.5:1** · 360px 무스크롤 · LCP 대리 |
| 크롤 간격 | `e2e/crawl_delay_e2e.py` | robots `Crawl-delay` 와 **1초 하한** (크롤 윤리 1순위) |

**0/1/2 관용구는 셋만 쓴다**(`quality_eval`·`passage_eval`·`design_check`) — 0 통과 · 1 기준 위반 ·
**2 는 판정이 아니라 「재지 못했다」**. **`perf_search`·`crawl_delay_e2e` 는 맨 `assert` 라 2 를 못 낸다**(566 실측).

- **재방문 주기**: `store.FRESH_DAYS` **= 30** 일(2xx) · `store.RETRY_DAYS` **= 15** 일(그 밖).
  **되돌리는 법은 플래그가 아니라 이 상수다** — 크게 잡으면 재방문이 꺼진다
- **근거 문단 입력 캡**: `indexer.MAX_PASSAGE_TAGS` **= 3,000** 태그가 재파싱 입력을 자르고
  `indexer.MAX_PASSAGE_HTML` **= 2,000,000** 이 그 바깥 울타리다. 올리는 것은 단위
  `TestPassages` 가 막는다(`캡 × PASSAGE_LIMIT` **8,000 × 10** 동결) — 유도는 `baselines.md`

## 한도

- 크롤러: 도메인당 요청 간격 1초 이상, robots.txt 준수 — 위반 코드는 RED
- 외부 네트워크를 때리는 테스트 금지 — 모킹 또는 로컬 테스트 서버만

## 건드리지 않을 곳

- `docs/specs/` — 읽기 전용 (사용자 영역)
