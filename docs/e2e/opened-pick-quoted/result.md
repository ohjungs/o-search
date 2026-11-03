# e2e 결과 — `opened-pick-quoted` (계획 133)

- **일시**: 2026-11-04 반복 816 (무인 night)
- **트리**: 사본 `/tmp/e2e133.LEmfkV` — `tests/ src/ docs/ scripts/ e2e/ README.md` 만 복사.
  `.git`·`data/` 는 **안 복사했다**(그 대가로 범위 가드 **2건이 건너뛴다** — 게이트 ⑱ ㉢ 의 선례).
- **명령**: `PYTHONPATH=<사본>/src python3 -m unittest discover -b -s <사본>/tests -t <사본>`
  — `-s`·`-t` 를 **둘 다** 사본으로 준다. 안 주면 cwd 가 `sys.path[0]` 에 들어가
  `tests` 패키지가 **원본 트리**로 풀린다(계획 131 `[E131-1]`).
- **판정 5/5 + 반증 1.**

## S0 — 사본 기준선

`Ran 1107 tests … OK (skipped=2)` · 33.9s. 사본이 원본과 같은 판정을 낸다.

## S1 — 따옴표 꼴 완료 행 + 취소선 없는 후보 줄 → **빨강**

사본의 `docs/digest.md` 에서 그 한 줄만 **계획 133 착수 시점 상태로 되돌렸다**
(`git show 9bdfff0:docs/digest.md` 의 원문 줄로 치환 — 손으로 쓰지 않았다).

```
FAIL: test_opened_candidates_are_struck_through (tests.test_docs.OpenSyncTest)
AssertionError: '집어간 후보에 취소선이 없다 — index.md `plan_mutant-anchor-unique` 는
`완료` 인데 digest 후보 줄 「변이 하네스의 「심긴 것을 먼저 단언한다」 가 `- ~~` 로
시작하지 않는다'
Ran 1107 tests … FAILED (failures=1, skipped=2)
```

**슬러그와 제목을 둘 다 댄다** — 사람이 어느 줄을 그어야 하는지 바로 안다. 실패는 **딱 1건**.

## S2 — 취소선만 다시 그으면 → **초록**

같은 트리에서 그 줄만 되돌려 놓으니 `Ran 1107 … OK (skipped=2)` · 33.5s.
**첫 판은 `FAILED (errors=1)` 에 63.7s 였다** — 아래 「곁다리」 참조.
재판 1판 + 확인 3판 = **4판 연속 OK rc=0** (33.5 · 33.5 · 33.7 · 33.7s).

## S3 — 백틱으로 닫은 기존 꼴 **판정 불변** (회귀)

조임판(완화 전) 추출 **10** · 완화판 **12** · `조임판 ⊆ 완화판` **True** · **잃은 것 0**.
넓히면서 기존 열을 모집단에서 떨어뜨리지 않았다.

## S4 — 반증: 완화 **한 자리만** 되돌린다 (존재 증명)

S1 의 트리(취소선 없는 상태)에서 `[`」]?` → ```?`` 한 자리만 되돌렸다. 같은 트리·같은 명령.

```
open_gap: None          ← 실물 적중이 «사라졌다»
FAILED (failures=3, errors=1, skipped=2)   ← 남은 빨강은 합성 못 셋뿐
```

**`OpenSyncTest` 가 조용해진다.** 즉 사흘간의 침묵은 **바로 그 문자 클래스**가 원인이고,
사람이 실수로 그 한 자리를 되돌리면 자가 **다시 눈을 감는다**. 합성 못 셋
(`..._quoting_the_section_name_is_counted` · `..._inner_pair_matches_by_its_prefix` ·
`..._pick_regex_reads_a_quoted_section_name`)이 그 되돌림을 각각 문다.

## 곁다리 — 간헐 빨강이 이 밤에 **두 번** 났고 벽시계가 범인을 좁혔다

1. 반복 814 변이 M6: 전수 판이 `2`「재지 못했다」 → 같은 변이 재판 `죽음 rc=0`.
2. 반복 816 S2 첫 판: `FAILED (errors=1)` · **63.7s** → 재판·확인 4판 전부 `OK` · **33.5~33.7s**.

**두 번 다 범인 줄을 못 봤다** — 1번은 `-b` 가 삼켰고 2번은 `tail` 로만 봤다.
다만 2번이 수를 하나 줬다: **63.7 − 33.6 ≈ 30.1초**. 후보 줄이 지목한
`communicate(timeout=30)` 의 상한과 **같은 값**이라 그 자리라는 쪽으로 좁는다(단정은 아니다).
**처방이 조항이면 또 놓친다** — 밤이 전수를 돌릴 때 **항상 로그로 받는 것**이 기제다.
