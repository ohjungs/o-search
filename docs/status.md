---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 316
updated: 2026-09-04
ctx: 62
night_iterations: 138
night_red: 2
night_retries: 0
plan: passage-html-column # 계획 54 — 설계 완료(안 A · `LIMIT 0`)
---

# 현재 상태

**계획 54 `passage-html-column` 설계 1/1 — `docs/design_passage-html-column.md`.**
제품 `src/` **0줄**(설계 phase 는 코드를 안 심는다). 다음 phase 는 **개발**이다.

## 결정 — 제품 한 줄

`indexer.passages()` 안, 계획 53 이 심은 `sqlite_master` 가드 **직후**·`hits` 루프 **앞**에
`db.execute("SELECT html FROM pages LIMIT 0")` **한 줄**. 열이 없으면 sqlite 가 준비 단계에서
`OperationalError` 를 질의와 무관하게 한 번 내고, `serve.do_GET` 의 `except Exception` 이
이미 그것을 500 으로 옮긴다. **`serve.py` 0줄 · `README.md` 0줄 · 새 예외 0개 ·
스키마·마이그레이션·재색인 0 · 시그니처 무변.** 제품 diff 는 한 파일이다.

## 갈림길 1 → 안 A(500). 결정한 것은 「다시 돌리면 낫나」 한 줄이다

계획서가 A(500) · B(503) · C(제품 0줄) 셋을 열었다. **B 를 버린 근거는 새로 잰 것이다**
(반복 316 · 임시 DB · `data/crawl.db` 는 사본으로만 읽었다):

| 고장난 DB 에 처방을 해 봤다 | 결과 |
|---|---|
| `store.Store(db)` 재생성 | **열이 안 살아난다**(`SCHEMA` 가 `IF NOT EXISTS`) · 남은 열 `['url','status']` |
| 이어지는 `store.upsert()` | `OperationalError: table pages has no column named html` |
| `indexer.index_pages()` | `OperationalError: no such column: html` |

**크롤도 색인도 그 DB 에서 죽는다.** 503 «색인이 아직 준비되지 않았다» 는 사양 5 와
`README.md` 의 «색인을 다시 돌리면 낫는 상태» 정의에 정면으로 어긋나고, 503 을 보고
재시도 루프에 든 인프라는 **영원히 안 낫는 것을 계속 두드린다**. C 는 거짓 주석만
참으로 바꿀 뿐 「판정이 질의 내용에 달렸다」를 **세 번째로** 남긴다 — A 와의 차이가
한 줄인데 그 한 줄이 사양 5 를 지킨다. `README.md` 는 이미 *"그 밖의 오류에는 500"*
이라 **0줄**이다.

## 갈림길 2 → `LIMIT 0`. 계획서 후보(`LIMIT 1`)가 가장 비쌌다

1000행·행당 10,426바이트 html, 200회 평균:

| 탐침 | 정상 DB | 고장 DB | 비용 |
|---|---|---|---|
| `SELECT html FROM pages LIMIT 1`(계획서 후보) | OK · 오탐 0 | `OperationalError` | 0.0128 ms |
| **`SELECT html FROM pages LIMIT 0`** | **OK · 오탐 0** | **`OperationalError`** | **0.0016 ms** |
| `SELECT html FROM pages WHERE 0` | OK · 오탐 0 | `OperationalError` | 0.0015 ms |
| `PRAGMA table_info(pages)` | 행을 훑음 | 판정을 **직접 써야** | — |
| (대조) 오늘의 `sqlite_master` 가드 | 통과 | **통과해 버린다** | 0.0024 ms |

**`LIMIT 1` 이 8배 비싼 이유가 결론이다** — 열 이름만 물으면 되는데 html 본문을 한 행
통째로 읽는다. `LIMIT 0` 은 행을 하나도 안 읽고 같은 판정을 낸다.
`PRAGMA` 는 «없다» 를 우리가 예외로 번역해야 해 판정이 한 벌 는다(계획 47 역행).
**계획서 3절이 걱정한 「예외 메시지 문자열 비교」는 안 일어난다** — 테이블이 통째로 없는
DB 는 위쪽 `sqlite_master` 가드가 먼저 `NoCrawlDataError` 를 내고 끝난다. 순서가 대신한다.

## 가장 위험한 가정을 깼다 — 일곱 상태 × 세 질의

제안 계약을 `src/` **밖에** 그대로 복제해(추가되는 줄 하나만 다르다) 전수로 쟀다.

| DB 상태 | 오늘 | 제안 |
|---|---|---|
| 정상 | 200·200·200 | **200·200·200** (오탐 0) |
| `html` 열 없음 | **500·200·200** | **500·500·500** ← 갈림 닫힘 |
| `pages` 없음 · 옛 색인 · `html`없음+옛색인 | 503·503·503 | 503·503·503 (무변) |
| 색인 전 | 200·200·200 | 200·200·200 |
| `html` 열 없음 + 색인 전 | 200·200·200 | **500·500·500** ← 알고 바꾼다 |

우선순위는 오늘 그대로다(없는 DB → 옛 색인 → 창고 없음 → **열 없음 500** 이 맨 뒤).
고장난 DB 의 `/search` 는 세 질의 모두 무변(2·0·0) — 완료 기준 5 를 지킨다.
마지막 행은 **색인을 돌리면 낫는 것이 아니라 색인이 죽는** DB 라 500 이 참인 쪽이다.

**대조군의 한계를 그대로 적는다** — `data/crawl.db` 사본은 `pages` 행이 **2건**뿐이라
다섯 질의 전부 오늘·제안 모두 0건으로 같았다(동일=True). **오탐 0 을 이 코퍼스가
증명하지는 못한다.** 붙드는 것은 **599건 OK**(13.352초 · 맨몸·단독 · 반복 316 재측)와
개발이 더할 정상 DB 단언이다. 실코퍼스 지연 증분 `-0.001 ms`(`-0.32%`, 잡음 안).

## 행동

**다음은 개발 phase.** RED 는 새로 짓는 것이 아니라 `tests/test_serve.py` 의
`TestPassagesWithoutHtmlColumn` 을 **뒤집는 것**이다 — 무매치·무토큰 두 질의를 500 으로,
클래스 docstring 의 «천장은 500/200 갈림» 진술을 고친다. 같은 DB 의 `/search` 200 단언은
구현 **전에도** 초록이어야 한다(가드가 `_connect()` 로 올라가는 것을 붙드는 유일한 자리).

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` · `loop/passage-html-column` 이
   그 뒤에 쌓여 있다. 병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
