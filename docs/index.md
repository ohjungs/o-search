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

13. `ua-assertions` — 완료 (**짧은 경로**, 계획서 없음)
    크롤러가 자기 이름을 대는지 재는 단언 3건. 의존: 없음
    (테스트 phase 갭 `[6]` 에서 왔다. UA 는 페이지 요청·robots.txt 요청 **두 곳**에서
    나가는데 tests/ 전체에 단언이 0건이었다. **대는 이름과 robots 를 지킬 때 쓰는
    이름의 일치**까지 잰다 — 갈리면 사이트는 자기 규칙이 우리에게 걸리는지 알 수 없다.
    동작 변경 없음. 변이 3종 확인)

14. `crawl-politeness` — 완료 (plan_history_012 · 설계 design_history_012 · e2e docs/e2e/crawl-politeness/)
    예의 계약이 워커 경계를 못 넘어 새는 구멍 2건을 닫는다. 의존: 12(cooldown-burn)
    (사양 분할에 없던 계획. `digest.md ## 판단 필요` 의 `[high]` 2건을 한 계획으로 묶었다 —
    뿌리와 파일이 겹친다. **둘 다 잘 안 풀렸을 때만 열린다**: 워커가 죽으면 `Crawl-delay: 5`
    가 1.0초로 떨어지고, 연결이 거부되면 재시도 3회가 0.4ms 안에 나갔다. 답은
    **네트워크를 안 타는** `RobotsCache.known_delay()` 와 `fetcher` 의 발신 훅
    `before_send` 였다 — 간격을 알고·재우고·재는 일은 전부 `crawl` 쪽 클로저가 한다.
    A 2.01초 · B 1.00초. 리뷰가 **내 테스트의 거짓 초록 8건**을 꺼냈다 — 가짜 fetch 가
    `**kw` 로 발신 훅을 받고 안 불렀다)

15. `pagination-ui` — 완료 (plan_history_013 · 설계 없음 · e2e docs/e2e/pagination-ui/)
    검색 화면에 이전/다음을 낸다. 의존: 9(search-api) · 13(search-ui)
    (사양 분할에서 왔다. 서버는 진작 2페이지를 줄 수 있었고 `?q=X&page=2` 를 손으로
    치면 나왔다 — **없던 것은 화면에 그려진 길**이다. JSON 경로가 이미 쓰던 수법
    (`limit=PAGE_SIZE + 1` 탐침 한 줄)을 `_page_hits`·`_has_next` **한 벌**로 뽑아
    두 경로가 나눠 쓴다. COUNT 를 안 더하므로 p95 에 얹히는 것이 없고, 총 건수를
    모르니 **번호 목록도 안 그린다** — 이전/다음만이 지금 아는 정보로 정직한 것이다.
    리뷰가 **테스트 15건이 `__main__` 가드 뒤에서 실행되지 않던 것**을 잡았다)

16. `retry-interval` — 완료 (plan_history_014 · 설계 없음 · e2e docs/e2e/retry-interval/)
    재시도도 프런티어가 아는 간격을 바닥으로 쓴다. 의존: 14(crawl-politeness)
    (사양 분할에 없던 계획. `digest.md ## 판단 필요` 의 `[5]` 에서 왔다. **한 서버인데
    두 경로가 다른 값을 썼다** — `robots.txt` 는 스킴별 문서라 `_fetch_one` 이 그것만
    보면 `http` 가 선언한 5초를 모른 채 `https` 재시도를 1초로 냈고, 프런티어는 netloc
    단위로 모아 5초를 알고 있었다. 답은 **바닥값을 제출 시점에 메인 스레드가 읽어
    넘기는 것** — `Frontier._interval` 의 밑줄만 뗐다. 워커는 여전히 `Frontier` 를
    안 만진다(동시화 계약 4). 5.01초 · 대조군 1.00초로 안 샌다. `robots.delay` 를
    스킴 무관으로 바꾸지 않았다 — 없는 선언을 있는 것처럼 읽는 쪽이 사양 위반이다.
    개발 중 **가짜 robots 가 netloc 으로 캐시해 이 버그를 표현조차 못하고 있었다**)

