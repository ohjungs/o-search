# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

---

## 2026-08-25 | crawler-core | 계획 1 | 시도1
- 한 일: 초기화(템플릿 7개 배치, 훅 설치) + concept.md 를 계획 6개로 분할(index.md) + plan_crawler-core.md 작성(스텝 7)
- 결과: project.md 명령 절은 "없음"(코드 0줄) — 스텝 1에서 갱신 예정
- 다음: 설계 phase — design_crawler-core.md (스택·모듈 경계)

## 2026-08-25 | crawler-core | 설계 | 시도1
- 한 일: design_crawler-core.md — 대안 3개(stdlib만/의존성 추가/Node) 비교, A 선택. 가정 탐침: 시스템 Python 3.9.6 sqlite3 FTS5 생성 성공
- 결과: 의존성 0 → 설계룰 4절 보류 사안 없음. 계약(시그니처·스키마) 확정
- 다음: 개발 스텝 1 — 스캐폴드 + unittest 러너 확인

## 2026-08-25 야간1 | crawler-core | 개발 1/7 | 시도1
- 한 일: 스캐폴드 — src/websearch/__init__.py, tests/test_smoke.py, .gitignore(data/·reports/), project.md 명령 갱신
- 결과: unittest 1/1 통과. 실패 먼저 확인(네임스페이스 패키지 탓에 1차 시도는 실패를 못 봐 단언 교체)
- 다음: 개발 2/7 robots

## 2026-08-25 야간2 | crawler-core | 개발 2/7 | 시도1
- 한 일: robots.py(RobotsCache) + test_robots.py 5케이스 — 허용/차단/404허용/5xx차단/도메인당 1회 캐시
- 결과: 실패 확인 후 구현, 전체 6/6 통과. 실네트워크 없음(_fetch_robots 주입)
- 다음: 개발 3/7 fetcher

## 2026-08-25 야간3 | crawler-core | 개발 3/7 | 시도1
- 한 일: fetcher.py(fetch→FetchResult) + test_fetcher.py 5케이스 — 성공/비HTML/4xx/타임아웃 3회 포기/재시도 성공
- 결과: 실패 확인 후 구현, 전체 11/11 통과. HTTPError 는 확정 응답이라 재시도 안 함
- 다음: 개발 4/7 store

## 2026-08-25 야간4 | crawler-core | 개발 4/7 | 시도1
- 한 일: store.py(Store: upsert/has/get_html/count) + test_store.py 3케이스 — 저장/갱신 중복 없음/실패기록
- 결과: 실패 확인 후 구현, 전체 14/14 통과. 스키마는 설계 계약대로 pages 단일 테이블
- 다음: 개발 5/7 links

## 2026-08-25 야간5 | crawler-core | 개발 5/7 | 시도1
- 한 일: links.py(extract) + test_links.py 6케이스 — 절대화/fragment/스킴 필터/중복/빈 href/깨진 HTML
- 결과: 실패 확인 후 구현, 전체 20/20 통과. stdlib HTMLParser 로 충분
- 다음: 개발 6/7 frontier

## 2026-08-25 야간6 | crawler-core | 개발 6/7 | 시도1
- 한 일: frontier.py(Frontier: add/next/empty/seconds_until_ready) + test_frontier.py 6케이스 — 중복/재큐 방지/1초 간격/라운드로빈/대기 시간
- 결과: 실패 확인 후 구현, 전체 26/26 통과. 시계 주입으로 sleep 없는 테스트
- 다음: 개발 7/7 crawl 통합

## 2026-08-25 야간7 | crawler-core | 개발 7/7 | 시도1
- 한 일: crawl.py(crawl + CLI main) + test_crawl.py 4케이스 — 시드→링크 추적/robots 미요청/max_pages/실패 미집계
- 결과: 실패 확인 후 구현, 전체 30/30 통과. 개발 phase 완료 → 테스트 phase
- 다음: 테스트 phase (갭 탐색)

