# 계획: 비ASCII URL 을 크롤할 수 있게 한다

- **슬러그**: `non-ascii-url`
- **브랜치**: `loop/non-ascii-url` (`loop/quality-eval` 37fa3aa 에서 갈라졌다 — 이 저장소의 계획 브랜치는 직렬로 쌓인다)
- **근거**: 사용자 지시 — "`src/websearch/fetcher.py` 의 비ASCII URL 버그(`https://ko.wikipedia.org/wiki/대한민국` 가 `UnicodeEncodeError`)". **이 계획을 세우며 로컬 서버로 재현했다**(아래 `## 실측`)
- **시작**: 2026-08-26

## 문제

한글이 든 URL 을 크롤하면 **크롤 루프가 통째로 죽는다.** `fetcher.fetch()` 가
`FetchResult(0, ...)` 를 돌려주는 것이 아니라 **예외가 함수 밖으로 새 나간다.**

```
fetch("http://127.0.0.1:PORT/위키/대한민국")
→ UnicodeEncodeError: 'ascii' codec can't encode characters in position 5-6
```

`fetcher.py:20-23` 의 `try` 는 `urllib.request.Request(url, ...)` **생성만** 감싼다.
실제 인코딩은 `urlopen` 안쪽(`http.client` 가 요청 줄을 ASCII 로 만들 때) 일어나고,
`fetcher.py:40` 의 `except (urllib.error.URLError, OSError)` 는 `UnicodeEncodeError`
(=`ValueError` 계열)를 안 잡는다. 그래서 `crawl.crawl()` 의 while 루프가 그 자리에서 끝난다.

**이것은 한국어 검색엔진에서 주변부 결함이 아니다.** `docs/specs/concept.md` 가 한국어를
1급으로 세웠는데(기능 2 의 합격선이 한국어 20질의다) 한국어 위키백과 URL 은 대부분
비ASCII 다. 지금은 그런 링크가 하나 섞이면 **그 크롤 세션 전체가 중단**된다.

## 목표

한글(또는 임의의 비ASCII) URL 이 섞인 사이트를 **끝까지 크롤한다.** 그 URL 의 페이지가
`pages` 에 저장되고, 같은 페이지가 표기만 달라 **두 행이 되지 않는다.**

## 실측 (이 계획을 세우며 로컬 서버로 확인한 것)

| 확인한 것 | 결과 |
|---|---|
| `fetch("http://host/위키/대한민국")` | **`UnicodeEncodeError` 가 함수 밖으로 나간다** (`FetchResult` 아님) |
| `fetch("http://host/%EC%9C%84")` (이미 인코딩됨) | 200. 서버가 받은 경로 `/%EC%9C%84` — **정상** |
| `RobotsCache.allowed("http://host/위키/...")` | **True. 안 죽는다** — 호스트가 ASCII 면 `robots.txt` URL 도 ASCII 라 이 경로는 무사하다 |
| `urlopen("http://한글도메인.test/")` (IDN 호스트) | `UnicodeEncodeError: 'latin-1'` — **경로와 원인이 다르다.** 호스트는 IDNA 가 필요하다 |
| `links.extract(base, "<a href='/가.html'>")` | `http://host/가.html` — **날것 그대로 프런티어·`pages` 에 들어간다** |
| `urllib.parse.quote("/%EA%B0%80.html", safe="/%")` | 그대로. **`safe` 에 `%` 를 넣으면 재인코딩이 안 일어난다** |

마지막 두 줄이 이 계획의 핵심 위험이다: **같은 페이지가 `/가.html` 과 `/%EA%B0%80.html`
두 표기로 `pages` 에 각각 저장될 수 있다.** `store.has()` 도 `Frontier` 의 중복 제거도
문자열 비교라 둘을 다른 URL 로 본다. 정규화를 **어느 경계에서** 하느냐로 이 결과가 갈린다.

## 설계

**필요** → `docs/design_non-ascii-url.md`

트리거 둘: **대안이 2개 이상 갈린다**(정규화 지점을 `fetcher.fetch` 안으로 넣느냐,
`links.extract`/`Frontier.add` 경계로 올리느냐 — 어느 쪽이든 크롤은 되지만 `pages` 에
남는 키가 달라진다) · **새 파일 가능성**(정규화 함수를 `src/websearch/urls.py` 로 뺄지
기존 모듈에 둘지). 설계가 답할 것:

