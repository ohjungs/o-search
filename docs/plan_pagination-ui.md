# 계획: pagination-ui — 검색 화면에서 2페이지로 갈 수 있게 한다

- 브랜치: `loop/pagination-ui` (기점 `716d245`, `loop/crawl-politeness` 위)
- 출처: `docs/index.md` 의 사양 분할 · `status.md ## 다음 계획`
- 의존: 009(`search-api`, `page=` 계약) · 013(`search-ui`, 렌더·디자인 검사)

## 1. 문제 · 목표 · 기대 결과

### 문제 — 서버는 2페이지를 줄 수 있는데 화면에 가는 길이 없다

`src/websearch/serve.py:217` 의 HTML 경로는 이미 `_parse()` 로 `page` 를 받고
`offset=(page - 1) * PAGE_SIZE` 로 조회한다. **`?q=X&page=2` 를 손으로 치면 2페이지가
나온다.** 그런데 `_results()` 가 그리는 것은 결과 목록뿐이라, 주소창을 편집할 줄 아는
사람만 11번째 결과를 볼 수 있다. 10건에서 못 찾으면 거기서 끝난다.

JSON API 는 같은 문제를 이미 풀었다 — `limit=PAGE_SIZE + 1` 로 받아 11번째의 유무로
`has_next` 를 판정하고(`serve.py:189-192`), 상한도 서버가 알려준다
(`has_next = len(hits) > PAGE_SIZE and page < MAX_PAGE`). **HTML 경로만 이 판정을
안 한다** — `limit=PAGE_SIZE` 로 딱 맞게 받으므로 다음 페이지가 있는지 알 방법이 없다.

### 목표

결과 화면 아래에 **이전 / 다음** 링크를 낸다. 그뿐이다.

### 기대 결과 (측정 가능하게)

| # | 기대 | 재는 법 |
|---|---|---|
| 1 | 11건 이상 맞는 질의의 1페이지에 `page=2` 링크가 있다 | 응답 HTML에 `href` 존재 |
| 2 | 마지막 페이지에는 다음 링크가 **없다** | 10건짜리 질의의 1페이지 |
| 3 | 2페이지에 `page=1` 링크가 있고, 1페이지에는 **없다** | 부정·긍정 짝 |
| 4 | `page=MAX_PAGE`(100)에서는 다음 링크가 없다 | 상한도 서버가 안다 (JSON 과 같은 규칙) |
| 5 | 결과가 0건인 2페이지 이상에서도 **이전 링크는 있다** | 막다른 길을 안 만든다 |
| 6 | JS 가 여전히 **0바이트** · 대비 4.5:1 · 360px 가로 스크롤 없음 | `e2e/design_check.py` 종료 0 |
| 7 | "N건" 표시가 11 로 새지 않는다 | `PAGE_SIZE + 1` 로 받는 데서 오는 함정 |

## 2. 읽고 확인한 것 (추측 아님)

- `_parse()`(`serve.py:33`)가 `page` 를 1..`MAX_PAGE`(100)로 이미 검증한다. **두 경로가
  같이 쓴다** — 여기를 고치면 `/search` 의 400 계약이 바뀐다. 손대지 않는다
- `PAGE_SIZE = 10`, `MAX_PAGE = 100`. `MAX_PAGE` 는 성능이 아니라 **자원 고갈 방어**다
  (깊은 OFFSET, 실측 offset 990 에서 7.2ms)
- `_results(query, hits)` 는 인자가 둘뿐이다 → `page`·`has_next` 를 받아야 한다
- CSS 규약: **새 `--fg-*` 토큰을 만들면 `design_check.PAIRS` 에도 짝을 적어야 하고,
  안 적으면 검사기가 종료 2(측정 불능)를 낸다**(`serve.py:53-57`). 그러므로 페이지
  이동은 **기존 토큰**(`--fg-link`·`--fg-muted`·`--line`)만 쓴다
- 360px 규약: 고정폭을 만들면 `design_check.check_mobile` 이 잡는다. flex + wrap 으로 낸다

## 3. 스텝

### 스텝 2 — HTML 경로가 다음 페이지의 유무를 알고, `_results` 가 이동을 그린다

의존: 없음. 파일: `src/websearch/serve.py` (+ `tests/test_serve.py`)

- `_do_html` 이 `limit=PAGE_SIZE + 1` 로 받는다 (JSON 경로와 같은 수법, 개수 질의 없음)
- `has_next = len(hits) > PAGE_SIZE and page < MAX_PAGE` — **판정 규칙을 두 경로가
  나눠 쓰게 한다**(같은 규칙이 두 벌이면 한쪽만 고쳐진다)
- `_results(query, hits, page, has_next)` — `hits[:PAGE_SIZE]` 로 잘라 그린다.
  **"N건" 은 자른 뒤의 수다**(기대 7)
- 이동 블록은 `<nav>` 안의 `<a href="/?q=…&page=N">` 둘. `rel="prev"`/`rel="next"`,
  `aria-label` 을 붙인다. **JS 없음**

RED 를 먼저 본다: 위 기대 1~5 를 단언하는 테스트가 현재 코드에서 실패하는 것을 확인한다.

### 스텝 3 — 테스트 phase

의존: 2. `rules/test.md` 6개 카테고리로 훑고, 변이는 **"이 줄을 안 썼다면"** 기준으로 고른다.
무변이 기준선을 먼저 잡는다.

### 스텝 4 — 리뷰

의존: 3. **별도 백지 세션**(diff + 소스만, `docs/` 차단).

### 스텝 5 — e2e

의존: 4. `docs/e2e/pagination-ui/result.md`. 시나리오는 **실제 응답 바이트**로 잰다:

1. 문서 11개를 색인해 1페이지 → 다음 링크를 따라가면 **11번째 문서가 보인다**
   (링크의 존재가 아니라 **따라간 결과**를 잰다)
2. 마지막 페이지에 다음 링크 없음 · 1페이지에 이전 링크 없음 (부정 짝)
3. `design_check.py` 종료 **0** — JS 0B · 대비 · 360px 회귀
4. 잴 대상이 사라지면(문서가 11개 미만) **종료 코드 2**. 조용히 통과하지 않는다

## 4. 하지 않을 것

- **총 건수 표시**(`검색 결과 1,230건`) — COUNT 는 두 번째 전수 질의라 p95 에 그대로
  얹힌다(`design_search-api.md` 계약). 총 건수를 모르므로 **페이지 번호 목록(1 2 3 …)도
  안 만든다.** 이전/다음만이 지금 아는 정보로 정직하게 그릴 수 있는 것이다
- JSON API 응답 변경 (`/search` 는 이미 옳다)
- `_parse()` 수정 — 400 계약이 두 경로에 걸려 있다
- `PAGE_SIZE`·`MAX_PAGE` 값 변경
- 새 `--fg-*` 색 토큰 (`design_check.PAIRS` 를 건드려야 한다)
- 무한 스크롤·프리페치 (JS 0B 를 깬다)
- `loop/*` 병합 · `docs/specs/` 수정 · `pages` 테이블
