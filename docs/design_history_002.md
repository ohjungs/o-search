# 설계: indexer — FTS5 스키마·토크나이저

## 결정 — unicode61 + prefix 색인 + 질의 접두 재작성, 단독 FTS5 테이블, 같은 DB 파일

## 토크나이저 — 탐침 실측 (2026-08-25, SQLite 3.51)

| | trigram | unicode61 + prefix='2 3' + 질의에 `*` |
|---|---|---|
| 2글자 질의(김치, 날씨) | **실패 — 토큰이 안 나옴** | 통과 (`김치*` → "김치를" 매치) |
| 조사 붙은 어절 | 통과 (부분 문자열) | 통과 (접두) |
| 어절 중간 부분어(찌개→김치찌개) | 통과 | 실패 |
| 영어 대소문자 | 통과 | 통과 |

**선택: unicode61.** 한국어 2글자 질의는 흔하고(치명), 어절 중간 부분어 미스는 상대적으로
드물다. 컨셉 메모("trigram 으로 버틴다")와 다른 결정 — **탐침에서 trigram 이 2글자
질의를 아예 못 하는 것이 실측**됐고, 갈림길 우선순위 "검색 품질" 이 이긴다.
quality-eval 계획의 40질의 측정에서 정답 포함률 80% 미달이면 재론 (혼합 색인·형태소).

## 스키마 — 단독 FTS5, crawl.db 안에

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS docs
USING fts5(title, body, url UNINDEXED, tokenize='unicode61', prefix='2 3')
```

- external content 를 버린 이유: 원본(pages.html)은 HTML 이라 그대로 못 쓰고, 추출
  텍스트를 어차피 저장해야 snippet 이 된다. 트리거·동기화 없는 단독 테이블이 최소
- 같은 DB 파일: 컨셉 경량 축(단일 머신·파일 하나). 분리는 실측 필요가 생기면

## 계약

- `extract.extract_text(html) -> (title, text)` — script/style/noscript 제거, 공백 정규화, title 없으면 ""
- `indexer.index_pages(db_path) -> int` — pages 중 html 있는 미색인 행만 추출·삽입(증분)
- `indexer.search(db_path, query, limit=10) -> [(url, title, snippet)]` — bm25 순.
  질의 재작성: 어절마다 `"어절"*` (접두), FTS5 특수문자는 따옴표로 무력화
- CLI `python3 -m websearch.indexer <db> [--query Q]` — 질의 없으면 색인 실행
- 증분 판정: `url NOT IN (SELECT url FROM docs)` — ponytail: 전표 스캔, 10만 문서에서 느려지면 색인 상태 컬럼으로

## 되돌리기 — 커밋 revert. docs 테이블은 DROP 하면 끝 (pages 는 안 건드림)

## 범위 밖 — 랭킹 가중치(title 부스트), 스니펫 하이라이트 다듬기, 삭제 문서 색인 제거(recrawl 소관)