## 2026-08-25 야간8 | crawler-core | 테스트 | 시도1
- 한 일: 갭 탐색 6카테고리 — 격리 위반 1건(테스트가 실제 시계 의존, 스위트 4.06s) 수정: crawl 에 now 주입, sleep 목이 가짜 시계를 흘림
- 결과: 30/30 통과 0.004s (PYTHONPATH=src python3 -m unittest discover tests — 전체). 8점 미만 갭 3건 digest 에
- 다음: 리뷰 phase

## 2026-08-25 야간9 | crawler-core | 리뷰 | 시도1
- 한 일: 패스 A 별도 세션(백지, 8건) → 코드 검증 → 자동 6건 수정(TDD 재현 테스트 11개 먼저): store 디렉터리 생성/FetchResult.url(리다이렉트 정본)/스킴 ValueError/charset 존중+폴백/2MB 상한/--max 방어
- 결과: 37/37 통과 0.007s (전체). 보류 2건 digest "판단 필요"로: 쿨다운 공회전(설계 결정), 재실행 스킵 정책(recrawl 소관)
- 다음: e2e phase

## 2026-08-25 야간10 | crawler-core | e2e | 시도1
- 한 일: e2e/crawl_e2e.py 신설(로컬 서버 20p+robots 차단) — CLI 실제 실행 검증. project.md e2e 명령 확정. 계획 아카이브(001)
- 결과: e2e 통과 — 수집 15/15, 차단 요청 0, 최소 간격 1.002s. 품질 4축은 미검증으로 기록(측정 명령 아직 없음)
- 다음: DONE → 다음 계획 indexer (계획 phase)

## 2026-08-25 야간11 | indexer | 계획 | 시도1
- 한 일: plan_indexer.md 작성 — 스텝 4(추출/증분 writer/질의+CLI/e2e). index.md 중복 확인: 없음
- 결과: 설계 필요 판정 (새 모듈+FTS5 스키마+토크나이저 갈림)
- 다음: 설계 phase

## 2026-08-25 야간12 | indexer | 설계 | 시도1
- 한 일: 토크나이저 탐침 — trigram 2글자 질의 불가(실측), unicode61+prefix+질의 재작성 채택. 단독 FTS5·같은 DB. design_indexer.md
- 결과: 컨셉 메모(trigram)와 다른 결정 — 근거 실측 기록. quality-eval 80% 미달 시 재론 조건 명시
- 다음: 개발 1/4 extract

## 2026-08-25 야간13 | indexer | 개발 1/4 | 시도1 (미완)
- 한 일: tests/test_extract.py 5케이스 작성(제목·본문/script 제외/공백 정규화/title 없음/깨진 HTML), 실패 확인
- 결과: 38 중 1 에러(extract 모듈 없음) — TDD 2단계까지. 구현 미착수
- 다음: extract.py 구현부터. 컨텍스트 상한으로 세션 종료

## 2026-08-25 야간14 | indexer | 개발 1/4 | 시도1
- 한 일: src/websearch/extract.py 구현 — stdlib html.parser 재사용(links.py 와 같은 패턴). script/style/noscript 는 깊이 카운터로 스킵, 닫히지 않은 <title> 은 다음 시작 태그에서 종료, 조각을 공백으로 이어 붙인 뒤 split/join 으로 정규화
- 결과: extract 5/5, 전체 42/42 통과 0.007s. 새 의존성 0
- 다음: 개발 2/4 FTS5 증분 색인 writer

## 2026-08-25 야간15 | indexer | 개발 2/4 | 시도1
- 한 일: tests/test_indexer.py 6케이스 먼저 작성·실패 확인 → src/websearch/indexer.py 의 index_pages(db_path) 구현. 설계대로 unicode61+prefix='2 3' 단독 FTS5 docs 테이블, 증분은 url NOT IN (SELECT url FROM docs), html NULL 행 스킵, 없는 DB 는 FileNotFoundError
- 결과: 전체 48/48 통과 0.016s. FTS5 가용 확인(SQLite 3.51). 새 의존성 0
- 다음: 개발 3/4 질의 함수 search() + CLI