1. **정규화 지점** — 저장 키를 무엇으로 할 것인가. 이미 `pages` 에 들어간 URL 과의 관계는
2. **함수의 집** — 새 모듈 / `links.py` / `fetcher.py` 중 어디
3. **인코딩 규칙** — 경로·질의는 `quote(safe=...)`, 호스트는 `encode("idna")`.
   `safe` 에 무엇을 넣는가(`%` 를 넣으면 재인코딩은 막지만 **경로에 든 진짜 `%` 문자**는
   못 고친다 — 그 한계를 받아들일지)

## 스텝 (설계가 갱신할 수 있다)

### 1. 정규화 함수 — 비ASCII 를 퍼센트/IDNA 로 바꾼다
- **의존**: 없음
- **예상 파일**: `src/websearch/urls.py`(설계가 위치를 정한다), `tests/test_urls.py`
- **완료 기준**: 함수가 아래를 만족하는 단위 테스트가 통과한다.
  `http://h/위키/대한민국` → `http://h/%EC%9C%84%ED%82%A4/%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD` ·
  이미 인코딩된 URL 은 **그대로**(멱등) · IDN 호스트는 `xn--` 로 · ASCII URL 은 **한 글자도
  안 바뀐다**(회귀 위험이 여기 있다)

### 2. 크롤 경로에 배선한다
- **의존**: 1
- **예상 파일**: 설계가 정한 경계(`src/websearch/links.py` 또는 `src/websearch/crawl.py`), 해당 테스트
- **완료 기준**: `links.extract` 가 돌려주는 URL 이 전부 ASCII 다. 한글 링크와 그것을
  퍼센트 인코딩한 링크가 **같은 페이지 안에 둘 다 있으면 결과가 1건**이다(중복 제거)

### 3. `fetch` 가 예외를 밖으로 내보내지 않는다
- **의존**: 없음 (1·2 와 독립. 최후 방어선이다)
- **예상 파일**: `src/websearch/fetcher.py`, `tests/test_fetcher.py`
- **완료 기준**: 정규화를 통과하지 못한 URL 을 `fetch()` 에 직접 넣어도
  **`FetchResult(0, None, None)`** 이 나온다(예외 아님). 테스트가 `UnicodeEncodeError` 를
  기대하지 않고 `status == 0` 을 단언한다. `crawl.crawl()` 은 그 URL 을 건너뛰고 계속 돈다

### 4. e2e — 한글 URL 이 든 사이트를 끝까지 크롤한다
- **의존**: 2, 3
- **예상 파일**: `e2e/crawl_e2e.py`(기존에 시나리오 추가) 또는 새 e2e, `docs/project.md`
- **완료 기준**: 로컬 HTTP 서버가 `/` 에서 한글 경로 링크를 걸고, 크롤 후 `pages` 에
  **그 페이지가 1행** 있다(0행도 2행도 아니다). 종료 코드 0

## e2e 시나리오

1. 한글 경로 링크를 따라가는 크롤 → 페이지가 저장되고 **크롤이 중단되지 않는다**
2. 같은 페이지를 한글 표기와 퍼센트 표기 두 링크로 걸어둔다 → `pages` 에 **1행**
3. 정규화로도 못 살리는 URL(예: 서로게이트가 든 것)을 시드에 섞는다 → 그 URL 만
   건너뛰고 나머지는 전부 수집된다

## 하지 않을 것

- **`pages` 에 이미 들어간 URL 의 소급 정규화** — 기존 행을 다시 쓰는 일이고 재크롤
  정책(`recrawl`, 보류 중)과 겹친다. 새로 들어오는 URL 만 다룬다
- **URL 정규화 일반**(끝 슬래시·기본 포트·질의 순서·대소문자 호스트) — 비ASCII 와 무관하다.
  하면 `pages` 의 키가 통째로 바뀐다. 하고 싶으면 별도 계획
- **국제화 도메인의 보안 검사**(혼동 문자·homograph) — 크롤러가 사람에게 URL 을 보여주는
  화면이 아직 없다. `search-ui` 계획 소관
- **`robots.txt` 경로의 IDNA** — 스텝 1 의 함수를 쓰면 자동으로 따라오지만, 별도로
  `robots.py` 를 손보지는 않는다. 실측상 ASCII 호스트에서는 이미 무사하다
- 검색 품질 fixture·랭킹 — `quality-eval`(006)이 고정한 기준선을 이 계획은 건드리지 않는다

## 기록

- 2026-08-26 반복 56 — 계획 작성. 설계 필요 판정(정규화 지점·함수 위치)
