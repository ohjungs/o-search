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
| plan_quality-eval | 완료 | loop/quality-eval | 4/4 | 통과(3은 반증) | 설계 있음(006). ko 85% · en 90%. **이 코퍼스는 랭킹을 못 잰다**(recall@1 == recall@10) |
| plan_non-ascii-url | 완료 | loop/non-ascii-url | 4/4 | 통과 | 설계 있음(007). 한글 URL 이 `UnicodeEncodeError` 로 크롤 루프를 죽이던 것을 닫음 |
| plan_crawl-throughput | 완료 | loop/crawl-throughput | 3/3 | 통과(4/4) | 설계 있음(008). **0.5/s → 10.25/s**(기준 5.0). 잠긴 DB 크래시도 닫음. 리뷰 패스 A 5건 중 3건 반영·1건 보류(쿨다운 태우기) |
| plan_tokenizer | 완료 | loop/tokenizer | 3/3 | 통과(6/6) | 설계 있음(010). **미검출 5 → 1**(ko 20/20 · en 19/20). 한글 2-gram 을 제목·본문 **열로 나눠** 넣고 질의는 **어절마다** 분기. 오탐 13.8→14.0 으로 안 늘었다. 리뷰 보류였던 `porter` 는 **양쪽을 다시 재서 유지로 닫음**(굴절 96.3% vs 1.0%, 접두 손실 11.2%가 그 값) |
| plan_search-ui | 완료 | loop/search-ui | 2/2 | 통과(5/5) | 설계 있음(009). **브라우저로 쓸 수 있는 제품이 처음 생겼다.** 디자인 4축 측정 명령(`e2e/design_check.py`)을 만들어 열었다 — JS 0 B · 최저 대비 4.87:1. 리뷰가 **검사기의 눈먼 자리 4곳**을 찾아 닫음(초록불이 근거 없이 켜져 있었다) |

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
6. `search-ui` — 완료 (plan_history_009)
   `GET /` 검색 홈 + 결과 페이지. `/search` JSON 은 무손상. **디자인 축을 열었다** —
   `e2e/design_check.py` 가 컨셉 4축을 실제 응답 바이트로 판정한다(종료 0·1·2).
   대비는 검사기가 색값을 들지 않고 응답 CSS 에서 매번 읽어 드리프트가 구조적으로 불가능하다
7. `quality-eval` — 완료 (plan_history_006)
   질의 40개 fixture + `e2e/quality_eval.py`. ko 17/20 · en 18/20 으로 기능 2 합격.
   **한계가 실측으로 드러났다**: 정답만 제목에 질의어를 갖는 구조라 매치되면 1위,
   아니면 미검출이다 — 상위 10 이라는 창이 아무 판정도 가르지 않는다. 랭킹 축을 재려면
   정답과 방해 문서가 같은 질의어를 갖는 fixture 가 따로 필요하다(digest 후보)
8. `recrawl` — 30일 재방문·갱신·삭제 반영. 의존: 2

9. `non-ascii-url` — 완료 (plan_history_007)
   비ASCII URL 을 퍼센트/IDNA 로 정규화해 한글 경로를 크롤할 수 있게. 의존: 1
   (사양 분할에 없던 계획. 사용자 지시 + 로컬 재현. 한국어가 1급인 저장소에서
   한국어 위키백과 URL 이 크롤 루프를 통째로 죽인다)

10. `crawl-throughput` — 완료 (plan_history_008)
    네트워크만 스레드풀로 동시화해 크롤 처리량을 올린다. 의존: 1
    (사양 분할에 없던 계획. 사용자가 실제 웹에서 잰 초당 0.5문서와 `concept.md:44`
    의 초당 5문서 사이 10배 격차. 같은 실측에서 1,700문서째 `database is locked`
    크래시도 함께 나왔다 — 둘 다 이 계획에서 닫았다)

11. `tokenizer` — 완료 (plan_history_010)
    한글 문자 2-gram 전용 열 둘(`title_ng`·`body_ng`) + `porter`. 의존: 7(quality-eval)
    (사양 분할에 없던 계획. `quality-eval` 이 실측으로 못박은 미검출 5건이 **랭킹이 아니라
    매치 문제**였다 — 복합어 뒷부분·띄어쓰기 변형·영어 굴절. `trigram` 은 한국어 질의
    20개 중 10개가 2자라 실측으로 먼저 버렸다(35/40 → 27/40))

12. `cooldown-burn` — 완료 (plan_history_011 · 설계 design_history_011 · e2e docs/e2e/cooldown-burn/)
    요청도 안 보내고 태우는 도메인 쿨다운을 회수한다. 의존: 10(crawl-throughput)
    (사양 분할에 없던 계획. `digest.md` 의 8일 묵은 `[high]` 를 재검토해 열었다.
    **robots 가 뭔가를 막는 사이트에서 실제 처리량이 4.48/s 로 `concept.md:44` 의
    초당 5문서를 밑돌고 있었다** — 재는 눈이 없어서 기준선 10.25/s 가 그것을 가렸다.
    팝이 아니라 실제 발신에만 간격 시계를 걸어 **10.29/s**, 간격 1.004s 는 그대로.
    digest 가 적어 둔 처방은 실측 0을 회수해 **틀렸음을 기록으로 남겼다**)

색인 규모 단계(10만→100만)는 별도 계획이 아니라 7번(quality-eval) 이후 운영 측정으로 판정.
