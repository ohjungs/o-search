# e2e: 계획 115 `nav-inline-passage` — **통과 (단, 실물 1건의 회귀를 함께 재연했다)**

**수단**: 이 계획의 「사용자」는 `GET /passages` 를 부르는 쪽이다. 그래서 e2e 는 **제품이
쓰는 길 그대로**(`Store.upsert` → `indexer.index_pages` → `indexer.passages`) 돌렸고,
되돌리기는 **추적 트리 복사본**에서만 했다 — `git archive main | tar -x -C $(mktemp -d)`.
워킹트리 무접촉(`git status --porcelain` 0줄로 확인).

**시나리오 ①②는 한 스크립트를 두 트리에 먹여** 돌렸다(배선이 양쪽에서 같다는 것이
비교의 전제라 스크립트를 가르지 않았다):

```bash
# 옛 판(main) 과 새 판(HEAD) 을 같은 코퍼스·같은 질의로
OLD=$(mktemp -d); git archive main | tar -x -C "$OLD"
python3 docs/e2e/nav-inline-passage/scenario.py src          # 새 판
python3 docs/e2e/nav-inline-passage/scenario.py "$OLD/src"   # 옛 판
# 리뷰 115 가 쓴 숨김 경계 census (방아쇠·결함을 실물에서 센다)
python3 docs/e2e/nav-inline-passage/hidden_census.py 1600
```

**코퍼스는 합성 1 + 실물 2**다. 합성만 재면 테스트 phase 가 YELLOW 를 낸 그 간극
(「합성에서는 고치고 실물에서는 안 움직인다」)을 **또 재게 된다** — 그래서 실물 크롤
DB(`data/crawl.db` · 읽기 전용)에서 706 이 회귀로 지목한 두 장을 그대로 떠 넣었다.

**앞 관문** (e2e 전에 통과시킨 것 · `e2e.md` 1절):

- 전수 **875 OK rc=0** (래퍼 판정 줄 · 20.8s) — README 단위 수 가드 `875` 와 일치
- **린트·타입체크는 이 저장소에 없다 — 「검증되지 않았다」로 적는다**(통과가 아니다)
- **CI 없음** — `.github/workflows` 가 없다(`ls` 로 확인)
- `passage_eval` **100%(398/398)** · p95 **1.61ms**(예산 500ms 의 0.3%) ·
  `quality_eval` **ko 20/20 · en 19/20**(미검출 1 은 알려진 `loaf` 천장) ·
  `design_check` **4축 전부 통과 rc=0**
- **성능 셋을 이번엔 전부 돌렸다** — 제품 `src/` 가 바뀌었기 때문이다(계획 114 는 0줄이라
  안 돌렸다): `perf_search` p95 **8.88ms**(예산 300ms 의 3.0%) · `perf_crawl` **3시나리오
  통과**(도메인 12개 최소 간격 1.000s) · `perf_memory` 100만 문서 외삽 **84.7MB**(예산 2GB 의 4.1%)

## ① 실물 모양 재연 — **설계 축 통과 · 실물 1건 회귀**

| 질의 | 문서 | 옛 판(main) | 새 판(HEAD) | 판정 |
|---|---|---|---|---|
| `김치찌개 된장찌개` | 합성 위키 | pos 0 `대문김치찌개 된장찌개김치찌개 만들기` (**내비 연접**) | pos 6 `김치찌개는 잘 익은 배추김치를 … 대표적인 찌개다.` (**본문 `p`**) | **통과** |
| `wikimedia foundation` | es.wikipedia `Fundación_Wikimedia` | pos 296 (참조 URL 덩이) | **동일** | 무변화 |
| `lrzsz zmodem` | ohse.de `lrzsz.html` | pos 3 `lrzsz is a unix communication package providing the XMODEM, YMODEM ZMODEM…` | pos 4 **`ZMODEM file transfer protocols. lrzsz is a heavily rehacked…`** | **회귀** |

- **계획이 적은 조건은 충족됐다** — 「본문 문단이 나오고 내비 연접이 안 나온다 · 되돌리면
  다시 내비가 나온다」가 합성 위키에서 **양방향으로** 확인된다(옛 트리가 곧 되돌린 판이다).
- **그리고 706 이 지목한 회귀가 e2e 에서 재연됐다.** `ohse.de` 는 **산문 속 인접 링크
  분할**(리뷰 115 천장 ⓐ)이다 — 한 문단 안에 링크 둘이 붙어 있어 경계가 서고, 근거가
  **문장 중간부터 시작하는 조각**으로 바뀐다. 시나리오를 낮추지 않고 그대로 적는다
  (`e2e.md` 7절). `es.wikipedia` 쪽은 **질의에 따라 다르다** — 706 은 문서 제목으로
  물어 회귀를 봤고, 여기 두 낱말 질의로는 양쪽이 같다.
- 심각도 **medium**(기능 — 근거 품질 저하 · 우회 가능: 질의를 바꾸면 다른 문단이 나온다).
  **이것이 병합 결정을 사람에게 남기는 이유**고, 닫는 조건은 `digest` 후보 ⓐ 로 등재했다.

## ② 색인이 안 바뀐 것을 실측 — **통과**

세 문서 전부 `docs.body` **sha256 바이트 동일**(옛 판 ↔ 새 판 `diff` 빈손).
**재색인이 없다** — 이 계획이 승인 게이트(스키마·마이그레이션) 밖인 근거가 이것이다.
단위 쪽 같은 계약은 `test_the_link_boundary_never_reaches_the_index_path` 가 든다.

## ③ e2e 18종 — **18/18 rc=0**

`crawl_e2e` `indexer_e2e` `noindex_e2e` `search_api_e2e` `crawl_delay_e2e` `non_ascii_e2e`
`hidden_passage_e2e` `design_check` `tokenizer_e2e` `domain_key_e2e` `deadline_e2e`
`interrupt_e2e` `indexer_interrupt_e2e` `crawl_politeness_e2e` `pagination_ui_e2e`
`recrawl_e2e` `retry_interval_e2e` `url_normalize_e2e` — **종료 2(측정 불능)를 낸 것 0종.**
`hidden_passage_e2e` 가 리뷰 115 의 숨김 가드와 같은 축을 떠받치는데 조용하다 — 그 자가
«숨은 글자가 블록에 담기나»만 보고 «숨은 태그가 보이는 블록을 끊나»는 안 보기 때문이다
(그 구멍을 단위 `test_links_hidden_from_people_do_not_cut_the_visible_paragraph` 가 메웠다).

## 만든 파일

- `docs/e2e/nav-inline-passage/scenario.py` — ①② 를 두 트리에 먹이는 스크립트
- `docs/e2e/nav-inline-passage/hidden_census.py` — 리뷰 115 의 숨김 경계 census
  (배선 3단 검사 → 실물 1,600문서. 방아쇠 **688문서·4,130회** · 블록 변경 **0건**)
- `e2e/` 에는 **새 파일 0개** — 18종 명부와 `project.md` 가 그대로다(전수 안의 명부 가드).