## 2026-08-25 야간16 | indexer | 개발 3/4 | 시도1
- 한 일: 테스트 13건 먼저 작성·실패 확인 → search(db_path, query, limit=10) + CLI main() 구현. 질의 재작성은 어절마다 "어절"* (큰따옴표로 FTS5 문법 문자 무력화 — 주입 방지), bm25 정렬, snippet(docs,1,...). 색인 전 DB 는 sqlite_master 확인 후 빈 목록
- 결과: 전체 61/61 통과 0.030s. CLI 실모듈 스모크 — 2문서 색인 → 재실행 0문서(증분) → "김치"(2글자·조사 붙은 어절) 매치 → "python tutorial" 대소문자 무시 매치
- 다음: 테스트 phase (빠뜨린 것 탐색)

## 2026-08-25 야간17 | indexer | 테스트 | 시도1
- 한 일: rules/test.md 3절 6카테고리로 갭 탐색 — 탐침 스크립트로 제목만 매치 / bm25 정렬 / 재크롤 갱신 / pages 없는 DB / 빈 pages 를 실측. 8점 2건(title 검색 가능, bm25 관련도순)을 테스트로 못박음. 단언이 실제로 잡는지 확인: ORDER BY bm25 를 DESC 로 뒤집으니 FAILED, 되돌리니 OK
- 결과: 전체 63/63 통과 0.034s (PYTHONPATH=src python3 -m unittest discover tests — 전체). 보류 2건 digest 로: [8] 증분이 갱신 미반영(스키마 변경 필요 → 무인 모드 보류, recrawl 소관), [6] indexer.main 이 pages 없는 DB 에 트레이스백
- 다음: 리뷰 phase

## 2026-08-25 야간18 | indexer | 리뷰 | 시도1
- 한 일: 백지 패스(별도 컨텍스트, 실측 재현 강제) 7건 전부 80점 이상. 재현 테스트 6건 먼저 작성·실패 확인 후 수정 — ① 인라인 태그 경계가 단어를 쪼갬(Kim<b>chi</b>→"Kim chi", 검색 실패) ② <title> 안 태그가 제목을 자르고 본문 오염 ③ 크롤 콘텐츠의 ANSI/NUL 제어문자가 터미널까지 유출(결과 위조 가능) ④ NUL 이 FTS5 문자열 조기 종료 ⑤ 검색 0건 침묵+exit 0 ⑥ snippet 이 body 열 고정이라 제목 매치 시 질의어 없는 스니펫. ①②는 _INLINE_TAGS 집합 하나로 동시 해결, ③④는 _CONTROL 번역표 하나로 동시 해결
- 결과: 전체 71/71 통과 0.037s. ANSI 유출 od -c 로 재확인 — ESC 사라짐. 보류 1건: [85] 색인이 meta noindex 를 무시(크롤 윤리 축, 계획·설계 어디에도 없는 미판단 항목) → digest 다음 계획 후보. 리뷰가 재발 1건 지적: CLI 트레이스백이 crawl.main 에 이어 indexer.main 에서 2회째 → digest 반복 실패에 기록
- 다음: e2e phase (계획 스텝 4)

