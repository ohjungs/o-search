---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 373
updated: 2026-09-06
ctx: 46
night_iterations: 187
night_red: 2
night_retries: 4
plan: archive-scope-cover 계획 64 (테스트 1/1 완료 · 8점 이상 갭 0 · 다음은 리뷰)
---

## 현재 상태

**계획 64 `archive-scope-cover` 테스트 1/1 완료 — 8점 이상 갭 0 · 코드 0줄 추가 ·
다음은 리뷰.** `rules/test.md` 3절 일곱 카테고리를 이번 변경(`ArchivePatternTest` +
`ARCHIVE` 축)에 대조했고, 새로 쓴 것 없이 **재는 것으로만** 끝났다 — 갭 탐색을
말이 아니라 변이 25판으로 했다.

## 검증 — 전수 25판, 전부 저장소 밖 `mock.patch.object`

코드는 메모리에서만 갈았다 · 워킹트리 `git status --porcelain` 빈손 ·
`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d)` 동반.

**① 개발 반복의 판정을 독립 재측했다 — 하나 빼고 그대로다.**

| 변이 | 어제(반복 372) | 오늘 | 죽은 자리 |
|---|---|---|---|
| M0 무변이 대조군 | 0 | **0** | 오탐 0 |
| M3 `$` 제거 · M4 `re.I` · M5 `[0-9]*` | 1·1·1 | **1·1·1** | `ArchivePatternTest.test_pattern_leaves_live_docs` |
| M11 `design_history` 제거 | 1 | **1** | `…test_pattern_catches_archive_names` |
| M10 접두 확대(`_[0-9]+`→`.*`) | 4 | **4** | `DocCitationTest` 1 + 새 단언 3 |
| M1·M2·M8 (`APPEND_TARGETS`+`CITATION`) | 1·2·3 | **1·2·3** | `CitationPatternTest`·`DocHeadTest`·`DocCitationTest` |
| M7 넓히기 · M9 순서 | 0·0 | **0·0** | 계획 5절대로 안 연다 |
| 계획 63 앵커 다섯 A1a·A1b·A2·A3·A4 | 각 1 | **각 1** | 무회귀 |
| P 양성 대조 `^ZZZ_[0-9]+\.md$` | 4 | **4** | `CAUGHT` 셋 + `DocCitationTest` |

**어긋난 것 하나 — M10 은 정의를 지켜야 4다.** 첫 판에서 `^.*\.md$` 로 갈았더니 6이
나왔다(`NOT_CAUGHT` 여섯 중 `.MD` 만 살아남는다). 계획서가 적은 M10 은 접두를 남긴
`_[0-9]+`→`.*` 이고 그것이 4다. **하네스가 계획서보다 넓게 간 것이지 감지력이 는 것이 아니다.**

**② 갭 탐색 — `ARCHIVE` 를 조각마다 하나씩 갈았다**(`rules/test.md` 3절 ② 경계값).
정규식의 어느 조각도 안 재진 채 남지 않았음을 세어서 보인다.

| 조각 변이 | 죽은 단언 | 판정 |
|---|---|---|
| 대안 `history` 제거 | **2** | 이미 잡힌다 |
| 대안 `plan_history` 제거 | **2** | 이미 잡힌다 |
| `_` 제거 | **4** | 이미 잡힌다 |
| `md` → `md.*` | **1** | 이미 잡힌다 |
| M6 `^` 제거 | 0 | **진짜 등가**(아래) |
| G3 `\.` → `.` | 0 | **진짜 등가**(아래) |
| G4 대안 순서 뒤집기 | 0 | **진짜 등가**(아래) |

**생존 셋은 구멍이 아니라 등가다 — 근거를 각각 댄다.**
`ARCHIVE` 의 제품 소비자는 `tests/test_docs.py:238` **하나뿐**이고(`grep` 확인) 그것이
`ARCHIVE.match(path.name)` 이다.
① **M6**: `re.match` 가 이미 위치 0에 앵커하므로 `^` 는 잉여다. 새 단언이 `search`
의미로 재도 `NOT_CAUGHT` 여섯 중 `…_<숫자>.md` 로 **끝나는** 이름이 0개라 구분자가 없다.
② **G3**: 순회가 `DOCS.glob("*.md")`(같은 줄 237)라 `path.name` 은 **언제나 `.md` 로
끝난다** — `md` 앞 글자가 점이 아닌 입력이 도달 불가다.
③ **G4**: `^` 뒤에서 세 대안은 서로 배타라(`plan_`·`design_` 접두가 갈린다) 순서가
결과를 못 바꾼다.
**셋 다 「재는 쪽이 아니라 지우는 쪽이 답」이고 그것은 계획 64 밖이다**(계획서 5절).

**③ 나머지 카테고리는 해당 없음이다.** ① 부정 경로 = `NOT_CAUGHT` 여섯이 그것이고
실제로 M3·M4·M5·M10 이 거기서 죽는다 · ③ 격리 = 파일·시계·네트워크를 0회 만지는
순수 리터럴 시험이다 · ④ flaky = `sleep`·랜덤·순서 단언 0 · ⑤ 보안 = 신뢰 경계 밖의
문서 검사 상수다 · ⑥ 커버리지 = 새 public 함수 0, `ARCHIVE` 자체는 안 바뀌어 「옛
동작만 덮는」 분기가 0 · ⑦ 동시 실행 = 서버·큐·공유 상태 무관.

**전수 판정 줄(맨몸, 리다이렉션 0):** `Ran 622 tests in 13.781s` · `OK` · **rc 0**.

**만진 파일은 문서 넷뿐** — `tests/test_docs.py`·`src/` 는 **0줄**.

## 다음

**리뷰 phase — 스텝 1/1.** 볼 자리 둘: ① `ArchivePatternTest` 가 `assertRegex`(=`search`)
로 재는데 제품은 `.match()` 다 — 시험이 제품보다 **엄격한** 쪽이라 오늘 거짓 초록은
없지만, 리뷰가 「재는 술어를 제품과 맞출 것인가」를 판단할 자리다. ② 등가 셋(`^`·`\.`·
대안 순서)을 **지우는** 편집은 리뷰가 열지 말지 정한다 — 계획 64 는 안 연다고 적었다.

## 한도

- 병합은 사람 몫이다 — 계획 57~64 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`). 워킹트리에는 변이
  스물다섯 판 내내 문서 넷 말고 아무것도 안 생겼다.
- **`night_iterations` 는 187 그대로 둔다** — 이 반복은 대화형이라 야간 예산을 안 쓴다.
- `docs/digest.md` 는 `[5]` 항목 한 줄만 늘었다 — 줄 수는 200 정각 그대로다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_065.md` 다.
