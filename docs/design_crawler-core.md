# 설계: crawler-core 스택·모듈 경계

## 결정 — Python 3.9(시스템) + 표준 라이브러리만, 동기 단일 루프, 모듈 6개

## 대안 비교

| | A. 최소: Python stdlib만 | B. 정공법: Python + requests/BS4/pytest | C. 되돌리기 우선: Node + node:sqlite |
|---|---|---|---|
| 되돌리기 | 쉬움 (커밋 revert, 지울 의존성도 없음) | 보통 (의존성 제거 필요) | 보통 |
| 코드량 | 적음 (robots·HTML파서·SQLite 전부 stdlib) | 적음 | 많음 (robots 파서 자작 또는 의존성) |
| 기존과 일치 | ○ (컨셉: SQLite 고정, 의존성 사유 없이 금지) | △ (의존성 3개 = 설계룰 4절 보류 사안) | △ (robots stdlib 없음) |
| 다음이 편한가 | ○ (indexer 가 같은 sqlite3 로 FTS5) | ○ | △ |

**선택: A** — ponytail 사다리 3번(stdlib)에서 멈춘다. `urllib.robotparser`,
`urllib.request`, `html.parser.HTMLParser`, `sqlite3` 가 계획의 스텝 2~5를 전부 덮고,
의존성 추가(설계룰 4절 보류 사안)를 아예 회피한다. 테스트도 `unittest`(stdlib).
**버린 이유: B** — requests/BS4 가 주는 편의가 보류 절차를 밟을 만큼 크지 않다.
품질 실측이 stdlib 한계를 보여줄 때 재론. / **C** — robots 파서가 stdlib 에 없고,
이후 계획(FTS5 색인)에서 Python sqlite3 만큼 매끄럽지 않다.

동기 단일 루프인 이유: 컨셉 "하지 않을 것"이 병렬·비동기를 초당 5문서 실측 전까지
금지한다. 도메인당 1초 간격이 있어 단일 루프도 도메인 다양성만 있으면 처리량이 나온다.

## 가정 — 시스템 Python 의 sqlite3 에 FTS5 가 없으면 이 설계(와 indexer 계획)가 무너진다
→ 3-2절 탐침 실행: Python 3.9.6, FTS5 가상 테이블 생성 성공, SQLite 3.51.0. **참.**

## 계약 — 개발이 지킬 것

- 문법 하한 Python 3.9 (match 문, `X | Y` 타입 표기 금지)
- 외부 의존성 0. 테스트 러너 `python3 -m unittest discover tests`
- 구조: `src/websearch/` 아래 `robots.py` `fetcher.py` `store.py` `links.py`
  `frontier.py` `crawl.py`. 패키지 실행은 `PYTHONPATH=src` (setup/pyproject 빌드 없음)
- 시그니처:
  - `robots.RobotsCache.allowed(url: str) -> bool` — robots 응답 실패 시 **허용**(관례),
    단 5xx 는 차단(보수)
  - `fetcher.fetch(url) -> FetchResult(status, html | None, url | None)` — 타임아웃 10s, 재시도 2회,
    UA `websearchbot/0.1`, text/html 외·2xx 외는 html=None, 응답 크기 상한 2MB.
    url 은 리다이렉트 후 최종 URL(저장 키·링크 base) — 리뷰 phase 에서 추가(리다이렉트 base 오염 수정)
  - `store.Store(path)` — 테이블 `pages(url TEXT PK, html TEXT, status INT, fetched_at TEXT)`,
    `upsert(url, html, status)`, `has(url) -> bool`. DB 파일 `data/crawl.db` (gitignore)
  - `links.extract(base_url, html) -> list[str]` — 절대화, fragment 제거, http(s)만, 중복 제거
  - `frontier.Frontier.add(urls)` / `.next() -> url | None` — 도메인 라운드로빈,
    같은 도메인 마지막 요청 후 1초 미만이면 다른 도메인을 먼저 낸다
  - `crawl.crawl(seeds, max_pages, db_path, robots_cache=None, now=time.monotonic) -> int(수집 수)`
    (robots_cache·now 는 개발·테스트 phase 에서 추가 — 실네트워크·실시계 없는 테스트를 위한 주입 지점)
- 부작용 범위: 파일은 `data/` 아래만. 네트워크는 fetcher·robots 만 나간다.
  테스트는 실네트워크 금지(`project.md` 한도)

## 되돌리기 — 의존성·설정 없음. 커밋 revert 로 끝

## 범위 밖 — sitemap.xml, 압축 응답(gzip 헤더), 인코딩 추정(chardet류), robots crawl-delay 존중
→ crawl-delay 는 digest 후보로 (윤리 축이라 우선순위 높음)