## 2026-08-25 야간19 | indexer | e2e | 시도1 → DONE
- 한 일: 앞 관문 먼저 — 전체 71/71 통과, 기존 crawl e2e 회귀 없음(수집 15·차단 0·최소 간격 1.005s). e2e/indexer_e2e.py 신설(로컬 서버 한/영 3페이지 → crawl 수집 → 모듈 실행으로 색인·질의). project.md e2e 명령 확정. 계획 아카이브(002)
- 결과: e2e 통과 — 3문서 색인 / "김치"(2글자+조사+인라인 태그) 매치 / "python" 대소문자 무시 매치 / 재실행 0문서 증분 / 무결과 안내 출력. 품질 4축 중 경량 3(신규 의존성 0)만 통과 기록, 나머지는 미검증(측정 명령 없음, 100만 문서 기준이라 지금 측정 불가)
- 다음: DONE → 다음 계획 search-api (계획 phase)

## 2026-08-25 야간20 | noindex-respect | 계획 | 시도1
- 한 일: plan_noindex-respect.md 작성(스텝 3: 판정 함수/색인 필터·기색인 제거/e2e). 상위 판단으로 search-api 대신 이것을 먼저 — digest 보류 [85], 컨셉 갈림길 1순위가 크롤 윤리. index.md 사양 분할에 3번으로 끼워 넣고 이후 번호 재정렬. 브랜치 loop/noindex-respect
- 결과: 코드 확인 결과 X-Robots-Tag 는 FetchResult 가 헤더를 버려 판단 불가(스키마 변경 필요) → 범위 밖. e2e 5단계는 crawl.py:23 재크롤 스킵 때문에 pages.html 을 직접 갱신하는 것으로 명시
- 다음: 설계 phase (트리거 2개: 대안 갈림 A/B, 공개 인터페이스 추가)

## 2026-08-25 야간21 | noindex-respect | 설계 | 시도1
- 한 일: design_noindex-respect.md — 대안 3개(A 색인 시점 판정 / B 수집 시점 차단+스키마 / C 검색 시점 필터) 비교, A 채택. 가정 4건 탐침: html.parser 가 void·self-closing·대문자·따옴표 없는 속성·깨진 HTML 에서 meta 를 잡는다 / 'robots' 사전 필터 안전 / FTS5 UNINDEXED url 로 DELETE 가능 / SQLite LIKE 대소문자 무시·NULL 미포함
- 결과: 넷 다 참(탐침 커밋 안 함). 스키마 변경 없음 → 야간 보류 사안 없음. 계약(시그니처·판정 규칙·질의 2개) 확정
- 다음: 개발 1/3 extract.is_noindex (TDD)

## 2026-08-25 야간22 | noindex-respect | 개발 1/3 | 시도1
- 한 일: tests/test_extract.py 에 10케이스 먼저 작성·실패 확인 → src/websearch/extract.py 에 _MetaRobotsParser + is_noindex() 구현. 설계 계약대로 name 소문자화 후 robots 만, content 를 쉼표로 쪼갠 토큰에 noindex/none, 사전 필터로 'robots' 없는 문서는 파싱 생략. _TextParser 는 안 건드렸다(반환 형태 유지)
- 결과: 전체 81/81 통과 0.039s (71 → 81). 새 의존성 0. 색인 경로는 아직 미연결
- 다음: 개발 2/3 index_pages 필터·제거

## 2026-08-25 야간23 | noindex-respect | 개발 2/3 | 시도1
- 한 일: tests/test_indexer.py 3케이스 먼저 작성·실패 확인(FAILED 3) → index_pages() 에 삽입 필터(is_noindex 면 continue, 반환값 미집계)와 제거 경로(docs ⋈ pages WHERE p.html LIKE '%robots%' 후보만 파싱해 DELETE FROM docs) 구현. 성능 천장은 ponytail 주석으로 남김
- 결과: 전체 84/84 통과 0.044s. pages 는 읽기만 — 판정 규칙 변경 시 재판정 근거 보존
- 다음: 테스트 phase (갭 탐색)

