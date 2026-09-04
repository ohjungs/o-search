---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 323
updated: 2026-09-05
ctx: 63
night_iterations: 145
night_red: 2
night_retries: 0
plan: db-state-invariant # 계획 55 — 개발 1/1 완료(자 + 처방 한 낱말) · 다음은 테스트
---

# 현재 상태

**계획 55 `db-state-invariant` 의 개발 1/1 이 끝났다.** 설계 5절 계약을 그대로 TDD 로
돌았고 브랜치는 `loop/db-state-invariant`. **다음 phase 는 테스트다.**

## 이 반복이 만든 것

**자 — `tests/test_indexer.py` `TestPassagesColumnAxisInvariant`**(`TestPassages` 옆 ·
HTTP 안 띄운다). 눈금을 우리가 안 적고 **정상 DB 의 `PRAGMA table_info(pages)`** 에서
받는다: 자기검사(4칸 이상 · `url`·`html` 포함) → 열마다 `subTest` 로 ①정상 DB 재생성
②그 열을 뺀 `pages` 로 교체(이름·선언 타입 둘 다 `PRAGMA` 가 준다 · 손으로 적는
스키마 0줄) ③세 질의(`김치찌개`·`zzzznope`·`\x01`)의 **판정 이름** 수집
④`len(set(...)) == 1`. **재는 것은 반환값이 아니라 판정**(예외 클래스 이름 또는 `ok`)
이다 — 설계가 거짓 RED 로 죽인 초안이 반환값을 비교한 것이었다.

**처방 — `src/websearch/indexer.py` `passages()` 의 한 낱말**:
`SELECT html FROM pages LIMIT 0` → **`SELECT url, html FROM pages LIMIT 0`**. 자리
(가드 직후 · `hits` 루프 앞)·시그니처·docstring 무변. 그 줄 위 `ponytail:` 주석 두
문장(「`html` 한 열만 본다」·「넓히는 날은 한 낱말」)이 거짓이 되므로 **같은 커밋에서**
새 천장으로 고쳤다 — 「아래 루프가 읽는 두 열만 본다 · 스키마 전 열을 요구하는 안은
설계 55 가 expand 함정으로 죽였다」.

**`tests/test_serve.py` 새 클래스 0개**(설계 5절) · `serve.py`·`store.py`·스키마
**0줄** · 새 예외 0 · 새 의존성 0.

## 이 반복이 직접 잰 것 (반복 323)

**RED 를 눈으로 먼저 봤다** — 자만 세운 상태에서 실패가 **정확히 `url` 한 행**이고
내용이 `{'김치찌개': 'OperationalError', 'zzzznope': 'ok', '\x01': 'ok'}` 였다. 처방
한 낱말로 **4행 전부 GREEN**. 설계가 예고한 값과 한 칸도 안 달랐다.

**완료 기준 5절을 대칭으로 잰 결과** — 오탐 0(정상 DB `1/0/0` · `status` 뺀 DB
`1/0/0` · `fetched_at` 뺀 DB `1/0/0`, 셋이 같다) · 눈금이 스키마를 따라간다(사본
`SCHEMA` 에 `lang TEXT` 를 더하니 케이스가 **4 → 5** 로 저절로 늘었다) · 눈금이 0칸
이면 조용한 초록이 아니라 **RED**(`_columns` 를 `[]` 로 갈아끼워 확인) ·
**변이 ①**(`url,` 삭제 = 착수 전 상태) **RED** · **변이 ②**(탐침을 `hits` 루프 **안**
으로) **RED, 2행**(`url`·`html`) — 계획 6절이 예고한 대로 둘 다 죽는다.

**HTTP 표면**(줄은 안 더했다) — `url` 열 없는 DB 를 실제 서버로 띄워 재니
`/passages` 세 질의가 **500·500·500**, `/search` 200 · 화면 `/` 200. 잰 뒤 서버는
`shutdown()`·`server_close()` 로 죽였고 `pgrep -f websearch.serve` **잔여 0**.

## 범위 (하드 제약 확인)

단위 **603 → 604 OK**(13.671초 · 맨몸·단독 · rc 0) · e2e 는 관련 둘만 먼저 확인
(`search_api_e2e` rc 0 · `hidden_passage_e2e` rc 0), **21종 전수는 e2e phase 몫** ·
`README.md` 의 `단위 603건` → `604건`(`test_readme` 가 즉시 FAILED 로 잡아 줬다) ·
`main` 직접 커밋 0 · `--no-verify`·`--force` 0 · **PR 무접촉(조회 0회)** ·
`docs/specs/` 무변 · `data/crawl.db` sha256 `85c96744…5bda18` **무변**(모든 실측이
임시 디렉터리 사본) · 스키마·마이그레이션·재색인 0 · stdlib 만 ·
**푸시 대조** — 착수 직전 원격이 `a2cc8ad` 로 밀려 있지 않아 먼저 푸시했고
`git ls-remote` 로 대조했다(직전 반복이 빠뜨린 것을 이 반복이 회수했다).

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **브랜치 병합** — 원격 `main` 은 `c0be72f`, 계획 54(PR #9)까지 들어 있다.
   `loop/db-state-invariant` 의 병합은 사람 몫이고 `main` 직접 커밋은 하지 않는다.
   **이 반복도 PR 을 조회조차 안 했다.**

## 정지 사유

없음 — 계획 55 **테스트** 로 이어간다.
