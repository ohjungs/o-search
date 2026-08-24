# 아카이브 요약

<!--
history_current.md 가 상한을 넘어 밀려날 때, 밀려나는 내용을 1~2줄로 압축해 여기 남긴다.
원본은 history_<NNN>.md 에 그대로 있다.

이 파일은 평소 읽지 않는다. 계획 탐색(discover.md) 때만 읽는다.
그래서 "다음에 뭘 해야 하는지 판단하는 데 필요한 것"만 남긴다:
  - 무엇을 완료했나 (같은 걸 또 하지 않기 위해)
  - 무엇이 보류됐나 (승인 받으면 재개할 것)
  - 반복해서 터진 문제 (근본 원인이 남아있다는 신호)

상한 200줄. 넘으면 오래된 완료 항목부터 지운다. 보류·반복실패는 남긴다.
-->

## 완료

<!-- - 2026-08-04~08 | plan_auth | 토큰 검증·만료 처리. 재시도 잦았음 — JWT 라이브러리 버전 이슈 -->
- 2026-08-25 | plan_indexer (002) | 본문 추출(stdlib html.parser) + FTS5 unicode61 증분 색인 + bm25 질의·CLI. e2e 통과. 재시도 0·RED 0
- 2026-08-25 | plan_noindex-respect (003) | meta robots noindex·none 문서를 색인 제외 + 기색인 문서 제거. 보류 [85] 닫음. e2e 통과. 재시도 0·RED 0

## 보류 (승인 대기)

<!-- - 2026-08-09 | plan_db 스텝2 | 마이그레이션 필요 → 무인 모드가 보류 -->

## 반복 실패

<!-- 같은 원인으로 2회 이상 막힌 것. 근본 원인이 안 고쳐졌다는 뜻이다. -->
- **CLI 가 예상 못 한 입력에 트레이스백을 낸다** — 2회. crawler-core 리뷰(bc98bc8)에서 crawl.main 을 고쳤는데 indexer.main 에서 같은 부류가 다시 나왔다(pages 없는 DB). 근본 원인은 "CLI 진입점마다 방어를 따로 쓴다" — 다음에 CLI 를 또 만들면 세 번째다

## 다음 계획 후보

<!--
리뷰·e2e 가 발견했지만 그 계획의 "하지 않을 것" 범위라 미룬 것.
근거가 이미 있으므로 계획 탐색 5순위로 바로 쓸 수 있다. (discover.md)
보류(승인 대기)와 다르다 — 이건 막힌 게 아니라 미룬 것이다.
-->

## 다음 계획 후보 (테스트 phase 갭, 8점 미만)
- [6] fetcher 가 UA 헤더를 실제로 보내는지 단언 없음
- [5] crawl: 이미 store 에 있는 URL 스킵 경로 무테스트
- [4] crawl.main CLI 인자 파싱 무테스트
- [6] indexer.main 이 pages 테이블 없는 DB 를 받으면 sqlite3.OperationalError 트레이스백. FileNotFoundError 만 잡고 있다 (crawl.main CLI 방어와 같은 부류)
- [높음·설계 범위 밖 메모] robots crawl-delay 존중 — 윤리 축이라 우선순위 높음

- [5] `<meta http-equiv="X-Robots-Tag" content="noindex">` 변형은 무시한다 (2026-08-25 noindex-respect 테스트 phase 탐침으로 확인). 표준은 HTTP 헤더이고 http-equiv 변형은 주요 검색엔진도 지원하지 않는다. X-Robots-Tag 헤더 계획(스키마 expand)을 열 때 함께 판단
- [4] `is_noindex` 의 `'robots'` 사전 필터와 제거 경로의 `LIKE '%robots%'` 는 **name 을 HTML 엔티티로 인코딩한 meta**(`&#114;obots`)를 놓친다 (2026-08-25 리뷰 지적, 실측 확인). 파서 자체는 엔티티를 풀어 지시를 본다 — 필터만 빼면 잡힌다. 실물에서 보이면 그때 뺀다
- [4] 본문에 들어 있는 진짜 `<meta name="robots" content="noindex">` 도 페이지 전체를 색인에서 뺀다 — 사용자 콘텐츠(포럼 글 등)가 호스트 페이지를 통째로 빼는 오탐이 가능하다. head 로 제한하면 막히지만 깨진 HTML 에서 head 경계가 불확실해 지금은 안전한 쪽(색인 안 함)으로 둔다
- [5] `serve.main` 인자 처리(`--port` 값 없음·비숫자, db 인자 개수)에 단위 테스트 0 — `e2e/search_api_e2e.py` 가 정상 경로만 덮는다. `crawl.main` CLI 무테스트와 같은 부류 (2026-08-25 search-api 테스트 phase)

## 판단 필요 (리뷰 보류 — 승인 필요 판정)
- [medium] frontier: robots 차단·기수집 URL 이 팝 시점에 도메인 쿨다운을 소모 — 공회전. 수정은 프런티어 계약 변경(팝/기록 분리 또는 add 시점 필터)이라 설계 결정
- [8] indexer 증분(`url NOT IN docs`)이 **갱신을 반영하지 않는다.** 탐침 실측(2026-08-25 테스트 phase): 같은 url 을 재크롤해 pages.html 을 바꾼 뒤 index_pages → 0건, 옛 본문이 계속 검색되고 새 본문은 안 나옴. 컨셉 기능 5(재크롤 30일 갱신 반영)에 걸린다. 고치려면 docs 에 fetched_at 을 두고 비교·재삽입 = **스키마 변경이라 무인 모드가 보류**. 위 store.has 항목과 같은 recrawl 계획 소관
- [high] store.has 가 상태 불문 스킵: 같은 DB 로 재실행하면 시드부터 스킵돼 0으로 끝남. 재크롤 정책(성공만 스킵/TTL/링크 재추출)은 recrawl 계획 소관 — 앞당길지 판단 필요
