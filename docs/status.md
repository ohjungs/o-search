---
signal: GREEN
phase: test
step: 1/1
attempt: 0
iteration: 400
updated: 2026-09-06
ctx: 55
night_iterations: 195
night_red: 2
night_retries: 4
plan: noindex-entity-prefilter 계획 69 (개발 1/1 완료 · 테스트 phase 대기)
---

## 현재 상태

**계획 69 `noindex-entity-prefilter` 개발 1/1 끝냈다 · GREEN.**
브랜치 `loop/noindex-entity-prefilter` · 계획서 `docs/plan_noindex-entity-prefilter.md` ·
스텝 **1개**를 전부 닫았다. **아홉 계획 만에 `src/` 에 착지했다** — 제품 **2줄**,
고친 파일 2개(`src/websearch/extract.py`·`src/websearch/indexer.py`).

## 이번 phase 가 산 것

**엔티티로 인코딩된 `meta robots` name 의 색인 거부 선언이 두 자리 모두에서 먹는다.**

1. `extract.is_noindex()` 의 사전 필터가 `robots` 낱말 **또는 `&#`** 이면 파싱한다.
   `<meta name="&#114;obots" content="noindex">`(십육진 `&#x72;`·대문자 `&#X72;` 포함)가
   이제 True 다. 판정은 예전처럼 `_MetaRobotsParser` 가 하고 — HTMLParser 가 속성값을
   이미 언이스케이프한다 — 필터는 그 파서까지 데려가는 일만 한다.
2. `indexer.py` 의 제거 질의에 같은 갈래(`OR p.html LIKE '%&#%'`)를 더했다. 이미 색인된
   문서가 뒤늦게 인코딩된 거부를 달아도 후보로 뽑혀 제거된다.

**빠른 길은 그대로다.** `robots` 도 `&#` 도 없는 평범한 문서는 파싱 0회로 지나간다.
`&#` 을 판별자로 고른 근거는 계획 phase 실측이다 — `r` 을 내는 이름 있는 엔티티가 없어
십진·십육진 문자참조가 전부 걸리고, `&amp;` 만 든 문서에는 `&#` 이 없다.

**오탐은 늘지 않는다.** 두 자리 모두 필터는 **후보를 넓히는 자**이고 최종 판정은 그 뒤의
`is_noindex()` 가 한다. 그 방향도 단언으로 못박았다(`&#38;`·`&#8212;` 만 든 본문,
`name="&#114;obots" content="index, follow"` 둘 다 False).

## TDD

**RED 를 눈으로 봤다** — 새 단언 4개 중 3개가 실패했다(`FAILED (failures=4)`,
넷째는 README 건수).
`test_entity_encoded_name_is_a_directive` `False is not true` ·
`test_entity_encoded_noindex_page_is_not_indexed` `2 != 1`(거부 문서가 색인됐다) ·
`test_already_indexed_page_declaring_entity_encoded_noindex_is_removed`
`[('http://a.test/', '', '허용 pyeongsan')] != []`(제거 질의가 후보로도 안 뽑았다).
**두 자리가 각각 따로 울었다** — 진입만 고쳤으면 셋째가 살아남았을 자리다.
제품 2줄을 넣고 GREEN.

## 검증

전수 **`Ran 632 tests` · `OK` · rc 0**(맨몸 1회) ·
`PYTHONPATH=src python3 e2e/noindex_e2e.py` rc 0 ·
`README.md:104` 「단위 628건」→**632건** · `data/crawl.db` 무변(`git status --porcelain`
에 없다) · 스키마·마이그레이션·재색인·새 의존성 **0** · `docs/specs/` 무접촉.

## 다음

**테스트 phase 1/1.** 변이는 두 자리로 자연스럽다 — 필터의 `&#` 갈래를 빼는 변이와
제거 질의의 `OR` 절을 빼는 변이가 **각각 다른 단언**을 죽여야 한다. 저장소 밖
`mktemp -d` 사본에서 최대 3판.