17. `domain-key` — 완료 (plan_history_015 · 설계 없음 · e2e docs/e2e/domain-key/)
    같은 서버는 한 칸이다 — 예의 계약이 세는 단위를 `urls.domain_key` 로 모았다. 의존: 16
    (사양 분할에 없던 계획. `digest.md ## 판단 필요` 의 `[high]` 에서 왔다. 열쇠가 날
    `netloc` 이라 `http://a.test`·`http://A.test`·`http://a.test:80` 이 큐도 `_last_fetch`
    도 `_delays` 도 따로 가졌다 — 2초를 선언한 서버가 **2밀리초 안에** 요청 넷을 받았고
    `robots.txt` 도 표기마다 받았다. 답은 **호스트 소문자화 + 스킴별 기본 포트 제거**를
    한 함수에 모으고 세 호출부(`frontier.add`·`crawl` 제출부·`robots._base`)가 그것만
    쓰는 것. **`.port` 를 안 쓴다** — `:abc`·`:99999` 에 ValueError 를 던져 열쇠를 만들다
    크롤을 죽인다. 백지 리뷰가 **진짜 크래시 1건**을 잡았다: 가드가 `domain_key` 에만
    들어가고 `robots._base` 는 날 `urlsplit` 을 부르고 있었는데, 최악의 자리는 예외가 나는
    곳이 아니라 **잡는 곳**이었다 — `_store_result` 의 `except` 가 복구하려 부른
    `known_delay` 가 두 번째로 던지면 아무도 안 잡는다. 파싱을 던지지 않는 `urls._split`
    한 곳으로 모아 닫았다. **URL 정규화는 안 했다** — 세 표기는 여전히 각각 수집·저장된다)

18. `url-normalize` — 완료 (plan_history_016 · 설계 없음 · e2e docs/e2e/url-normalize/)
    같은 문서는 한 URL 이다 — 수집·저장·색인의 열쇠를 `urls.normalize` 로 모았다. 의존: 17
    (사양 분할에 없던 계획. `digest.md ## 다음 계획 후보` `[5]` 에서 왔다. 017 이 "어느
    서버인가" 를 한 칸으로 모은 뒤에도 `Frontier._seen` 과 `store.pages.url` 은 문자열
    그대로를 열쇠로 써서 같은 문서를 표기 수만큼 받고 저장하고 색인했다. 답은 **RFC 3986
    6.2.2 가 의미를 안 바꾼다고 인정하는 것만**(스킴·호스트 소문자 · 스킴별 기본 포트 제거 ·
    빈 경로 `/` · 퍼센트 3연 hex 대문자)을 **URL 이 태어나는 세 경계**에 거는 것.
    `to_ascii` 는 **안 건드렸다** — "ASCII 는 한 글자도 안 바꾼다" 가 멱등성과 이중 인코딩
    방지를 한 규칙으로 사는 계약이고 회귀 위험이 전부 거기 있다. 끝 슬래시 일반화·
    `index.html`·`www.`·질의 정렬은 동치가 아니라 **안 접는다**. 백지 리뷰가 둘을 잡았다:
    원본 문자열을 `len(netloc)` 으로 자르는데 `urlsplit` 이 탭·CR·LF 를 떼서 한 글자씩 밀려
    **다른 호스트**가 되던 것(`http://a\tcom/p` → `http://acom/m/p`), 그리고 프래그먼트를
    `links.extract` 만 떼고 있어 시드·리다이렉트 최종 URL 이 새던 것 — 열쇠를 정하는 자리는
    하나다. 017 의 e2e 는 018 이 그 축을 접어 **크게 실패했고**(조용한 통과가 아니다)
    **userinfo 축**으로 옮겼다 — `normalize` 는 보존하고 `domain_key` 는 떼는, 살아 있는
    유일한 축이다. **기존 DB 는 안 고친다** — 옛 열쇠 행의 일회성 통합은 마이그레이션이라
    야간 금지고, 이 변경은 **새 DB 에서만 목적을 달성한다**(digest `## 판단 필요`))

19. `normalize-gaps` — 완료 (plan_history_017 · 설계 없음 · e2e docs/e2e/normalize-gaps/)
    018 이 못 접은 두 표기를 닫았다. 의존: 18. (사양 분할에 없던 계획. `digest.md
    ## 판단 필요` 의 `[4]`·`[2]` 에서 왔다 — 018 백지 리뷰가 실측으로 남긴 것.)
    ① **점 세그먼트**(RFC 3986 6.2.2.3): `http://b.com/a/../p` 와 `/p` 가 두 문서였다.
    **절대 href 는 `urljoin` 도 안 접는다**(실측) — 018 이 "상대 링크는 `urljoin` 이
    접는다" 며 미룬 근거의 절반이 틀렸다. ② **`:080`**: `domain_key` 가 문자열 비교라
    `'080' != '80'`. 예의를 세는 칸이라 **간격 계약이 새던 자리**다.
    `_fold_dots` 는 **`posixpath.normpath` 를 안 쓴다** — 저것은 `/a//b`·`/a/b/` 까지
    접어 018 이 명시적으로 거부한 끝 슬래시 일반화를 되살린다. 변이 M4 가 **018 의
    기존 테스트를 죽여** 그것을 독립적으로 확인했다.
    **백지 리뷰가 019 자신의 회귀를 잡았다**: `lstrip("0")` 이 `:0` 을 통째로 먹어
    빈 포트가 되고 빈 포트는 기본 포트라 **요청이 다른 포트로 나갔다**(`or "0"` 로 닫음).
    리뷰어가 RFC 5.2.4 레퍼런스로 세그먼트 전수 3905개 대조 — 불일치 0.
    **기존 DB 는 안 고친다**(마이그레이션은 야간 금지) — 새 DB 에서만 목적을 달성한다.
    남은 틈: `links` 의 `urljoin` 이 RFC 보다 넓게 접어 231/3905 모양이 갈린다(digest `[4]`)

