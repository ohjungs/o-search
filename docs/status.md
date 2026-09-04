---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 324
updated: 2026-09-05
ctx: 47
night_iterations: 146
night_red: 2
night_retries: 0
plan: db-state-invariant # 계획 55 — 테스트 1/1 완료(자기검사 2 를 더했다) · 다음은 리뷰
---

# 현재 상태

**계획 55 `db-state-invariant` 의 테스트 1/1 이 끝났다.** 전수를 맨몸으로 다시 돌리고
갭을 훑어 **8점짜리 하나**를 닫았다. 브랜치는 `loop/db-state-invariant`.
**다음 phase 는 리뷰다.**

## 이 반복이 직접 잰 것 (반복 324)

**전수 재확인** — `PYTHONPATH=src python3 -m unittest discover -b -s tests` 를 맨몸·단독
(러너를 파이프 왼쪽에 안 둔다)으로 돌려 **604건 OK · 13.320초 · rc 0**. 직전 반복이 적어
둔 604 는 참이었다. 새 테스트를 더한 뒤 **605건 OK · 13.448초 · rc 0**.

**변이 넷을 다시 심었다**(전부 저장소 밖 사본에서 · `PYTHONDONTWRITEBYTECODE=1`).

| 변이 | 결과 |
|---|---|
| ① 처방 되돌리기 (`SELECT url, html` → `SELECT html`) | **RED, 604건 중 정확히 1건** — 새 자의 `missing='url'` 뿐 (`{'김치찌개': 'OperationalError', 'zzzznope': 'ok', '\x01': 'ok'}`) |
| ② 눈금 0칸 (`_columns` → `[]`) | **RED** — 자기검사가 `0 not greater than or equal to 4` |
| ③ `store.SCHEMA` 에 `lang TEXT` 추가 | 눈금 **4 → 5칸** 자동 확장(`url·html·status·fetched_at·lang`), 자는 **그대로 GREEN**(처방 A 에 expand 함정이 없다는 설계 4절의 재확인) |
| ④ 판정 삼키기 (`except OperationalError: return []`) | **RED 8건** — 전부 계획 53·54 가 남긴 클래스(`TestPassages`·`TestPassagesWithoutHtmlColumn`·`…BeforeIndexing`). **새 자는 이 변이에 안 죽는다**(셋 다 `ok` 라 판정은 여전히 하나) |

**변이 ①이 604건 중 1건만 죽였다는 것이 「53·54 클래스가 중복인가」의 답이다** — 아니다.
`url` 축을 잡는 자는 저장소에 **새 자 하나뿐**이고, 반대로 변이 ④는 새 자가 못 잡고 53·54
클래스만 잡는다. 둘은 **서로 다른 것을 잰다**(일관성 vs 값). 지우면 구멍이 생긴다.

## 이 반복이 더한 것 — 갭 하나 (중요도 8)

**`tests/test_indexer.py` `TestPassagesColumnAxisInvariant.test_the_three_queries_really_have_different_shapes`** (+1건, `src/` **0줄**).

자기검사가 **눈금 축만** 막혀 있었다. 자가 재는 물음은 «루프에 **닿는** 질의와 **못 닿는**
질의가 같은 판정인가» 인데, `DOC`·`QUERIES` 가 바뀌어 세 질의가 같은 모양이 되면 그 물음이
사라져도 판정은 여전히 하나라 **조용히 초록**이 된다 — 설계가 위험 1 로 막은 「눈금 0칸」과
같은 고장이 다른 방아쇠로 살아 있었다. 정상 DB 에서 세 질의의 모양이
`[True, False, False]` 인지 한 줄로 단언한다(정상 DB 오탐 0 도 같은 줄이 잡는다).

**RED 를 보고 넣었다** — 사본에서 `DOC` 의 `김치찌개` 를 `된장찌개` 로 바꾸니 새 자기검사만
`[False, False, False]` 로 **RED**, 본 자는 GREEN. 정확히 그 구멍이다.

## 8점 미만이라 안 한 것 (리뷰·다음 계획 몫)

- **`url` 열 없는 DB 의 HTTP 표면 클래스**(5점) — 직전 반복이 실서버로 500·500·500 을
  쟀지만 테스트로는 안 박았다. 설계 5절이 `serve.py` 매핑을 범위 밖으로 두었고,
  `OperationalError → 500` 은 `TestPassagesWithoutHtmlColumn` 이 이미 박고 있다(변이 ④가
  증명했다). 새 클래스는 같은 매핑의 두 벌이다.
- **두 열 이상이 동시에 빠진 조합**(4점) · **열 타입이 바뀐 축**(4점) — 설계 6절이 적어 둔
  천장 그대로. 조합을 늘리면 재현 비용만 는다.

## 범위 (하드 제약 확인)

`src/` **0줄** · `serve.py`·`store.py`·스키마·마이그레이션·재색인 **0** · 새 의존성 0 ·
새 예외 0 · stdlib 만 · 고친 파일 **둘**(`tests/test_indexer.py` +16줄 ·
`README.md` 의 `단위 604건` → `605건`) · `docs/specs/` 무변 ·
`data/crawl.db` sha256 `85c96744…5bda18` **무변**(모든 변이가 저장소 밖 사본) ·
서버 0개(`pgrep -f websearch.serve` 잔여 0) · `main` 직접 커밋 0 ·
`--no-verify`·`--force` 0 · **PR 무접촉(조회 0회)** · 브랜치 병합 시도 0 ·
e2e 21종 전수는 **e2e phase 몫**.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **브랜치 병합** — 원격 `main` 은 `c0be72f`, 계획 54(PR #9)까지 들어 있다.
   `loop/db-state-invariant` 의 병합은 사람 몫이고 `main` 직접 커밋은 하지 않는다.
   **이 반복도 PR 을 조회조차 안 했다.**

## 정지 사유

없음 — 계획 55 **리뷰** 로 이어간다.
