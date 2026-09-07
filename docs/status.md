---
signal: GREEN
phase: test
step: 1/1
attempt: 0
iteration: 406
updated: 2026-09-07
ctx: 25
night_iterations: 200
night_red: 2
night_retries: 4
plan: digest-strike-sync
---

## 현재 상태

**계획 70 `digest-strike-sync` 테스트 phase 1/1 완료 · GREEN.**
브랜치 `loop/digest-strike-sync` · 계획서 `docs/plan_digest-strike-sync.md` ·
다음은 **리뷰 phase 1/1**.

## 이번 phase 가 산 것

**변이 9판을 저장소 밖 사본에서 돌려 9/9 를 죽였다.** 계획서가 지목한 여섯(취소선
떼기 · 절 제목 오타 · 포인터 정규식 사망 · 상태 칸 비교 삭제 · 취소선 검사 삭제 ·
미등재 검사 삭제)은 처음부터 전부 죽었다. 완료 기준 3(재발)과 5(추출기 0)이
실물에서 확인됐다.

**갭 탐색이 살아남은 변이 둘을 찾았다** — 추출기의 **범위를 넓히는** 쪽
(절 자르기 제거 · 목록 줄 요구 제거)은 638건을 통째로 통과했다. 하한 못은 범위가
**좁아지는** 쪽만 막고, 넓어지면 남의 절과 본문 산문이 후보로 세어져 **거짓 RED** 가
된다 — 조용한 초록의 반대쪽 실패다. 실물에 표본이 없어 아무도 안 물었다.
중요도 8 로 보고 합성 단언 **하나**(`test_only_candidate_list_lines_are_counted`)로
둘 다 물게 했다. 재확인 결과 M7·M8 각각 그 하나만 죽인다.

**README 건수 가드가 즉시 울었다** — 639건이 됐는데 `README.md:104` 가 638이라
전수가 `FAILED (failures=1)`. 계획 62 가 세운 자다.

## 안 산 것

**제품 `src/`·`e2e/` 0줄** · 후보 줄의 내용·점수 무접촉 · 포인터 문구 강제 규약
없음(YAGNI) · digest 의 다른 네 절 무접촉 · `rules/*.md`·`docs/specs/` 무접촉.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 639 tests · OK · rc 0
```

638 → **639**(새 메서드 1개와 정확히 같다) · `README.md:104` 639로 동기 ·
`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** ·
새 의존성·스키마·마이그레이션·재색인 **0** · `main` 직접 커밋 0 · PR #7 무접촉.
변이는 전부 `mktemp -d` 사본에서만 돌았고 워킹트리는 무변경이었다.

## 다음

**리뷰 phase 1/1** — 백지에서 diff 를 다시 읽는다. 초점은 ① 이 자가 거울이 아닌지
(대조하는 두 쪽이 다른 문서인가) ② 하한 못 9 가 후보를 닫을 때마다 손이 가는
비용을 만들지 않는지 ③ 남은 천장(포인터 문구가 어미만 달라지면 여덟이 일곱으로
주는 것은 못 막는다)을 `digest` 후보에 등재했는지.
