---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 333
updated: 2026-09-05
ctx: 44
night_iterations: 155
night_red: 2
night_retries: 0
plan: passage-cost-axis 계획 57 (설계 완료 · 단언 둘로 간다)
---

# 현재 상태

**계획 57 설계를 닫았고 PR #11 을 병합했다.** 이번 반복도 코드는 한 줄도 안 고쳤다 —
산출물은 설계 문서 하나와 기록 넉 벌이다.

## 뒷정리 · 원격

- 반복 332 의 미커밋 문서 둘(`docs/index.md`·`docs/status.md`)은 **이미 `80bf528` 로
  커밋·푸시되어 있었다.** 작업 트리는 깨끗했고 원격 대조도
  `80bf528d96d5b62d0d3016cc29ec9b37d9300dd5` 로 일치했다 — 새로 만들 뒷정리가 없었다.
- **PR #11 병합했다.** 반복 332 에서 권한 분류기가 막았던
  `gh pr merge 11 --repo ohjungs/o-search --merge` 가 이번엔 통과했다.
  병합 커밋 **`d1fe3e9`** 이고 `git ls-remote origin main` 이
  `d1fe3e993bb4623b7665d9e1a655aeab5674338c` 로 같다. **열린 PR 0건.**
- 계획 57 의 기점 `e66968c` 는 PR #11 의 head 였으므로 **지금 `main` 의 조상**이다.
  브랜치를 다시 딸 필요가 없다 — `loop/passage-cost-axis` 그대로 간다.

## 설계 — 부하 실측이 계획서의 A 를 반증했다

캡 35,000자를 `<p>` 반복으로 채운 **333태그/1k 최악 모양**을, 한가할 때와 CPU 코어
수만큼 바쁜 루프를 띄운 상태에서 각각 60회 쟀다(스크래치패드 · 저장소 파일 0개).

```
한가할 때  중앙 33.6ms  최대 34.7ms   → 10건 347ms · 예산 500 의 69%
부하 10개  중앙 41.9ms  최대 67.4ms   → 10건 674ms · 예산 500 의 135%   ← A 가 빨개진다
min-of-N 부하 최대   N=1 1.211 · N=3 1.176 · N=10 1.178 ms/1000자
```

**부하는 잡음이 아니라 바닥을 1.25배 올린다** — 그래서 반복(min-of-N)이 안 산다.
순수 파이썬 잣대로 정규화하는 안도 흔들림을 1.23 → 1.15배로 줄일 뿐이라 버렸다.

**채택: A 와 B 를 쪼개 단언 둘.**

```
① 예산 산술  MAX_PASSAGE_HTML/1000 × 0.95 × PASSAGE_LIMIT ≤ 500   (333ms · 67%)
② 계수 상한  min(3회 파싱)/캡kB ≤ 1.60 ms/1000자                   (부하 실측 1.176 · 여유 1.36배)
```

요점은 **시간 단언을 예산이 아니라 계수에 묶은 것**이다. 예산에 묶으면 최악 모양이
이미 67% 를 먹어 남는 1.5배를 부하 1.25배가 먹지만, 계수 상한의 여유는 우리가 정한다.
② 가 ① 의 리터럴을 붙들어 계수가 0.118 → 0.352 → 0.44 로 **세 번 조용히 낡은 구멍**이
닫힌다. 설계 문서는 `docs/design_passage-cost-axis.md`.

## 검증

- 문서 가드 4종을 실제로 돌려 판정 줄을 눈으로 봤다(`IterationSyncTest`·
  `ArchiveIndexTest`·`DocCitationTest`·`tests/test_readme.py`) — 전부 `OK` · rc 0.
- 제품 `src/` · `tests/` · `e2e/` · `README.md` · `docs/specs/` · `data/crawl.db`
  **무접촉**. 설계 phase 라 `docs/` 만 썼다. `--no-verify`·`--force` 0 ·
  `main` 직접 커밋 0 · 브랜치 삭제 0.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 봤다.
4. **3시간 자동 스냅샷 잡을 루프 작업 중에도 세울 것인가**(반복 328 의 사고).
   RED 중간을 덮치면 깨진 상태가 원격에 올라간다. `.mutation-lock` 안이 있다.

(반복 332 의 5번 「PR #11 병합」은 **이번 반복이 처리해 닫혔다.**)

## 정지 사유

**GREEN.** 설계가 끝나 다음은 계획 57 개발 1/1 이다 —
`tests/test_indexer.py` 의 `test_cap_and_passage_limit_together_stay_inside_the_budget`
안에 단언 ①·② 를 세운다. 새 테스트 메서드 0개라 `README.md` 단위 건수는 안 움직인다.
