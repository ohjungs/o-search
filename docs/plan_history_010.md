# 계획: tokenizer — 한국어 복합어·띄어쓰기와 영어 굴절을 매치시킨다

슬러그 `tokenizer` · 브랜치 `loop/tokenizer` (기점 `f8d921b`, `loop/search-ui`)

## 문제

`e2e/quality_eval.py` 가 재는 recall@10 이 한국어 17/20 · 영어 18/20 이다.
합격선(`docs/specs/concept.md:22-23` 기능 2, 80%)은 넘었지만 **미검출 5건이 전부
같은 원인**이고, `docs/e2e/quality-eval/result.md` 가 그 원인을 실측으로 못박아 뒀다 —
**랭킹 문제가 아니라 매치 문제**다. 5건 모두 순위 밖으로 밀린 것이 아니라 매치가 0이다.

| 질의 | 정답 문서의 표기 | 왜 안 되나 |
|---|---|---|
| `보관법` | 제목 `김치찌개보관법 …` | `unicode61` 은 복합어를 한 토큰으로 본다. 접두 매치라 **뒷부분**에 못 닿는다 |
| `일출봉` | 제목 `성산일출봉 …` | 같음 |
| `올레길` | 제목 `올레 길 7코스` | 띄어쓰기 변형. 토큰이 `올레` + `길` 로 갈린다 |
| `tuples` | 본문 `a tuple cannot …` | 영어 굴절. `tuple` ≠ `tuples` |
| `loaf` | 제목 `… sourdough loaves` | 영어 **불규칙** 복수 (f→ves) |

## 목표

미검출 5건 중 **4건**을 매치시킨다 — 한국어 3건 + `tuples`.
`loaf`↔`loaves` 는 **하지 않는다** (아래 "하지 않을 것" 참조).

## 기대 결과 (계획 시점의 실측 근거)

탐침을 `scratchpad` 에서 돌려 확인했다. 저장소에는 아무것도 남기지 않았다.

```
A 기준선 unicode61            recall@10 35/40   (ko 17/20 · en 18/20)
B porter unicode61            recall@10 36/40   tuples 만 붙는다
C trigram                     recall@10 27/40   ← 더 나빠진다. 아래 참조
E porter + 한글 bigram 열      recall@10 39/40   (ko 20/20 · en 19/20)
```

**C 를 여기서 버린 근거가 이 계획의 핵심이다.** `trigram` 은 3자 미만 질의에서
토큰을 하나도 만들지 못한다. 그런데 fixture 의 **한국어 질의 20개 중 10개가 2자**다
(`국물` `참치` `두부` `맛집` `냄비` `시간` `숙소` `예산` `날씨` `카페`).
전부 매치 0이 되어 27/40 으로 떨어진다 — 고치려던 것보다 큰 구멍이 뚫린다.

## 스텝

### 스텝 1 — 색인 스키마 드리프트를 감지해 `docs` 를 재구축한다
- 의존: 없음
- 문제: `indexer.SCHEMA` 는 `CREATE VIRTUAL TABLE **IF NOT EXISTS** docs` 다.
  스텝 2 에서 열과 tokenize 를 바꿔도 **이미 색인된 DB 는 옛 스키마 그대로 남는다.**
  그 상태로 스텝 2 의 질의를 던지면 `no such column: title_ng` 로 터진다.
  스텝 2 를 먼저 하면 이 구멍이 열린 채로 커밋된다 — 그래서 **이것이 스텝 1** 이다.
- 할 일: `sqlite_master.sql` 을 `SCHEMA` 와 대조한다. 다르면 `DROP TABLE docs` 후
  재생성 → 기존 증분 경로가 `pages` 에서 전량 재색인한다.
  `docs` 는 `pages` 에서 파생된 색인이므로 재구축에 원본 손실이 없다.
- 건드릴 파일: `src/websearch/indexer.py` · `tests/test_indexer.py`
- 완료 기준: 옛 정의(`fts5(title, body, url UNINDEXED, tokenize='unicode61')`)로
  만든 `docs` 가 있는 DB 에 `index_pages()` 를 돌리면
  ① `sqlite_master.sql` 이 `SCHEMA` 와 같아지고 ② 문서 수가 재색인 전과 같고
  ③ 검색이 된다. **`pages` 행 수는 변하지 않는다**(긍정 짝 단언).
  드리프트가 없으면 재구축하지 않는다 — 재색인 수 0 으로 확인한다.