## 2026-08-25 야간24 | noindex-respect | 테스트 | 시도1
- 한 일: rules/test.md 3절 6카테고리 갭 탐색 — 탐침으로 주석/엔티티 이스케이프 meta, 부분 문자열 noindexing, 빈 content, http-equiv 변형, html NULL 행, pages 에서 사라진 색인 행을 실측. 8점 4건을 테스트로 못박음(test_extract 3, test_indexer 1)
- 결과: 전체 88/88 통과 0.045s. 변이 검사 — is_noindex 를 항상 False 로 뒤집으니 8건 FAILED, 되돌리니 OK. 8점 미만 2건 digest 로: [5] http-equiv 변형 무시, [4] 본문 안 진짜 meta 의 오탐
- 다음: 리뷰 phase

## 2026-08-25 야간25 | noindex-respect | 리뷰 | 시도1
- 한 일: 백지 패스를 별도 세션에 위임(diff 와 소스만 제공) → 4건 전부 80점 이상, 코드에서 재확인 후 재현 테스트 2건 먼저 작성·실패 확인하고 수정 — ① content="noindex nofollow" 공백 구분 미탐(쉼표+공백 둘 다 구분자로) ② 제거가 침묵(색인 전후 문서 수 비교해 "N 문서 색인 제외" 출력, index_pages 반환 계약은 유지) ③ 모듈 독스트링 2개 정정. ④ 사전 필터가 엔티티 인코딩 name 을 놓치는 건 천장으로 주석·digest 기록
- 결과: 전체 90/90 통과 0.047s. 리뷰가 지적한 오탐 0건 — 4건 모두 실재
- 다음: e2e phase (계획 스텝 3/3)

## 2026-08-25 야간26 | noindex-respect | e2e 3/3 | 시도1 → DONE
- 한 일: 앞 관문 먼저 — 전체 90/90 통과, 기존 e2e 2개 회귀 없음(crawl 수집 15·차단 0·간격 1.000s / indexer 3문서). e2e/noindex_e2e.py 신설(로컬 서버 4페이지: 목차·일반·noindex·none, 셋 다 본문에 pyeongsan). project.md e2e 명령 확정, 계획·설계 아카이브(003), digest 보류 [85] 닫음
- 결과: e2e 통과 3.7s — 4수집 중 2문서 색인 / 질의는 /open 만 / pages.html 을 직접 noindex 로 갱신 후 재색인하니 "0 문서 색인 + 1 문서 색인 제외" 출력하고 검색에서 사라짐. 품질 4축 중 경량 3(의존성 0) 통과, 크롤 윤리 축은 이 계획이 닫음
- 다음: DONE → 다음 계획 search-api (계획 phase)

## 2026-08-25 야간27 | search-api | 계획 | 시도1
- 한 일: plan_search-api.md 작성 — 스텝 5(결과 JSON/페이지네이션/신뢰 경계·오류 경로/p95 측정·기준선/e2e). 중복 확인: index.md·digest 에 없음. 브랜치 loop/search-api
- 결과: 설계 필요 판정(트리거 3: 새 모듈, indexer.search 시그니처 변경, sqlite 연결 전략 갈림). digest "반복 실패"의 CLI 진입점 방어를 스텝 3 근거로 명시 — HTTP 핸들러가 세 번째 진입점이다
- 다음: 설계 phase

## 2026-08-25 야간28 | search-api | 설계 | 시도1
- 한 일: design_search-api.md — 연결 전략 3안 비교(요청마다/풀/단일스레드). 탐침 3000문서 색인으로 측정: 연결 open+close 0.04ms, 질의 p50 1.16ms, 연결 재사용과 p95 차 0.05ms
- 결과: A(요청마다 연결) 채택 — 아끼려던 비용이 없었다. 계약 확정(JSON 키·has_next 는 limit+1 로, 검증은 _parse 한 곳, POST 는 스텁 없이 stdlib 501)
- 판단: OFFSET 이 선형 증가(990에서 7.2ms)라 page 상한 100을 **성능이 아니라 자원 고갈 방어**로 넣었다
- 다음: 개발 스텝 1 — GET /search 결과 JSON (TDD)

