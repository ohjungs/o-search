---
signal: GREEN
phase: e2e
step: 1/1
attempt: 0
iteration: 402
updated: 2026-09-07
ctx: 52
night_iterations: 197
night_red: 2
night_retries: 4
plan: noindex-entity-prefilter 계획 69 (리뷰 1/1 완료 · e2e phase 대기)
---

## 현재 상태

**계획 69 `noindex-entity-prefilter` 리뷰 1/1 끝냈다 · GREEN.**
브랜치 `loop/noindex-entity-prefilter` · 계획서 `docs/plan_noindex-entity-prefilter.md` ·
전수 **632건 `OK`** · e2e `noindex_e2e.py` rc 0 · 이번 phase 의 `src/` 변경 **2줄(주석)**.

## 이번 phase 가 산 것

**앞 phase 가 보고를 안 하고 넘긴 축 하나를 실제로 쟀다 — `&#` 판별자의 대가.**

`&#` 은 `&#38;`·`&#8212;` 같은 **평범한 엔티티에도 있다.** 그래서 `robots` 가 없는데
문자참조만 든 문서가 오늘부터 파서까지 간다. 임시 DB 로 실측했다(`data/crawl.db` 무접촉):

| 자리 | 재는 것 | 값 |
|---|---|---|
| 단건 | 20KB 문서 1건(`&#` 있고 `robots` 없음) | 0.041 → **1.808ms · x44.5** (≈ **+90ms/MB**) |
| 제거 루프 | 3000문서 × 30KB(90MB) · `robots` 55% | 4847 → **5916ms · x1.22** (후보 1683 → 2092) |
| 〃 | 같은 코퍼스 · `robots` **10%** | 932 → **3395ms · x3.64** (후보 304 → 1163) |
| 색인 루프 | 100KB 신규 문서 1건 | 14.20 → **26.62ms · x1.87** — 어차피 `extract_text` 가 뒤에서 같은 문서를 판다 |

**판정: 통과다.** 최악 x3.64 는 이미 `indexer.py:172` 가 「매 실행 전수 조인」으로
적어 둔 천장의 **상수 배**이고 새 차수가 아니다. 검색 경로는 **0** 이다. 사양 우선순위가
「크롤 윤리 > 검색 품질 > 검색 성능 > 색인 규모」라 남의 색인 거부를 존중하는 값과
색인 루프의 상수 배는 **바꿀 만한 거래**다(`docs/specs/concept.md:59`).

## 고친 것 — 보고 1건, 전부 자동 수정

`[R69-1]` 넓힌 질의의 주석이 **오탐만** 말하고 **대가**는 말하지 않는다 (`indexer.py:176`).
`metrics.md` 반복 319 가 굳힌 「`ponytail:` 천장이 «여기는 안전하다» 를 주장하면 그
주장도 실측 대상이다」의 옆 칸이다 — 「오탐이 늘지 않는다」는 참인데, 읽는 사람은
**비용도 안 는다**로 읽는다. 실측 배수를 두 줄로 적었다. **단언 무변 · 제품 동작 무변.**

## 기각한 것

- **`&#` 이 판별자로 충분한가** — 참이다. `html.entities.html5` **전수**에서 ASCII
  글자를 내는 명명 엔티티는 **1개**뿐이고 `r·o·b·o·t·s` 를 내는 것은 **0개**다.
  주석의 천장 문장이 실측과 같은 말을 한다(status 401 이 남긴 볼 자리 ①).
- **`OR` 절의 SQL 오탐/우선순위** — `WHERE` 에 `AND` 가 없어 괄호 문제가 없고,
  `&`·`#` 은 `LIKE` 와일드카드가 아니라 `ESCAPE` 도 필요 없다. `html IS NULL` 은
  `NULL` 이라 여전히 안 뽑힌다(기존 단언이 이미 문다).
- **뿌리를 놓친 형제 호출자** — `is_noindex()` 호출자는 `indexer.py:161`·`:180`
  **둘뿐**이고 diff 가 둘 다 덮는다. 남은 자리 0.

## 등재 — `digest ## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` · 중요도 4

**파서 입력을 `</head>` 까지 자르면 `&#` 갈래의 대가가 사라진다 — 실측 x893**
(100KB 문서 12.19 → 0.014ms). 등재 전에 처방을 먹여 봤다(`metrics.md` 반복 331 규칙).
**천장이 같이 나왔다** — `<body>` 안의 `<meta name="robots">` 를 놓친다(실측 True → False).
미탐이라 우선순위 최상단 축을 건드린다. **여는 조건**은 제거 루프가 증분이 된 뒤에도
전수 파싱이 예산을 밟는 날이다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
→ Ran 632 tests · OK · rc 0   (주석 수정 후 다시 1회)
PYTHONPATH=src python3 e2e/noindex_e2e.py
→ e2e 통과 · rc 0
```

**변이 0판** — 앞 phase 가 3판을 이미 돌려 생존 0을 샀다. 이번 반복의 임계경로는
비용 측정이었고 그것은 변이가 아니라 실측이다. 측정은 전부 `tempfile` 임시 DB ·
`data/crawl.db` **열지 않았다** · 스키마·마이그레이션·재색인·새 의존성 **0** ·
`docs/specs/` 무접촉.

## 다음

**e2e phase 1/1.**