### 스텝 2 — `porter` + 한글 bigram 열로 매치를 넓힌다
- 의존: 1 (드리프트 재구축 경로가 있어야 스키마를 바꿀 수 있다)
- 할 일: `SCHEMA` 에 `title_ng` · `body_ng` 열을 더하고 `tokenize='porter unicode61'`.
  `index_pages` 가 색인할 때 한글 bigram 을 채우고, `_fts_query` 가 **질의가 전부
  한글일 때만** bigram 구절 분기를 `OR` 로 붙인다. 설계는 `docs/design_tokenizer.md`.
- 건드릴 파일: `src/websearch/indexer.py` · `tests/test_indexer.py`
- 완료 기준: `e2e/quality_eval.py` 가 **한국어 20/20 · 영어 19/20**, 종료 0.
  `보관법` `일출봉` `올레길` `tuples` 4건이 미검출 목록에서 사라진다.
  기존 235 테스트 전부 통과 — 특히 `test_all_terms_required`(AND 계약)와
  `test_snippet_comes_from_matching_column`(스니펫 계약)이 깨지지 않는다.

### 스텝 3 — 오탐과 성능 회귀를 실제로 잰다
- 의존: 2
- 문제: `quality_eval.py` 는 **정답이 들어왔는가**만 센다. 매치를 넓히는 변경은
  정의상 **오탐을 늘릴 수 있는데 그것을 재는 수단이 저장소에 없다.**
  "정답 4건 더 찾았다"만 보고 닫으면 무엇을 잃었는지 모른 채 닫는 것이다.
- 할 일: `quality_eval.py` 가 질의당 매치 수 요약(평균·최대)을 함께 출력한다.
  기준선(평균 13.8 · 최대 28)과 대조해 `project.md` 에 적는다.
  `e2e/perf_search.py` 와 `e2e/perf_crawl.py` 를 돌려 p50·p95·처리량을 기준선과 대조한다.
- 건드릴 파일: `e2e/quality_eval.py` · `docs/project.md`
- 완료 기준: ① 평균 매치 수 증가가 **+1건 이내**(기준선 13.8) ② `perf_search.py`
  p95 가 기준선 6.71ms 의 **2배 이내** ③ `perf_crawl.py` 처리량 5.0/s 이상 유지.
  셋 다 숫자로 `docs/e2e/tokenizer/result.md` 에 적는다.

## 하지 않을 것

- **`loaf` ↔ `loaves`** — 영어 불규칙 복수다. `porter` 가 `loaves`→`loav`,
  `loaf`→`loaf` 로 갈라 놓는다(탐침 실측). 고치려면 불규칙 변화 예외 목록이
  필요하고, 그건 사전을 저장소에 들이는 일이다. **영어 19/20 로 닫고 digest 후보로 남긴다**
- **랭킹 개선** — 이 계획은 매치 축이다. `docs/e2e/quality-eval/result.md` 가
  "bm25 정렬은 한 번도 시험되지 않았다"고 적어 뒀지만 그건 fixture 를 고쳐야 재는 것이고,
  코퍼스·질의 셋은 **동결**이다
- **`recrawl`** (`fetched_at` 스키마 변경) · **`X-Robots-Tag`** — 승인 대기 항목
- **`pagination-ui`** — 별도 계획
- **의존성 추가** — 형태소 분석기(mecab·kiwi 등)를 넣지 않는다. `concept.md` 경량 3
- **`scratchpad/live.db` · `serve.db`** — 사람이 쓰는 DB. 열지 않는다

## e2e 시나리오 (계획 시점 확정)

1. **한국어 복합어 뒷부분** — `보관법` 으로 검색하면 `김치찌개보관법` 문서가 결과에 있다
2. **띄어쓰기 변형** — `올레길` 로 검색하면 `올레 길 7코스` 문서가 결과에 있다.
   반대로 `올레 길` 로 검색해도 같은 문서가 나온다
3. **영어 굴절** — `tuples` 로 검색하면 `tuple` 만 쓴 문서가 결과에 있다
4. **스니펫이 사람이 읽을 수 있다** — 위 1·2 의 결과 화면 스니펫에 bigram
   나열(`김치 치찌 찌개`)이 **없다**. 본문/제목 원문이 나온다 (긍정 짝)
5. **AND 계약 유지** — `김치 python` 처럼 한글과 영어가 섞인 두 어절 질의는
   두 어절을 **모두** 가진 문서만 낸다
6. **옛 색인 자동 복구** — 옛 스키마로 색인된 DB 로 서버를 띄우고 `index_pages()` 를
   돌리면 재색인되어 1~3 이 동작한다
