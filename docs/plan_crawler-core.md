# 계획: crawler-core — 정적 HTML 크롤러

- 근거: 사용자 지시 + `docs/specs/concept.md` "기능 3" (시드에서 프런티어 확장, robots 준수) · "기능 4" (색인 규모 1단계 10만 문서의 전제)
- 브랜치: `loop/crawler-core`
- 상태: 진행

## 문제 재진술

지금 저장소에는 코드가 한 줄도 없다. 검색엔진 파이프라인(크롤 → 색인 → 검색 → UI)의
첫 노드인 크롤러를 만든다. 시드 URL 목록에서 출발해 정적 HTML 을 수집하고, 링크를
추출해 프런티어를 넓히며, 수집물을 SQLite 에 저장한다. robots.txt 준수와 도메인당
요청 간격 1초는 컨셉상 어길 수 없는 전제다.

기대 결과: 시드 몇 개를 주고 실행하면 사람 개입 없이 N 페이지를 수집해 DB 에 쌓이고,
robots 가 막은 URL 은 요청조차 하지 않으며, 같은 도메인에 1초 안에 두 번 요청하지 않는다.

가정(명시): 언어·프로젝트 구조는 설계 phase 에서 확정한다 (아래 6-1절). 저장소는
컨셉이 SQLite 로 고정했다. 아래 예상 파일명은 Python 기준 초안이며 설계가 갱신할 수 있다.

## 스텝

1. **프로젝트 스캐폴드** — 의존: 없음
   - 패키지 구조·테스트 러너 확정, 빈 테스트 1개가 실제로 돈다
   - 완료 기준: 테스트 명령 1회 실행 성공, `docs/project.md` 명령 절 갱신
   - 예상 파일: `pyproject.toml`, `src/websearch/__init__.py`, `tests/test_smoke.py`
2. **robots.txt 확인 모듈** — 의존: 1
   - 도메인별 robots.txt 를 받아 캐시하고 URL 허용 여부를 답한다 (stdlib `urllib.robotparser` 우선)
   - 완료 기준: 허용/차단/robots 없음/응답 실패 4케이스 테스트 통과
   - 예상 파일: `src/websearch/robots.py`, `tests/test_robots.py`
3. **fetcher** — 의존: 1
   - URL 1개를 받아 HTML 을 가져온다. 타임아웃 10s, 재시도 2회, User-Agent 명시,
     text/html 이 아니면 버린다
   - 완료 기준: 성공/타임아웃/비HTML/4xx 케이스 테스트 통과 (네트워크 모킹)
   - 예상 파일: `src/websearch/fetcher.py`, `tests/test_fetcher.py`
4. **저장소 스키마** — 의존: 1
   - SQLite `pages(url PK, html, status, fetched_at)` + upsert. 스키마 생성은 코드가 한다
   - 완료 기준: 저장→재저장(갱신)→조회 테스트 통과
   - 예상 파일: `src/websearch/store.py`, `tests/test_store.py`
5. **링크 추출 + URL 정규화** — 의존: 1
   - HTML 에서 `<a href>` 절대 URL 화, fragment 제거, http(s) 만, 중복 제거
   - 완료 기준: 상대경로/fragment/mailto/중복 케이스 테스트 통과
   - 예상 파일: `src/websearch/links.py`, `tests/test_links.py`
6. **프런티어 큐** — 의존: 4, 5
   - 방문 예정 URL 큐. 이미 저장된 URL 제외, 도메인 라운드로빈으로 꺼내
     같은 도메인 간격 1초를 큐 수준에서 보장
   - 완료 기준: 중복 제외·도메인 간격 테스트 통과 (시계 모킹)
   - 예상 파일: `src/websearch/frontier.py`, `tests/test_frontier.py`
7. **크롤 루프 통합** — 의존: 2, 3, 6
   - `crawl(seeds, max_pages)` — robots 확인 → fetch → 저장 → 링크를 프런티어에.
     CLI 엔트리 1개
   - 완료 기준: 아래 e2e 시나리오 통과
   - 예상 파일: `src/websearch/crawl.py`, `tests/test_crawl.py`

## 하지 않을 것

- 색인·검색 — `plan_indexer` 이후
- JS 렌더링, sitemap.xml, 재크롤 주기 — 컨셉 "하지 않을 것" / 후속 계획
- 병렬·비동기 크롤 — 초당 5문서는 이후 계획에서 측정 후 결정. 지금은 단일 루프
- 크롤 대상 필터링(언어 감지 등) — 범위 밖

## 6-1. 설계 판단

**설계 필요** — 새 프로젝트의 스택·모듈 경계를 처음 긋는다. 언어 선택(Python vs Node),
동기/비동기 구조 등 대안이 복수다. → `phase: 설계`

## e2e 시나리오

1. 로컬 테스트 서버(페이지 20개, 일부 robots 차단) 에 시드 1개로 `crawl(seeds, max_pages=15)` 실행
   → DB 에 15행, robots 차단 URL 요청 로그 0건
2. 같은 도메인 연속 요청 타임스탬프 간격 전부 ≥ 1초
