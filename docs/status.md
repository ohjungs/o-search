---
signal: GREEN
phase: review
step: 1/1
attempt: 0
iteration: 407
updated: 2026-09-07
ctx: 58
night_iterations: 200
night_red: 2
night_retries: 4
plan: digest-strike-sync
---

## 현재 상태

**계획 70 `digest-strike-sync` 리뷰 phase 1/1 완료 · GREEN.**
브랜치 `loop/digest-strike-sync` · 계획서 `docs/plan_digest-strike-sync.md` ·
다음은 **e2e phase 1/1**(계획의 마지막 phase).

## 이번 phase 가 산 것

**패스 A 를 구조로 돌렸다** — `claude -p` 별도 세션에 diff 와 수정 파일만 주고
계획·설계·상태 문서는 주지 않았다. 받은 지적 1건(`## ` 만 절을 끊어 `###`·H1 이
범위를 안 끈다)은 **80점 미만으로 버렸다**: 실물 `digest.md` 에 `###` 는 **0개**이고,
`###` 는 후보 절의 **하위** 절이라 계속 세는 것이 오히려 맞으며, 후보 절 뒤 H1 재출현은
`DocHeadTest` 가 존재하는 이유인 구조 붕괴라 그 가드가 먼저 운다. 형제 `done_section`
도 같은 관용구(`## ` 로만 끊는다)를 쓴다 — 바꾸면 두 헬퍼가 갈린다.

**패스 B 가 낡은 수치 하나를 잡았다 (자동 수정)** — `STRIKE_POINTER_FLOOR` 주석이
「오늘 실물의 포인터 수는 9다」인데 **실측 10**이다(개발 phase 가 `[4]` 줄에 포인터를
채워 하나 늘었다). 하한 상수는 **9로 두었다** — 값 축에 붙이면 문구가 달라지는 날도
물지만 후보 절을 정리하는 날 거짓 RED 다. 그 갈림은 등재했다.

**주석의 수치를 말로 낮추는 대신 실측으로 샀다** — 「M7·M8 이 638건을 통째로 통과했다」는
`tests.test_docs` 37건만 돌린 근거였다. 가드를 심기 **전** 버전(`HEAD~1`)을 사본에 넣고
두 변이를 각각 **전수로** 돌려 `Ran 638 · OK` 를 실제로 봤다.

**계획 7절의 천장을 처방 실측과 함께 등재했다** — 처방 A(백틱 슬러그를 통째로 세어
대조)는 오늘 실물에서 엄격 10 대 느슨 31, **오탐 21건**이라 그대로는 못 쓴다.
처방 B(하한을 실측치에 붙인다)가 답이고 여는 조건까지 적었다.

## 안 산 것

**제품 `src/`·`e2e/` 0줄** · 단언 무변(주석만) · 하한 상수 무변 · 후보 줄의 내용·점수
무접촉 · `rules/*.md`·`docs/specs/` 무접촉.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 639 tests · OK · rc 0
```

건수 **639 무변**(주석·문서만 고쳤다) · `README.md:104` 639 로 동기 유지 ·
`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** ·
새 의존성·스키마·마이그레이션·재색인 **0** · `main` 직접 커밋 0 · PR #7 무접촉.

## 다음

**e2e phase 1/1** — 이 계획의 산출물은 제품이 아니라 **문서 가드**라 크롤→색인→서버를
관통시킬 것이 없다. 대신 「실제 루프가 후보를 닫는 편집을 했을 때 이 자가 실물
파이프라인(전수 러너)에서 운다」를 사본에서 관통시킨다 — 계획 60·61 의 e2e 가 같은
자리에서 쓴 방식이다. 끝나면 계획 70 DONE · `main` 병합.
