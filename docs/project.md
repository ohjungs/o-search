# 프로젝트 정보

<!-- 확인 안 된 명령은 적지 않는다 — 여기 있는 것은 전부 한 번 돌려 보고 적었다. -->

## 명령

**아래 명령은 전부 맨몸으로 돈다** — 파이프·`grep`·`head`·`tail`·리다이렉션을 붙이지 않는다.
붙이면 종료 코드와 판정 줄이 잘려 **실패가 통과로 보인다**(`digest ## 반복 실패` 최다 재발 ·
방아쇠는 언제나 「이미 초록일 것 같은 실행」이다). `-b` 가 **통과한** 것의 출력만 삼키므로
화면이 짧다 — 어길 이유가 없고, 실패한 것의 stdout/stderr 는 보고서에 그대로 나온다.

**그리고 조항 말고 기제가 하나 생겼다 — `scripts/verdict.sh`** (계획 106). 아무 명령이나
감싸면 **판정과 `rc` 를 stdout 의 마지막 한 줄**로 다시 찍는다. 그래서 그 자를 통해 부른
것에는 **`| tail -1` 을 붙여도 판정이 산다** — 가장 자주 붙는 손이 오히려 판정만 남긴다.
**환경 변수는 래퍼 앞에 둔다**(`VAR=val scripts/verdict.sh <명령>`) — 뒤에 두면 명령
이름으로 읽혀 `rc=127` 이다. **조항은 그대로 산다**: 래퍼가 덮는 것은 「래퍼를 통해 부른
것」뿐이고, 러너를 맨손으로 직접 치는 길은 열려 있다.

**모집단도 이제는 지킨다**(계획 107). 전에는 `discover` 에 시작 디렉터리를 빠뜨리면
`Ran 0 tests / OK / rc=0` 이 **정직하게** 실려 나왔다 — 0건을 돌렸으니 0건이 통과였고,
가려진 것은 출력이 아니라 **모집단**이라 조항도 래퍼도 구조적으로 못 덮었다. 두 자리를
함께 막았다: **① `tests/__init__.py` 가 덫을 뿌리에서 없앴다** — 시작 디렉터리를 빼도
전수가 그대로 돈다 **② 래퍼가 `Ran 0 tests` 를 판정이 아니라 사고로 읽는다** — `rc` 가
0 이던 0건 실행은 **`모집단 0` · `rc=2`** 로 나간다(이 저장소에서 2 는 판정이 아니라
「재지 못했다」다). `rc` 가 0 이 아닌 0건은 이미 빨가니 **안 건드린다.**
**건수의 «값» 은 여전히 README 의 단위 수 가드가 읽는다** — 여기가 무는 것은 0 대 0 아님뿐이다.

- **테스트(전체)**: `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests`
  (2026-09-19 실행 확인 · 829건 약 26초라 빠름/전체 구분 없음 · 린트·타입체크는 없다)
  **시작 디렉터리 `tests` 는 그대로 적는다** — 이제는 빼도 829건을 돌지만(계획 107 의
  `tests/__init__.py`), 적어 두는 쪽이 무엇을 재는지 명시한다. 실제 건수는 README 의
  단위 수 가드와 대조한다(`tests/test_readme.py`). 래퍼 없이 맨몸으로 돌려도 된다 —
  조항이 그 자리를 지키고, **0건으로 끝나는 길은 래퍼 쪽이 `rc=2` 로 문다**
- **변이 검사**: `PYTHONDONTWRITEBYTECODE=1` **과** `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를
  **함께** 준다. 앞엣것만으론 부족하다 — 이 기계의 시스템 파이썬은 캐시를 **저장소 밖**
  (`~/Library/Caches/com.apple.python`)에 쌓고 그 플래그는 쓰기만 막지 **읽기는 안 막는다**
  (계획 57 리뷰가 실제로 속았다 · 경위는 `baselines.md`)
- **e2e 18종**: `PYTHONPATH=src python3 e2e/<이름>.py` — `crawl_e2e` `indexer_e2e` `noindex_e2e` `search_api_e2e`
  `crawl_delay_e2e` `non_ascii_e2e` `hidden_passage_e2e` `design_check` `tokenizer_e2e` `domain_key_e2e` `deadline_e2e`
  `interrupt_e2e` `indexer_interrupt_e2e` `crawl_politeness_e2e` `pagination_ui_e2e` `recrawl_e2e` `retry_interval_e2e` `url_normalize_e2e`.
  **종료 2 는 실패가 아니라 측정 불능이다.** 명부가 낡으면 `test_docs.py` 가 문다 · 나머지는 **`docs/baselines.md`**
- **측정**: `e2e/perf_crawl.py`(처리량) · `e2e/perf_search.py [문서수] [반복]`(검색 지연) ·
  `e2e/perf_memory.py [작은규모] [큰규모] [반복]`(서버 상주 RSS — 컨셉 경량 2) ·
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
| 서버 상주 메모리 | `e2e/perf_memory.py` | 100만 문서 외삽 **2GB** (경량 2) — **이 자는 예산과 비교해 실패하지 않는다**. 오늘 규모의 수는 기준선이고 무는 것은 «기울기» 다(`baselines.md`) |
| 크롤 간격 | `e2e/crawl_delay_e2e.py` | robots `Crawl-delay` 와 **1초 하한** (크롤 윤리 1순위) |
| 의존성 0 | `-m unittest tests.test_deps` | 표준 라이브러리 밖 임포트 **0건** (경량 3·5) — 예산이 아니라 **불변식**이라 어기면 실패다. **표에서 유일하게 전수 안에서 도는 줄**이고, 그것이 이 자의 요점이다: 나머지 여섯은 사람이 기억해서 쳐야 하지만 이 축은 **안 쳐도 물린다**. **3.9~3.14 확인**(반복 606) — 판정이 인터프리터 설치 레이아웃과 마이너 버전에 묶여 있어 「이 기계에서 초록」이 판정이 옳다는 뜻이 아니다 |

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
