---
signal: GREEN
phase: 개발
step: 0/1
attempt: 0
iteration: 371
updated: 2026-09-06
ctx: 46
night_iterations: 187
night_red: 2
night_retries: 4
plan: archive-scope-cover 계획 64 (계획 완료 · 설계 생략 · 다음은 개발 1/1)
---

## 현재 상태

**계획 64 `archive-scope-cover` 를 등재했다 — 1스텝 · 설계 생략(트리거 0) · 다음은 개발.**
계획서는 `docs/plan_archive-scope-cover.md` 이고 `docs/index.md` 64번 행에 올렸다.
`tests/test_docs.py` 의 `ARCHIVE` 는 `DocCitationTest` 가 **어느 문서를 훑을지**를 혼자
정하는데 그 판정을 재는 단언이 0개다 — 넓히는 변이 셋과 좁히는 변이 하나가 전수 620건에서
**죽은 단언 0** 으로 산다. 계획 60→61→62→63 이 다섯 번 닫은 자리의 마지막 상수다.

## 탐색

**1~5순위 실측 0건.** 전수 맨몸 `Ran 620 tests in 15.877s` · `OK` · rc 0 ·
린터/타입체커 설정 파일 0개(최상위 설정은 `.gitignore` 하나뿐) · `TODO`/`FIXME`/`HACK`
이 `src/`·`tests/`·`e2e/` 에 1건인데 그것은 `tests/test_indexer.py:759` 의 **파서 입력
문자열 안** · `docs/candidates.md` 없음 · `docs/patches/` 없음 · `digest ## 보류` 절이
비어 0건 · `gh issue list --state open` 0건 rc 0 · 활성 계획 0.

**6순위에서 열었다** — `digest ## 다음 계획 후보 (테스트 phase 갭, 8점 미만)` 의 `[5]`
「범위 상수 둘은 아직 안 재진다」. 여는 조건이 「`APPEND_TARGETS` 나 `ARCHIVE` 를 손대는
날」인데 계획 63 이 같은 파일의 같은 축을 반복 370 에 닫아 미룬 이유가 없어졌다.
**더 높은 점수는 전부 여는 조건 미도래**다 — `[9]` `/search` 몫 · `[8]` 숨은 텍스트
뒷절반(재색인) · `[8]`·`[6]` 토크나이저(실물 코퍼스) · `[7]` macOS pycache(처방 기투입) ·
`[7]` robots 비ASCII(도달 불가) · `[7]` 키셋 페이지네이션(사람 결정) · `[6]`
`_IMPLIED_END` 표 · `[6]` `extract_blocks` 이름표 · `[6]` `Frontier` 폐기.

## 착수 탐침 — 기록이 뒤집혔다

저장소 밖 `mock.patch.object` 하네스로 변이마다 전수를 다시 돌렸다(워킹트리 무변경).

**`ARCHIVE` 축은 넷이 산다** — M3(`$` 제거) · M4(`re.I`) · M5(`[0-9]+`→`[0-9]*`)에 더해
**기록에 없던 M11(`design_history` 이름 빼기)까지 `Ran 620 · 죽은 단언 0`**. 양성 대조
(`^ZZZ_[0-9]+\.md$`)가 `DocCitationTest` 1건을 죽여 배선을 증명했다. M11 의 도달성은
항목이 ② 를 `[4]` 로 깎은 이유와 다르다 — `design_history_*.md` 가 오늘 `docs/` 에 **33개**
실재해서, 이름 하나가 빠지면 그 33개가 곧바로 검사 대상이 된다.

**반대로 항목이 값을 뒀던 ①(`APPEND_TARGETS`)은 하네스 인공물이다**(`digest [7]`
「기록된 답을 실행 전에 다시 재라」 **열다섯 번째 적용**). `CITATION` 이 임포트 시점에
그 상수에서 파생되므로, 소스 편집과 같게 둘을 함께 갈면 M1(셋→둘) **1건** ·
M2(셋→하나) **2건** · M8(이름 오타) **3건**이 죽는다. 항목이 잰 방식대로
`APPEND_TARGETS` 만 갈면 오늘도 0 이라 재현은 됐지만, 그 0 은 소스 편집의 값이 아니다.
살아남는 것은 M7(대상에 `project.md` **추가**) 하나인데 검사를 더 조일 뿐 오늘 아무것도
안 깬다. **그래서 축 하나를 버리고 `ARCHIVE` 에만 선다.**

**처방 리터럴 아홉이 갈래를 실제로 가르는 것도 미리 쟀다** — 실물 정규식은 `CAUGHT` 3/3
통과 · `NOT_CAUGHT` 6/6 거절(**오탐 0**)이고, M3 은 `history_001.md.bak.md` · M4 는
`HISTORY_001.MD` · M5 는 `history_.md` · M10(접두 확대)은 그 셋에 `history_current.md`
까지 · M11 은 `design_history_046.md` 에서 각각 물린다.

## 다음

**개발 phase — 스텝 1/1.** `ArchivePatternTest` 를 `ArchiveMatchTest` 옆에 세운다
(리터럴 표 한 벌 + 메서드 둘). 완료 기준 9개는 계획서 4절에 있다. 제품 `src/` **0줄**.
새 메서드가 둘 늘므로 `README.md` 의 「단위 N건」을 **같은 커밋에서** 함께 고친다.

## 한도

- 병합은 사람 몫이다 — 계획 57~64 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`). 워킹트리는 변이 열두 판
  내내 `git status --porcelain` 빈손이었다.
- **`night_iterations` 는 187 그대로 둔다** — 이 반복은 대화형이라 야간 예산을 안 쓴다.
- `docs/digest.md` 는 **200줄 정각** 유지 — `[5]` 항목에 정정을 **덧붙여** 줄 수를 안 늘렸다.
- 회전은 없다 — `history_current.md` 는 상한 300 아래고, 다음 회전 번호는 `history_065.md` 다.
