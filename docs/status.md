---
signal: GREEN
phase: 계획
step: 0/1
attempt: 0
iteration: 315
updated: 2026-09-04
ctx: 52
night_iterations: 137
night_red: 2
night_retries: 0
plan: passage-html-column # 계획 54 — 설계 필요(갈림길 둘)
---

# 현재 상태

**계획 54 `passage-html-column` 착수 — 계획서를 썼다.** 다음 phase 는 **설계**다(트리거 둘).
계획서는 `docs/plan_passage-html-column.md`, 브랜치는 `loop/passage-html-column`(기점 `91731e4`).

## 무엇을 여는가

계획 53 이 닫은 것은 「`pages` 테이블이 통째로 없다」 **한 축**이다. `pages` 는 있는데
**`html` 열이 없는** DB 에서는 「DB 상태 판정이 질의 내용에 달렸다」가 글자 그대로 살아 있다.

| 질의 | `html` 열 없는 DB (오늘) | 정상 DB (대조군) |
|---|---|---|
| `/passages?q=김치찌개`(매치 있음) | **500**(`OperationalError: no such column: html`) | 200 · 문단 1건 |
| `/passages?q=zzzznope`(매치 없음) | **200 `[]`** | 200 `[]` |
| `/passages?q=%01`(무토큰) | **200 `[]`** | 200 `[]` |
| `/search?q=김치찌개` | 200 · 결과 1건(무변) | 200 |

소비자가 **같은 순간의 같은 DB** 를 «우리가 터졌다» 와 «근거가 없다» 로 갈라 읽는다.
계획 47 이 `search()` 안에서, 계획 53 이 `passages()` 의 테이블 축에서 닫은 그 원칙이
**같은 함수에서 세 번째로** 나타난 자리다 — 자리가 아니라 **판정의 넓이** 문제라는 신호다.

## 탐색 — 1~5순위 0건, 6순위 `[6]` 채택

단위 **599건 OK**(13.709초 · 맨몸·단독 · rc 0) · 린터·타입체커 설정 **0개** ·
코드 `TODO`/`FIXME`/`HACK` **0**(유일한 hit 는 `tests/test_indexer.py` 의 fixture HTML
문자열 안) · `candidates.md` 없음 · `digest ## 보류` 살아 있는 항목 **0**.

**중복 방지(discover 5절)를 고르기 전에 5곳 전수로 돌렸다** — `index.md` 계획 행 30개 ·
`digest ## 완료` · 활성 계획서 · 보류 · `docs/patches/`(디렉터리 없음). 직전 계획 53 이
비고 마지막 줄에 *"남기는 것: `html` 열이 없는 DB"* 로 **스스로 안 열었다고 적어 둔** 축이다.

**함정 둘을 지나왔다.** ① 점수가 가장 높은 `[8]` 「토크나이저가 못 잡는 세 가지」는
**계획 11 `plan_tokenizer` 가 이미 닫았는데 취소선이 없다** — 그대로 믿었으면 완료된 것을
다시 여는 반복이었다. ② 그 `[8]` 의 남은 갈래(trigram 병행 색인)는 **재색인**이라 이 반복의
제약에 정면으로 걸린다. 계획 53 탐색이 `[6] focus_rule` 에서 겪은 자리와 같다.

## 후보의 서술과 처방을 실행 전에 다시 쟀다 — **이번엔 둘 다 맞았다**

`digest [7]` 「기록된 답을 실행 전에 다시 재라」의 **여섯 번째 적용**이다. 임시 DB 를 만들어
(`store.upsert` → `index_pages` → `pages` 를 `html` 없는 스키마로 재생성) `indexer` 를 직접
불렀다. **저장소의 `data/crawl.db` 는 읽지도 않았다.** 위 표의 500/200/200 이 재현됐고,
처방 자리에서 `SELECT html FROM pages LIMIT 1` 한 줄은 **정상 DB 에서 OK(오탐 0)** ·
고장난 DB 에서 **질의와 무관하게** `OperationalError` 다.

순서도 쟀다 — `html` 열 없음 **+ 옛 색인** → 세 질의 다 `StaleIndexError`,
**+ 색인 전** → 세 질의 다 `[]`, **`pages` 테이블 없음** → 세 질의 다 `NoCrawlDataError`
(계획 53 의 수리가 그대로 선다).

**다만 후보가 적은 «그날의 답 = 500» 을 그대로 받지 않았다.** 이 상태에 닿으려면 사람이
스키마를 손으로 고쳐야 한다(`store`·`indexer` 의 어떤 경로도 `html` 없는 `pages` 를 만들지
않는다) — 후보 자신이 «8점이 아닌 이유» 로 적어 둔 그것이다.

## 설계가 잴 것 — 갈림길 둘

1. **세 질의를 무엇으로 모으나** — A 500(재시도로 안 낫는다 · `serve.py` 0줄) ·
   B 503 `NoCrawlDataError`(계획 53 과 같은 표면 · 계약 표에 줄을 안 더한다) ·
   **C 제품 0줄**(거짓이 된 제품 주석과 테스트 docstring 만 고친다 — ponytail 1칸).
   사양의 *"HTTP 상태 코드가 뜻을 갖는다"* 와 「계약 안정성 > 기능 추가」로 가른다.
2. **판정을 어떻게 넓히나** — ㄱ `SELECT html FROM pages LIMIT 1` 한 줄을 잇는다 ·
   ㄴ `PRAGMA table_info` 로 이름을 본다 · ㄷ 두 가드를 합치고 예외 **메시지**로 축을 가른다
   (마지막은 sqlite 판에 계약을 건다).

## 범위

제품 diff 예상 **한 파일**(`src/websearch/indexer.py`) · `serve.py` **0줄**(두 갈래가 이미 있다) ·
스키마·마이그레이션·재색인 **0** · 새 의존성 **0**. TDD 의 RED 는 새로 짓는 것이 아니라
`tests/test_serve.py` 의 `TestPassagesWithoutHtmlColumn` 두 단언을 **뒤집는 것**이다 —
그 테스트가 docstring 에 *"천장을 옮기는 날 이 테스트가 빨개져 「그 갈림을 알고 바꾼다」가
되게 하려고 잰다"* 고 적어 뒀다.

**기점을 `main` 으로 안 잡았다** — `git ls-remote origin` 으로 다시 읽어 보니 원격 `main` 은
`687a1598…`(계획 47)이고 `loop/passage-db-state` 는 `91731e47…` 로 로컬 HEAD 와 같다.
고칠 코드가 **계획 53 이 심은 가드 그 자체**라 `main` 에서 따면 대상이 없고, `README.md` 의
`단위 599건`·`e2e 시나리오 21종` 단언도 이 사슬에서만 참이다. **PR #7 은 조회만 하지 않았다 —
무접촉이다.**

## 행동

**다음은 설계 phase.** 갈림길 둘을 표로 가르고 특히 안 C(제품 0줄)를 진지하게 잰다 —
도달 조건이 낮은 고장이라 «주석과 docstring 만 고치고 닫는다» 가 정답일 수 있고,
그것도 이 계획의 정상 종료다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **PR #7**(`loop/merge-48-50` → `main`)이 **OPEN·미병합**이고 `loop/hidden-passage` ·
   `loop/focus-ring-combinator` · `loop/passage-db-state` · `loop/passage-html-column` 이
   그 뒤에 쌓여 있다. 병합은 사용자가 처리한다 — 이 반복도 **PR 무접촉**이다.

## 정지 사유

없음.
