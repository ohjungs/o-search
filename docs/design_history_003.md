# 설계: noindex-respect — 색인 시점에 meta robots 를 판정한다

계획: `docs/plan_noindex-respect.md` / 슬러그 `noindex-respect`

## 결정

`pages.html` 안의 `<meta name="robots">` 를 **색인 시점에** 읽어 noindex·none 문서는
`docs` 에 넣지 않고, 이미 `docs` 에 있으면 지운다. 스키마도 수집 경로도 건드리지 않는다.

## 대안 비교

출발점을 셋으로 나눠서 냈다 (`rules/design.md` 3-1절).

| | A. 최소 — 색인 시점 판정 | B. 정공법 — 수집 시점 차단 | C. 되돌리기 우선 — 검색 시점 필터 |
|---|---|---|---|
| 무엇 | `index_pages()` 가 html 을 보고 거르고 지운다 | `fetcher` 가 헤더를 보존하고 `pages` 에 `noindex` 컬럼 추가, `crawl` 이 기록 | `docs` 에는 그대로 넣고 `search()` 결과에서 뺀다 |
| 되돌리기 | 쉬움 (커밋 하나 revert) | 어려움 (스키마 + 수집 경로) | 쉬움 |
| 코드량 | 적음 (판정 함수 1 + 색인 분기 2줄 + 삭제 질의 1) | 많음 (3파일 + 스키마) | 가장 적음 |
| 기존과 일치 | ○ `extract` 는 이미 html.parser 로 html 을 읽는 자리다 | △ | ○ |
| 다음이 편한가 | 보통 — 매 실행 전수 재판정이 천장 | 좋음 — `X-Robots-Tag` 도 같이 풀린다 | **나쁨** |
| 야간 가능 | ○ | ✗ 스키마 변경 = 무인 금지 | ○ |

**선택: A** — 되돌리기가 가장 쉽고(기준 1순위), 판정 근거인 html 이 이미 `pages` 에
그대로 있어 새로 저장할 것이 없다. `extract` 모듈은 이미 html 을 파싱하는 자리라
관용구도 맞는다. B 가 필요해지는 순간(헤더)은 계획에서 범위 밖으로 명시했다.

**버린 이유: B** — `FetchResult` 필드 추가 + `pages` 스키마 변경(expand)이 필요하고,
`docs/project.md` 에 마이그레이션 항목이 없으므로 `rules/design.md` 4절대로 전부 보류다.
더 중요한 문제는 **판정 시점이 수집 시점으로 굳는다**는 것이다. 판정 규칙을 고치면
이미 수집한 문서는 재크롤 없이 재판정할 수 없다. A 는 html 이 남아 있어 언제든 다시 판정한다.

**버린 이유: C** — noindex 문서를 색인에 **넣어두고** 보여줄 때만 감추는 것이다.
색인 자체가 거부된 행위이므로 컨셉의 크롤 윤리 축을 만족하지 못한다. 게다가 앞으로
추가될 모든 조회 경로(search-api, 통계, 덤프)가 각자 같은 필터를 다시 걸어야 한다.

## 가정 — 탐침으로 깨봤다 (2026-08-25, 커밋하지 않음)

1. **`html.parser` 가 meta 를 놓치지 않는다** — 참. `<meta>`(void)·`<meta/>`(self-closing)·
   대문자 `<META NAME=...>`·따옴표 없는 속성·닫히지 않은 `<title>` 이 섞인 깨진 HTML
   전부에서 `handle_starttag` 가 `{'name': 'robots', 'content': ...}` 를 돌려줬다.
   태그명·속성명은 `HTMLParser` 가 소문자로 내리고 **값은 원문 그대로** 준다(`' NoIndex , nofollow '`).
2. **`'robots'` 문자열 사전 필터가 안전하다** — 참. `name="robots"` 는 정의상 그 문자열을
   포함하므로 놓치는 경우가 없다. 본문에 "noindex" 라는 낱말만 있는 문서는 문자열
   자체가 없어 파싱조차 안 한다.
3. **FTS5 `docs` 에서 UNINDEXED `url` 로 지울 수 있다** — 참. `DELETE FROM docs WHERE url=?`
   후 같은 질의가 남은 문서만 돌려주는 것을 확인했다.
4. **SQLite `LIKE '%robots%'` 는 대소문자를 구분하지 않고, `html IS NULL` 행은 안 걸린다** — 참.

셋 중 하나라도 거짓이었으면 A 는 성립하지 않는다. 넷 다 참이라 개발로 간다.

## 계약 — 개발이 지킬 것

```python
# src/websearch/extract.py
def is_noindex(html_text):
    """<meta name="robots"> 가 noindex 또는 none 을 선언하면 True."""
```

- 판정 규칙: `name` 을 소문자로 내려 `"robots"` 인 meta 만 본다. `content` 를 쉼표로
  쪼개 각 토큰을 `strip().lower()` 해서 `noindex` 또는 `none` 이 있으면 참.
  meta 가 여럿이면 **하나라도 참이면 참**.
- 사전 필터: `"robots" not in html_text.lower()` 이면 파싱하지 않고 거짓.
- 파서는 `extract.py` 안의 새 `HTMLParser` 서브클래스로 둔다. `_TextParser` 에 얹지
  않는다 — `extract_text()` 의 반환 형태(제목, 본문)를 바꾸면 기존 호출부·테스트가
  전부 흔들린다. 사전 필터 덕에 파싱이 두 번 도는 문서는 meta robots 가 실제로 있는
  드문 문서뿐이다.

```python
# src/websearch/indexer.py — index_pages(db_path) 의 변경분
```

- 삽입 경로: 기존 증분 select 결과에서 `is_noindex(html)` 이면 건너뛴다.
  **반환값은 실제로 `docs` 에 넣은 수** — 건너뛴 문서는 세지 않는다.
- 제거 경로: `SELECT d.url, p.html FROM docs d JOIN pages p ON p.url = d.url
  WHERE p.html LIKE '%robots%'` 로 후보를 좁힌 뒤 `is_noindex` 가 참인 url 만
  `DELETE FROM docs WHERE url=?`.
- 부작용은 `docs` 테이블에만 미친다. `pages` 는 읽기만 한다 — 원본을 지우면
  판정 규칙을 고쳤을 때 재판정할 근거가 사라진다.
- 커밋은 기존대로 함수 끝에서 한 번.

### 성능 천장 (ponytail 주석으로 코드에 남긴다)

제거 경로는 **매 실행 색인 전체를 훑는다**(`docs` 전수 조인). 파이썬까지 올라오는 것은
`LIKE` 를 통과한 소수지만 SQLite 는 모든 행을 읽는다. `indexer.py:21` 에 이미 같은 성격의
주석이 있고, 색인 상태 컬럼이 생기는 시점(`recrawl` 계획)에 함께 증분으로 바꾼다.
지금 미리 만들지 않는다 — 1만 문서 수준에서는 측정할 것도 없다.

## 되돌리기

커밋 하나 revert. 데이터 형태를 안 바꾸므로 되돌린 뒤 `index_pages` 를 다시 돌리면
지워졌던 문서가 그대로 다시 색인된다(`pages.html` 이 남아 있다). 마이그레이션 없음.

## 범위 밖 (→ digest 후보)

- `X-Robots-Tag` 응답 헤더 — B 안이 필요하다. `FetchResult` + `pages` 스키마(expand).
- `nofollow` 로 링크 추적 중단 — `crawl.py` 소관.
- `<meta name="googlebot">` 등 봇 이름별 지시 — 이 크롤러의 UA 는 자기 이름을 쓴다.
