---
signal: GREEN
phase: dev
step: 1/1
attempt: 0
iteration: 405
updated: 2026-09-07
ctx: 44
night_iterations: 200
night_red: 2
night_retries: 4
plan: digest-strike-sync
---

## 현재 상태

**계획 70 `digest-strike-sync` 개발 phase 1/1 완료 · GREEN.**
브랜치 `loop/digest-strike-sync` · 계획서 `docs/plan_digest-strike-sync.md` ·
다음은 **테스트 phase 1/1**.

## 이번 phase 가 산 것

**닫힌 후보에 취소선이 그어졌는지를 재는 자를 세웠다.** `tests/test_docs.py` 에
`candidate_pointers`·`strike_gap` 헬퍼(`iter_gap`·`step_gap` 옆)와 실물
`StrikeSyncTest`(2) · 합성 `StrikeGapTest`(4). 대조하는 두 쪽은 `digest` 후보 줄의
취소선 ↔ `index.md` 계획 행의 **상태 칸**이라 거울이 아니다.

**RED 를 먼저 봤다** — 취소선을 긋기 전 `tests.test_docs` 만 돌려 `failures=1`,
자리는 계획서가 지목한 `spec-citation-anchor` 그대로다(완료 기준 1).

**숫자 하나를 정정했다** — 포인터 줄은 8이 아니라 **9**(취소선 8 · 없음 1)다. 후보 두
절의 `열었다` 11자리 중 둘은 「계획 49 범위 밖이라 **안** 열었다」 부정문이고, 포인터
앞의 **백틱 슬러그 요구**가 그 둘을 가른다. RED 건수와 자리는 계획서와 같다.

**취소선은 두 줄**(`[6]` 인용 앵커 = 계획 68 · `[4]` 엔티티 noindex = 계획 69).
뒤엣것은 포인터 자체가 없어 가드에 안 보이던 자리라 포인터도 함께 채웠다 —
계획서 7절의 천장(「여덟이 일곱으로 주는 것은 못 막는다」)의 실물 표본이다.

## 안 산 것

**후보 줄의 내용·점수는 안 건드렸다**(열린 58줄) · **포인터 문구를 강제하는 규약은 안
만들었다**(YAGNI) · **`~~` 가 어디서 닫히는지는 안 잰다**(거울) · digest 의 다른 네 절
무접촉 · `rules/*.md`·`docs/specs/` 무접촉.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 638 tests · OK · rc 0
```

632 → **638**(새 메서드 6개와 정확히 같다) · `README.md:104` 638로 동기 ·
`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** ·
새 의존성·스키마·마이그레이션·재색인 **0** · `main` 직접 커밋 0 · PR #7 무접촉.

## 다음

**테스트 phase 1/1** — 변이로 판정을 무력화해 본다(포인터 정규식 사망 · 상태 칸 비교
삭제 · 취소선 검사 삭제). 하한 못 `STRIKE_POINTER_FLOOR` 가 첫째를 실제로 죽이는지가
초점이고, 변이는 저장소 밖 `mktemp -d` 사본에서만 돈다.
