# 계획 목록

<!--
계획 하나당 한 줄. 계획 탐색 때 이것만 읽으면 전체 지형이 보인다.
plan_history_<NNN>.md 를 다 열어볼 필요가 없게 하는 것이 목적이다.

상태: 진행 | 완료 | 보류 | 폐기
-->

| 계획 | 상태 | 브랜치 | 스텝 | e2e | 비고 |
|---|---|---|---|---|---|
| plan_crawler-core | 완료 | loop/crawler-core | 7/7 | 통과 | 설계 있음(001). 리뷰 보류 2건 digest |
| plan_indexer | 완료 | loop/indexer | 4/4 | 통과 | 설계 있음(002). unicode61 채택. 리뷰 보류 1건(meta noindex) digest |
| plan_noindex-respect | 완료 | loop/noindex-respect | 3/3 | 통과 | 설계 있음(003). digest 보류 [85] 닫음. 리뷰 4건 중 3건 수정 |
| plan_search-api | 완료 | loop/search-api | 5/5 | 통과 | 설계 있음(004). 성능 축을 열었다 — p95 기준선 |
| plan_crawl-delay | 완료 | loop/crawl-delay | 4/4 | 통과 | 설계 있음(005). robots Crawl-delay 존중. 리뷰 10건 중 6건 수정 |
| plan_quality-eval | 진행 | loop/quality-eval | 4/4 | 미정 | 설계 필요. concept 기능 2 정답 포함률 80% 를 처음 잰다 |

## 사양 분할 (docs/specs/concept.md → 계획 순서)

의존은 왼쪽이 먼저. 한 번에 한 계획만 활성.

1. `crawler-core` — 완료 (plan_history_001)
2. `indexer` — 완료 (plan_history_002)
3. `noindex-respect` — 완료 (plan_history_003)
   (사양 분할에 없던 계획. 컨셉 갈림길 1순위가 크롤 윤리라 search-api 앞에 끼워 넣었다)
4. `search-api` — 완료 (plan_history_004)
   `GET /search?q=&page=` JSON·10건 단위. **성능 축을 열었다** — `e2e/perf_search.py`,
   기준선 p95 6.71ms(3000문서)가 `project.md` 에 있다
5. `crawl-delay` — 완료 (plan_history_005)
   robots 의 `Crawl-delay` 를 도메인 간격에 반영. 1초 하한은 유지, 30초 초과는 도메인 포기.
   (사양 분할에 없던 계획. digest 의 "윤리 축이라 우선순위 높음" 메모에서 왔다)
6. `search-ui` — 검색 홈 + 결과 페이지 (LCP·번들·접근성 기준). 의존: 4
7. `quality-eval` — 질의 40개 테스트 셋 + 정답 포함률 80% 측정. 의존: 4
8. `recrawl` — 30일 재방문·갱신·삭제 반영. 의존: 2

색인 규모 단계(10만→100만)는 별도 계획이 아니라 7번(quality-eval) 이후 운영 측정으로 판정.