20. `deadline` — 완료 (plan_history_018 · 설계 design_history_018 · e2e docs/e2e/deadline/)
    크롤에 **총 크롤 시간 예산**이 생겼다. 의존: 1. (사양 분할에 없던 계획.
    `digest.md ## 다음 계획 후보` `[4]` 와 `## 판단 필요` `[4]`·`[6]` 셋이 같은
    자리를 가리켰다.) `MAX_DELAY 30` 은 **요청당** 대기만 막아서, `--max 100` 에
    `Crawl-delay: 30` 이면 크롤이 밤을 통째로 쓴다. 이제 `crawl(..., deadline=D)` 와
    CLI `--deadline N` 이 예산을 다하면 **새 요청을 안 던지고 지금까지 저장한 것을
    정상 반환**한다(예외 아님). 기본값 `None` 은 무제한 — **예산을 안 주면 오늘과
    한 글자도 안 다르다**(e2e 15종·단위 393건으로 확인).
    **예산은 간격을 깎지 않고 자른다.** 만료 시 `MAX_DELAY` 만큼 더 자는 것만 막고,
    깨어나 소진 검사로 끝낼 뿐 짧아진 간격으로 요청이 나가지 않는다 — e2e 시나리오
    3이 이걸 지킨다(간격 최소 1.00s).
    **단위 393건이 눈먼 자리를 e2e 가 잡았다**: CLI 가 `deadline=` 을 안 넘기는
    변이(M6)에 단위는 전부 OK 다 — `tests/test_crawl.py` 가 `crawl` 을 목으로
    갈아끼우고 CLI 를 보기 때문. e2e 만 죽는다.
    **미해결(승인 대기)**: 예산 만료 `break` 가 **떠 있는 요청의 결과를 버린다**
    (`docs/patches/deadline-inflight-reap.patch`, critical). executor 는 나갈 때
    어차피 그것을 기다리므로 **시간은 치르고 결과만 버리는** 셈이다. 가짜 시계는
    `sleep` 에서만 흐르고 `sleep` 은 `inflight` 가 빌 때만 해서 **단위는 구조적으로
    도달 못 한다** — e2e 가 `저장 N / 서버 응답 M` 으로 관측만 한다(0~1건, 실시계
    타이밍에 달렸다). 설계 4절이 줍는지 버리는지를 안 정해 승인이 필요하다.
    `--deadline=5` 형태가 조용히 무시되는 것도 보류(`deadline-eq-form.patch`) —
    근본 원인 `_number_flag` 가 `--max`·`--workers` 까지 걸려 설계 결정이다.

21. `indexer-cli-guard` — 완료 (**짧은 경로**, 계획서 없음 · 브랜치 `loop/indexer-cli-guard`)
    `pages` 테이블이 없는 DB(크롤한 적 없거나 남의 DB)를 `python3 -m websearch.indexer`
    에 주면 `sqlite3.OperationalError` 가 그대로 새어 **트레이스백 + rc=1** 이었다.
    `index_pages()` 가 읽기 직전 `sqlite_master` 를 한 번 보고 `NoCrawlDataError` 를
    내고, `main()` 이 `StaleIndexError` 와 같은 관용구로 받아 복구법을 찍고 **rc=2**.
    근거: `digest.md ## 반복 실패` 의 "CLI 가 예상 못 한 입력에 트레이스백을 낸다"(2회).
    **`0` 으로 합치지 않았다** — "크롤 데이터가 없다" 와 "크롤했는데 0건" 은 다른
    상태고, 합치면 DB 경로 오타가 조용한 성공이 된다(대조군 테스트가 고정).
    **digest 의 처방은 과했다**: "CLI 진입점마다 방어를 따로 쓴다" 를 근거로 공통
    방어층을 만들 뻔했는데, 탐침하니 `serve.main`·`crawl.main` 은 이미 막고 있었다 —
    남은 구멍은 한 곳이라 한 곳만 고쳤다(digest `[7]` 관용구의 또 다른 사례).
    단위 393 → **396건 OK** · e2e 15종 rc=0.

색인 규모 단계(10만→100만)는 별도 계획이 아니라 7번(quality-eval) 이후 운영 측정으로 판정.
