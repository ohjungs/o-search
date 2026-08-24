# 계획: indexer — 수집 문서 파싱 → FTS5 색인

- 근거: `docs/specs/concept.md` "기능 1·2" (랭킹 결과·한국어/영어 질의) 의 전제. index.md 분할 2번, 의존 crawler-core(완료)
- 브랜치: `loop/indexer`
- 상태: 진행

## 문제 재진술

crawler-core 가 `pages(url, html, ...)` 에 원문 HTML 을 쌓는다. 검색하려면
HTML 에서 본문 텍스트·제목을 뽑아 FTS5 역색인에 넣어야 한다. 색인은 재실행 시
**증분**이어야 한다 (컨셉 성능 3: 수집→검색 가능 지연 10분 이내의 전제).

기대 결과: 크롤 DB 를 주고 색인 명령을 실행하면 FTS5 테이블이 만들어지고,
질의(MATCH)가 해당 문서를 돌려준다. 다시 실행하면 새 문서만 색인된다.

## 스텝

1. **본문 추출** — 의존: 없음
   - HTML → (title, text). script/style/noscript 내용 제거, 공백 정규화
   - 완료 기준: 제목/본문/script 제외/중첩/깨진 HTML 케이스 테스트 통과
   - 예상 파일: `src/websearch/extract.py`, `tests/test_extract.py`
2. **색인 스키마 + 증분 writer** — 의존: 1
   - FTS5 테이블 생성(토크나이저는 설계에서 확정), `index_pages(db)` — pages 중
     미색인 문서만 추출·삽입, 색인 수 반환
   - 완료 기준: 신규 색인/재실행 증분 0건/HTML 없는 행 스킵 테스트 통과
   - 예상 파일: `src/websearch/indexer.py`, `tests/test_indexer.py`
3. **질의 함수 + CLI** — 의존: 2
   - `search(db, query, limit) -> [(url, title, snippet)]` (bm25 순) + `python3 -m websearch.indexer` CLI
   - 완료 기준: 한국어·영어 질의 매치/무결과/limit 테스트 통과
   - 예상 파일: `src/websearch/indexer.py`(확장), `tests/test_indexer.py`(확장)
4. **e2e** — 의존: 3 (e2e phase 에서 실행)

검색 API 서버·p95 측정은 search-api 계획 소관 — 여기서는 함수·CLI 까지만.

## 하지 않을 것

- HTTP 서버·랭킹 튜닝·스니펫 하이라이트 다듬기 — search-api/search-ui 소관
- 형태소 분석 — 컨셉 "하지 않을 것" (trigram 으로 버틴다)
- pages 스키마 변경 — 색인은 별도 테이블로만

## 6-1. 설계 판단

**설계 필요** — 새 모듈 + 데이터 구조(FTS5 스키마·토크나이저) + 대안 갈림
(external content vs 복사, unicode61 vs trigram). → `phase: 설계`

## e2e 시나리오

1. 로컬 서버(한국어·영어 본문 포함 페이지)를 crawl 로 수집 → `index_pages` 실행
   → 한국어 질의·영어 질의 각각 정답 URL 이 결과에 포함
2. 색인 명령 재실행 → "0 문서 색인" (증분 확인)
