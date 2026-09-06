---
signal: GREEN
phase: 개발
step: 1/1
attempt: 0
iteration: 372
updated: 2026-09-06
ctx: 46
night_iterations: 187
night_red: 2
night_retries: 4
plan: archive-scope-cover 계획 64 (개발 1/1 완료 · 완료 기준 9/9 · 다음은 테스트)
---

## 현재 상태

**계획 64 `archive-scope-cover` 개발 1/1 완료 — 완료 기준 9/9 · 다음은 테스트.**
`tests/test_docs.py` 에 `ArchivePatternTest` 를 `ArchiveMatchTest` 바로 위에 세웠다
(**한 파일 39줄 추가 · 리터럴 아홉 + 메서드 둘**). `ARCHIVE` 가 혼자 정하던 「무엇을
검사 대상에서 뺄지」가 이제 실물 파일 목록이 아니라 **합성 리터럴**에 붙들린다.

## 검증 — RED 를 이 반복에서 직접 봤다

`rules/dev.md` 0절대로 테스트를 먼저 넣고 돌렸다. 첫 줄이 빨갛게 왔다 —
`AssertionError: Tuples differ: (620, 21) != (622, 21) : README 의 (단위, e2e) 숫자가
실제와 다르다`(`test_readme.test_verification_counts_match_reality`). 계획 63 은 메서드가
안 늘어 이 줄이 무접촉이었지만 이번엔 **설계대로 즉시 울었고**, 같은 커밋에서
`README.md:104` 를 620 → **622** 로 고쳤다.

**변이 판정은 전부 저장소 밖 `mock.patch.object` 하네스**(코드는 메모리 · 워킹트리
`git status --porcelain` 빈손 · 전수를 변이마다 다시 돌렸다).

| 기준 | 변이 | 결과 |
|---|---|---|
| 1 | M3 `$` 제거 | **1** — `NOT_CAUGHT` 의 `history_001.md.bak.md` |
| 2 | M4 `re.I` | **1** — `HISTORY_001.MD` |
| 3 | M5 `[0-9]+`→`[0-9]*` | **1** — `history_.md` |
| 4 | M11 `design_history` 이름 제거 | **1** — `CAUGHT` 의 `design_history_046.md` |
| 5 | M10 접두 확대 | **4**(`DocCitationTest` 1 그대로 + 새 단언 3) |
| 5 | M1 · M2 · M8 (`APPEND_TARGETS`+`CITATION`) | **1 · 2 · 3** — 어제와 같다 |
| 5 | 계획 63 앵커 다섯(A1a·A1b·A2·A3·A4) | **각 1** — 무회귀 |
| 6 | M0 무변이 대조군 | **0** — 오탐 0 |
| — | P 양성 대조 `^ZZZ_[0-9]+\.md$` | **4** — `CAUGHT` 셋이 전부 죽어 배선 증명 |

기준 7: 전수 **맨몸** `Ran 622 tests in 15.461s` · `OK` · **rc 0** 이고 `README.md` 의
「단위 622건」이 실제와 같다. 기준 8: `git diff --stat ba53783 HEAD -- src/ e2e/
docs/specs/ data/` **빈손** · `data/crawl.db` sha256 `85c96744…5bda18` 무변 · 재색인 0.
기준 9 는 계획 phase 가 `digest [5]` 에 정정을 적어 이미 닫혔다.

**만진 파일은 둘뿐** — `tests/test_docs.py`(+39) · `README.md`(+1 −1).

## 다음

**테스트 phase — 스텝 1/1.** 새 단언이 놓친 갭을 찾는다. 눈여겨볼 자리 둘:
① `ARCHIVE` 는 `.match()` 로만 불려 `^` 가 잉여인데 새 단언도 `assertRegex`(=`search`)라
**`^` 를 지우는 M6 은 여전히 등가 변이**다 — 재는 쪽이 아니라 지우는 쪽이 답이라고 계획서
5절이 이미 적었다. ② `APPEND_TARGETS` 축은 계획서 5절이 이유를 적어 **닫아 두었다**
(해로운 방향은 `CITATION` 파생이 이미 1·2·3건으로 죽인다 — 다시 열지 않는다).

## 한도

- 병합은 사람 몫이다 — 계획 57~64 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`). 워킹트리에는 변이 열여섯
  판 내내 계획이 허용한 두 파일 말고 아무것도 안 생겼다.
- **`night_iterations` 는 187 그대로 둔다** — 이 반복은 대화형이라 야간 예산을 안 쓴다.
- `docs/digest.md` 는 **200줄 정각** 유지 — 이 반복은 `digest` 무접촉이다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_065.md` 다.
