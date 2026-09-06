# 계획 69 `noindex-entity-prefilter`

- 브랜치: `loop/noindex-entity-prefilter` (기점 `7fcd669` = `origin/main`)
- 스텝: **1개** (개발 1/1)
- 설계: **없음** — 갈림길이 한 자리 두 줄이고 대안 셋을 아래 4절 표에서 잰다
- 근거: **사용자 지시**(반복 399, 「소스 편중을 깨라 — `src/websearch/` 를 고치는
  계획을 열어라」) + `docs/digest.md` 「다음 계획 후보」 `[4]`(`is_noindex` 의
  `'robots'` 사전 필터와 제거 경로의 `LIKE '%robots%'` 가 엔티티 인코딩된 name 을
  놓친다, 2026-08-25 리뷰) + `src/websearch/extract.py:202-203` 이 스스로 적어 둔
  천장 주석. **계획 60~68 아홉 계획이 `src/` 를 0줄 고쳤다** — 이 계획은 제품에 착지한다.

## 1. 문제

`meta robots` 의 `name` 을 HTML 엔티티로 인코딩한 문서는 **색인 거부 선언이 무시된다.**
파서는 지시를 제대로 보는데 그 앞의 사전 필터가 파싱 자체를 막는다.

**오늘 다시 쟀다** (2026-09-06 · 반복 399 계획 phase 탐침 · 기점 `7fcd669` ·
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 로 실행):

| 입력 | `is_noindex()` | `_MetaRobotsParser` 단독 |
|---|---|---|
| `<meta name="&#114;obots" content="noindex">` | **False** | `['noindex']` |
| `<meta name="&#x72;obots" content="none">` | **False** | `['none']` |
| `<meta name="robots" content="noindex">` | True | `['noindex']` |

즉 **막는 것은 파서가 아니라 `src/websearch/extract.py:204` 의 한 줄**이다:

```python
if "robots" not in html_text.lower():
    return False
```

**같은 구멍이 두 자리다.** 색인 진입을 막는 `extract.is_noindex()`(호출자
`src/websearch/indexer.py:162`)와, **이미 색인된 문서를 빼는** 경로
`src/websearch/indexer.py:176` 의 `WHERE p.html LIKE '%robots%'` 가 같은 문자열
필터를 쓴다. 한쪽만 고치면 「새로 안 넣지만 옛것은 남는다」가 된다 — 크롤 윤리 축의
누락은 오탐보다 무겁다(사양 `docs/specs/concept.md` 의 크롤 윤리 1순위 · `robots.txt`
준수와 같은 계약이다).

**왜 지금 여는가.** 후보 `[4]` 가 적어 둔 여는 조건은 「실물에서 보이면 그때 뺀다」였다.
그 조건은 오늘 사용자 지시가 대신 열었고(discover 0절 — 지시가 곧 근거),
**처방은 「필터를 뺀다」가 아니라 「필터를 엔티티까지 넓힌다」로 갈아 끼운다**(4절).
후보 항목의 처방을 실행 전에 다시 재는 것은 이 저장소의 재발 교훈
(`digest [7]` 「기록된 답을 실행 전에 다시 재라」)의 여섯 번째 적용이다.

## 2. 목표와 기대 결과

엔티티로 인코딩된 `name` 을 쓴 `noindex`·`none` 선언이 **두 자리 모두**에서 먹는다.
`robots` 도 `&#` 도 없는 평범한 문서는 **오늘과 같은 빠른 길**(파싱 0회)로 지나간다.

## 3. 스텝

### 개발 1/1 — 두 자리의 사전 필터에 `&#` 갈래를 더한다

고칠 파일 **2개** · 제품 **2줄** (+ 주석·테스트):

1. `src/websearch/extract.py` `is_noindex()` 의 사전 필터를
   「`robots` 가 있거나 **문자열에 문자참조가 있으면**」으로 넓힌다.
2. `src/websearch/indexer.py:176` 의 제거 질의 `WHERE p.html LIKE '%robots%'` 에
   같은 갈래(`OR p.html LIKE '%&#%'`)를 더한다. 이 질의는 **후보를 좁히는 자**이고
   최종 판정은 그 뒤의 `extract.is_noindex()` 가 하므로 넓혀도 오탐이 안 는다.

판별자를 `'&#'` 로 잡는 근거(오늘 실측): 십진(`&#114;`)·십육진(`&#x72;`·`&#X72;`)
문자참조는 **전부 `&#` 로 시작**하고, `r` 을 내는 **이름 있는 엔티티는 없다**.
`&amp;` 만 든 문서(`<p>a &amp; b</p>`)에는 `&#` 이 **없다** — 빠른 길이 유지된다.

**완료 기준** (각각 단언 하나로 잰다 · `tests/test_extract.py`·`tests/test_indexer.py`):

1. `extract.is_noindex()` 가 `name="&#114;obots" content="noindex"` 에 **True**
   (오늘 False) · `name="&#x72;obots" content="none"` 에도 **True**.
2. 같은 문서가 이미 `docs` 에 있는 DB 에서 `index_pages()` 재실행이 그 행을
   **뺀다**(제거 경로가 후보로 집어 온다). 오늘은 `LIKE '%robots%'` 가 못 집어 남는다.
3. **필터의 값이 남는다** — `robots` 도 `&#` 도 없는 문서에서
   `_MetaRobotsParser` 가 **0회** 생성된다(가짜로 계수한다).
4. 오탐 0 — 기존 `is_noindex` 단언 전부 그대로 초록.
5. 전수 `python3 -m unittest discover -b -s tests` 가 `OK`(628 + 새 단언) ·
   `README.md` 의 테스트 건수 한 줄을 그 수로 갱신.

## 4. 왜 이 방향인가

| 안 | 내용 | 판정 |
|---|---|---|
| **A (채택)** | 사전 필터에 `&#` 갈래를 더한다 (두 자리, 제품 2줄) | 구멍을 닫고 **빠른 길을 대부분 문서에 남긴다** |
| B | 사전 필터를 **뺀다** (후보 `[4]` 가 적어 둔 원래 처방) | 정확도는 A 와 같은데 **모든 페이지를 색인마다 한 번 더 파싱**한다 — 얻는 것 없이 비용만 |
| C | `html.unescape(html_text)` 로 먼저 풀고 검사한다 | 캡 없는 문자열의 **전체 사본**을 뜬다(`fetcher.MAX_BYTES` 2MB) — B 보다 비싸고, 본문 속 `&#114;obots` 텍스트에 오탐이 난다 |

## 5. 하지 않을 것

- `_SKIP_TAGS`·`_INLINE_TAGS`·`extract_text` **무접촉** — 색인 본문이 바뀌면 재색인이다
- `<meta http-equiv="X-Robots-Tag">` 변형 (`digest [5]`) — 별도 축, 안 연다
- 본문 속 진짜 `<meta name="robots">` 의 head 제한 오탐 (`digest [4]`) — 안 연다
- 스키마 변경 · 마이그레이션 · 재색인 · `data/crawl.db` 변경 · 새 의존성 **전부 0**
- `docs/specs/` 는 읽기만 — 한 글자도 안 고친다
- e2e 새 파일 0 — 이 계획의 판정은 단위로 끝난다(색인 거부는 이미
  `e2e/indexer_e2e.py`·`e2e/noindex_e2e.py` 가 실물로 돈다)

## 6. 검증 명령 (맨몸 · 리다이렉션 금지)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
PYTHONPATH=src python3 e2e/noindex_e2e.py
```
