---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 374
updated: 2026-09-06
ctx: 52
night_iterations: 187
night_red: 2
night_retries: 4
plan: archive-scope-cover 계획 64 (리뷰 1/1 완료 · low 1건 자동 수정 · 다음은 e2e)
---

## 현재 상태

**백지 패스가 지적 하나를 냈고 그 자리에서 고쳤다 — low · 신뢰도 100 · 판정 0줄 무변.**
새 클래스 docstring 이 `DocCitationTest` 를 「**아래**」라고 가리키는데 실제로는 **위**다
(`tests/test_docs.py:233` vs `522`). 바로 밑의 `ArchiveMatchTest` 가 같은 관용구를
「**위** 검사는 자기를 못 잰다」로 쓰고 있어 **방향만 뒤집힌 복사**다. critical/high **0건**
이라 개발 phase 로 안 돌아간다.

## 검증 — 앞 phase 가 「했다」고 적은 것을 직접 다시 걸었다

계획·status 를 열기 전에 diff 만 보는 패스 A 를 먼저 끝냈고, 그다음 대조했다.
변이는 전부 저장소 밖 `mock.patch.object`(코드는 메모리에서만) ·
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 동반.

| 변이 | 반복 373 이 적은 값 | 리뷰 재측 | 죽은 자리 |
|---|---|---|---|
| M0 무변이 대조군 | 0 | **0** | 오탐 0 |
| M3 `$` 제거 · M4 `re.I` · M5 `[0-9]*` | 1·1·1 | **1·1·1** | `ArchivePatternTest.test_pattern_leaves_live_docs` |
| M11 `design_history` 제거 | 1 | **1** | `…test_pattern_catches_archive_names` |
| M10 `_[0-9]+`→`.*` | 4 | **4** | `DocCitationTest` + 새 단언 |
| P 양성 대조 `^ZZZ_[0-9]+\.md$` | 4 | **4** | `CAUGHT` 셋 + `DocCitationTest` |
| M6 `^` 제거 · G3 `\.`→`.` · G4 순서 | 0·0·0 | **0·0·0** | 등가 — 아래에서 따로 판정 |

**여덟 줄이 한 건도 안 움직였다.** 전수는 재측 열 판 내내 `Ran 622` 로 같았다.

**등가 셋은 건수가 아니라 논거를 다시 걸었다 — 셋 다 성립한다.**
`ARCHIVE` 의 소비자는 `tests/test_docs.py:238` `ARCHIVE.match(path.name)` **하나뿐**이다.
① **M6**: `.match()` 가 위치 0에 앵커하므로 `^` 는 잉여다. ② **G3**: 순회가 `DOCS.glob("*.md")`
(같은 줄 237)라 `md` 앞 글자는 **언제나 점**이고, 점이 아닌 입력은 도달 불가다. ③ **G4**:
`^` 뒤 세 대안은 접두어(`plan_`·`design_`)가 갈려 **서로 배타**라 순서가 결과를 못 바꾼다.
셋 다 「구멍이 아니라 등가」가 맞고, 답은 재는 것이 아니라 지우는 것이다.

## 앞 phase 가 넘긴 판단 둘 — 둘 다 「안 연다」

① **`assertRegex`(=`search`) vs 제품 `.match()`.** 술어를 맞추지 않는다. `^` 가 붙어 있는
동안 둘은 **같은 함수**이고, 갈리는 유일한 경우는 `^` 를 지웠을 때인데 그것이 바로 M6 —
제품에서 등가인 변이다. 즉 술어를 맞춰도 **새로 죽는 변이가 0** 이라 값이 없다
(`severity.md` 4절 「이미 충분히 덮는 단언을 더 조일 수 있다」). 다만 status 가 적어 둔
「시험이 제품보다 엄격한 쪽」은 절반만 맞다 — `assertNotRegex` 는 엄격한 쪽이지만
`assertRegex` 는 **느슨한** 쪽이다. 오늘 값이 같은 이유는 엄격도가 아니라 `^` 다.
② **등가 셋을 지우는 편집.** 안 연다 — 직교 편집이고 계획 64 밖이다(계획서 5절).

## 계획 대조 (패스 B)

계획서 4절 완료 기준을 직접 다시 쟀다 — `ArchivePatternTest` 2메서드 · `CAUGHT` 3 ·
`NOT_CAUGHT` 6 · 배선 증명(P 가 `DocCitationTest` 를 죽인다) · 제품 `src/` **0줄** ·
`README.md:104` **622** = 실측 622 · 만진 파일 둘(`tests/test_docs.py`·`README.md`) ·
`git diff --stat` 에 `docs/specs/`·`data/`·`src/`·`e2e/` **0건**. 전부 참이다.

**전수 판정 줄(맨몸, 리다이렉션 0):** `Ran 622 tests in 15.828s` · `OK` · **rc 0**.

## 다음

**e2e phase — 스텝 1/1.** 이번 계획은 문서 검사 상수의 단위 시험이라 새 e2e 파일을
안 만든다고 계획서 5절이 적어 뒀다 — e2e 는 21종 전수 rc 0 과 완료 기준 대조가 몫이다.

## 한도

- 병합은 사람 몫이다 — 계획 57~64 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`). 워킹트리에 남은 것은
  이번 지적의 한 글자 수정과 문서 셋뿐이다.
- **`night_iterations` 는 187 그대로 둔다** — 이 반복은 대화형이라 야간 예산을 안 쓴다.
- `data/crawl.db` 무변경 · 재색인 0 · `docs/specs/` 읽기만 · 의존성 추가 0(stdlib).
- 회전은 이번에도 없다 — `history_current.md` 는 **292줄**(항목 9)로 상한 300 아래다.
  **다음 반복이 넘긴다** — e2e phase 가 append 하기 전에 `history_065.md` 로 회전한다.