## 2026-08-25 야간29 | search-api | 개발 1/5 | 시도1
- 한 일: serve.py 신설 — GET /search 가 {query, results:[{url,title,snippet}]} 를 낸다. 테스트 7개 먼저 쓰고 ImportError 로 실패 확인 후 구현
- 결과: 97/97 통과 0.160s. CLI(`python3 -m websearch.serve <db> --port 0`)로 실물 응답까지 눈으로 확인
- 판단: 테스트가 3.6s 로 느려 원인을 봤다 — serve_forever 기본 poll_interval 0.5s 를 shutdown 이 기다린다. 0.01 로 주입해 0.16s
- 다음: 스텝 2 페이지네이션 — indexer.search 에 offset 추가

## 2026-08-25 야간32 | search-api | 개발 2/5 | 시도1
- 한 일: indexer.search 에 offset(기본 0) 덧붙이고 GET /search 에 page 추가. 테스트 8건(offset 1 + 페이지네이션 7) 먼저 쓰고 실패 6건 확인 후 구현. has_next 는 limit=11 로 받아 11번째 유무로 판정 — 개수 질의 안 함
- 결과: 105/105 통과 0.27s. 변이 검사 — limit+1 을 limit 으로 되돌리니 has_next 테스트 FAILED, 되돌리니 OK. 기존 호출부(CLI·테스트 8곳) 무영향
- 판단: 픽스처를 20건 = 딱 2페이지로 잡았다. limit+1 방식이 틀리기 가장 쉬운 곳이 "딱 떨어지는 마지막 페이지"(has_next 가 참으로 새는 지점)라 25건 부분 페이지보다 이쪽이 날이 선다
- 다음: 스텝 3 신뢰 경계 — page 범위·q 길이·404·501, _parse 한 곳에

## 2026-08-25 야간33 | search-api | 개발 3/5 | 시도1
- 한 일: _parse() 한 곳에 page 범위(1~100)·질의 길이(200자) 검증. 테스트 10건 먼저 쓰고 6건 실패 확인 후 구현. 404·POST 501·FTS5 문법/NUL/제어문자 12종 200 은 이미 되고 있던 것을 테스트로 고정
- 결과: 115/115 통과 0.45s. 변이 검사 2건 — MAX_PAGE 100000·길이 검사 무력화 각각 FAILED, 되돌리니 OK
- 판단: isdigit 대신 isdecimal — "²".isdigit() 은 참인데 int() 가 거부해 파이썬 예외 문구가 응답으로 샌다. `?page=` 빈 값은 parse_qs 가 버려 1페이지로 떨어지는데, 폼이 빈 칸을 보내는 모양이고 안전한 쪽이라 거부하지 않고 테스트로 명시했다
- 다음: 스텝 4 p95 측정 스크립트 + project.md 성능 기준선

## 2026-08-25 야간34 | search-api | 개발 4/5 | 시도1
- 한 일: e2e/perf_search.py 신설 — 임시 색인(기본 3000문서)에 --port 0 서버를 띄우고 질의 5종 × 200회 순차 왕복 측정. project.md 품질 기준의 "성능 측정"·"기준선 파일" 을 숫자로 채움
- 결과: 2.1s. p50 1.26ms · p95 6.60ms · 최대 6.90ms (1000 요청). 전체 115/115 회귀 없음. 인자 지정(300문서 20회)도 확인
- 판단: 질의 셋에 page=100(OFFSET 990)을 일부러 넣었다 — p95 를 끌어올리는 게 이것 하나(6.51ms)고 나머지는 1.3ms 이하다. 가장 느린 쪽이 빠진 기준선은 회귀를 못 잡는다. 설계 탐침의 7.2ms 와 같은 값이라 탐침 가정이 실물에서도 참
- 다음: 스텝 5 e2e — 사용자가 하는 그대로(crawl → 색인 → serve → 질의·페이지·오류 경로)
