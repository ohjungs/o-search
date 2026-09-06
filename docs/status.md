---
signal: GREEN
phase: plan
step: 0/1
attempt: 0
iteration: 404
updated: 2026-09-07
ctx: 44
night_iterations: 199
night_red: 2
night_retries: 4
plan: digest-strike-sync 계획 70 (계획 phase 완료 · 개발 1/1 대기)
---

## 현재 상태

**계획 70 `digest-strike-sync` 를 열었다 — 계획 phase 완료 · GREEN.**
브랜치 `loop/digest-strike-sync`(기점 `1e17a20` = `origin/main`) ·
계획서 `docs/plan_digest-strike-sync.md` · 스텝 **1개**(개발 1/1) · 설계 없음.
이번 반복은 **계획서와 기록 문서만** 만들었다 — `src/`·`tests/`·`e2e/`·`README.md`
**0줄**.

## 이번 phase 가 산 것

**부기 규약을 재는 자가 없다는 것을 실물에서 셌다.**

`digest ## 다음 계획 후보` 두 절의 목록 줄은 **74개**, 그중 「계획 NN `slug` … 로
열었다」 포인터를 단 줄은 **8개**다. 그 여덟 중 **일곱은 취소선이 있고 하나는 없다** —
`## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 의 `[6]`「`concept.md:<N>` 인용 18건 중
11건은 …」 항목이 계획 68 `spec-citation-anchor` 로 열려 어제 `완료` 로 닫혔는데
(`index.md` 상태 칸) 후보 목록에서는 아직 열린 줄이다. **낡은 줄은 하나 더 있다** —
같은 절의 `[4]`「`is_noindex` 사전 필터가 엔티티 인코딩한 meta 를 놓친다」 항목은 어제
계획 69 가 닫았는데 포인터 문구가 없어 **자가 구조적으로 못 문다**. 손으로 긋고 천장을
계획서 7절에 적었다.

**처방을 등재 전에 네 판 돌렸다**(문자열만 조작 · 저장소 무접촉 · 워킹트리 무변경):

| 판 | 입력 | 결과 |
|---|---|---|
| M1 구멍 | 오늘 실물 두 문서 | **위반 1건**(`spec-citation-anchor`) |
| M2 처방 | 그 `[6]` 줄에 `~~` 를 그은 사본 | 위반 **0** |
| M3 재발 | 다른 취소선 줄에서 `~~` 제거 | **위반 1건** — 다시 운다 |
| M4 오탐 축 | 그 계획 상태를 `완료`→`진행` | 위반 **0** — 진행 중은 안 문다 |

**탐색 1~5순위는 빈손이었다** — 실패 테스트 0 · 린터/타입체커 설정 0개 · 코드 `TODO`
1건은 파서 입력 문자열 안(`tests/test_indexer.py:779`) · `docs/candidates.md`·
`docs/patches/` 부재 · `digest ## 보류 (승인 대기)` 0건. **6순위 목록을 읽다가 목록
«자신» 의 부기 구멍을 골랐다** — 닫힌 항목을 다시 계획하는 것이 아니라서
`rules/discover.md` 5절 중복 방지에 안 걸린다.

## 안 산 것

- **후보 줄의 내용·점수는 안 건드린다** — 열린 58줄(`[9]`1 · `[8]`5 · `[7]`7 · `[6]`12 ·
  `[5]`16 · `[4]`17)은 각자 여는 조건이 따로 있다.
- **포인터 문구를 강제하는 규약은 안 만든다**(YAGNI) — 74줄 중 66줄을 RED 로 만드는데
  그 대부분은 계획으로 열린 적이 없다.
- **가드의 천장은 계획서 7절에 적었다** — 포인터 어미가 달라지면 「조용한 초록」이 된다.
  못 둘(추출기 0 방어 · 실물 하한)로 완화하되 여덟이 일곱으로 주는 것은 못 막는다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
→ Ran 632 tests in 15.842s · OK · rc 0
```

`src/`·`tests/`·`e2e/`·`README.md` **0줄** · `docs/specs/` 무접촉 ·
`data/crawl.db` **무개봉** · 새 의존성·스키마·마이그레이션·재색인 **0** ·
바깥 네트워크 접속 **0** · `main` 직접 커밋 0 · PR #7 무접촉(`gh` 0회).

## 다음

**개발 phase 1/1** — `tests/test_docs.py` 에 `candidate_lines`·`strike_gap` +
`StrikeSyncTest`(실물)·`StrikeGapTest`(합성)를 심어 **RED 1건**을 먼저 보고,
낡은 후보 두 줄(`[6]` 인용 앵커 · `[4]` 엔티티 사전 필터)에 취소선을 긋는다.
완료 기준은 계획서 4절 일곱 개.
