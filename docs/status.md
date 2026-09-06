---
signal: DONE
phase: e2e
step: 0/0
attempt: 0
iteration: 375
updated: 2026-09-06
ctx: 55
night_iterations: 187
night_red: 2
night_retries: 4
plan: null
---

## 현재 상태

**계획 64 `archive-scope-cover` 를 e2e 1/1 로 닫았다 — 통과 · 완료 기준 9/9 · 활성 계획 0.**
e2e 21종을 전부 맨몸으로 다시 돌려 **rc 0 · 21/21** 이고, 전수는 `Ran 622 tests in
15.941s` · `OK` · rc 0 이다. 결과는 `docs/e2e/archive-scope-cover/result.md`.

## e2e 결과

**새 e2e 파일 0개를 「해당 없음」으로 넘기지 않고 근거 셋으로 쟀다**(`rules/e2e.md` 3절) —
프로세스 밖 변화 0(`src/`·`e2e/`·`docs/specs/`·`data/` diff **빈손**) · 새 클래스가
`tests/` 안이라 네 수단(웹 UI·HTTP API·CLI·라이브러리) 어디에도 걸 곳이 없다
(`src/` 에 `tests` 를 import 하는 줄 **0건**) · 새로 만들면 전수 명령과 겹쳐 「1회만」이
깨진다. 계획 61·62·63 이 밟은 자리와 같고 형식도 같다.

**대신 사용자 관점 검증을 실행했다.** 실물 `docs/` 를 `mktemp -d` 로 복사해 **같은 인용
한 줄을 일곱 자리에** 넣었다 — 어디에 넣느냐가 곧 `ARCHIVE` 가 혼자 정하는 축이다.
아카이브 셋(`history_065.md`·`design_history_099.md`·`plan_history_099.md`)은 **조용하고**
(`Ran 28 · OK`), 아카이브처럼 생겼지만 아닌 둘(`history_001.md.bak.md`·`history_.md`)과
살아 있는 `index.md` 는 **운다**. **오늘 계획이 산 자리가 그 「운다」다** — 이 계획 전이라면
판정은 같았겠지만 `ARCHIVE` 가 `$` 나 수량자를 잃어도 아무도 안 울어서, 그 둘이 조용해지는
날을 막을 자가 없었다.

**대조군이 처음엔 빨갰고 그것이 오늘의 회전을 검사했다.** `history_065.md` 를 만든 직후
`digest.md` 명부에 이름을 넣기 전 상태에서 `ArchiveIndexTest` 가 「명부에 없다」로 울었다 —
계획 64 의 형제 가드가 이번 회전 절차 자체를 문 것이고, 명부를 채우자 초록으로 돌아왔다.

**완료 기준 9/9 를 열여덟 판으로 다시 쟀다.** M0 대조군 `Ran 622 · 죽은 단언 0`(오탐 0) ·
**M3**(`$` 제거)·**M4**(`re.I`)·**M5**(`[0-9]*`) → `ArchivePatternTest.test_pattern_leaves_
live_docs` 각 1건 · **M11**(`design_history` 제거) → `…test_pattern_catches_archive_names`
1건 · **M10**(접두 확대) 4건 · **M1·M2·M8**(`APPEND_TARGETS` 축) 1·2·3건 · 계획 60~63 의
앵커 변이 **일곱**도 각 1건(감지력 무회귀). 기준선은 8축 전부 회귀 0 이라
`docs/project.md` 를 한 줄도 안 갱신했다.

## 계획서가 「안 잰다」로 남긴 등가 주장을 실행으로 확인했다

M6(`ARCHIVE` 에서 `^` 제거)은 계획 5절이 **완전 등가**라 뺀 변이다. 오늘 같은 판에 세우니
`Ran 622 · 죽은 단언 0` 이고, **바로 그 판에서** 양성 대조(`^ZZZ_[0-9]+\.md$`)는 4건을
죽인다. 하네스가 죽어서 0 이 아니라 살아 있는데도 0 이다 — 등가라는 말이 「안 재도 된다」의
근거로 서려면 이 두 줄이 함께 있어야 한다.

## e2e 가 잡은 것 — 없음

diff 의 주장(소비자가 `ARCHIVE.match()` 한 곳뿐 · `src/` 가 `tests` 를 안 읽는다 ·
리터럴 아홉이 실물에서 오탐 0)을 실물과 다시 대조했다 — **어긋난 곳 0**.

## 검증

전수 **맨몸** `Ran 622 tests in 15.941s` · `OK` · **rc 0**.
e2e 21종 개별 실행 **전부 rc 0**. `ls e2e/*.py` **21개** ↔ `README.md` 「e2e 시나리오 21종」 ·
`README.md:104` 「단위 622건」 ↔ 실제 622.
범위 무접촉 — `git diff --stat ba53783 HEAD -- src/ e2e/ docs/specs/ data/` **빈손** ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변.

## 다음

**활성 계획 0 — 다음 반복은 계획 phase 다.** 후보 탐색은 이 반복에서 하지 않았다.
계획 64 가 소비한 `[5]` 는 테스트 phase 가 이미 취소선으로 닫았고, 그 항목의 ① 도
「하네스 인공물이라 다시 열지 않는다」로 닫혀 있다.

## 한도

- 병합은 사람 몫이다 — 계획 57~64 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main`(`d1fe3e9`) 무접촉 · PR #7 무접촉(`gh pr` 호출 0).
- `--force`·`--amend`·`rebase` 없음. 스텝 하나 = 커밋 하나.
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 **0회**(누적 38 유지).
- `PYTHONDONTWRITEBYTECODE=1` 과 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다.
- 변이는 저장소 밖에서만 — 코드는 메모리(`mock.patch.object`), 문서는 `mktemp -d` 복사본.
- `docs/digest.md` 는 **200줄 정각**이다 — 완료 한 줄을 더하면서 가장 오래된 완료 항목
  하나(계획 58 `passage-cost-band` · 원본 `plan_history_044.md`)를 지워 정각을 지켰다.
- **회전했다** — 이 기록을 붙이면 상한 300 을 넘어 계획 63 의 반복 기록 다섯(반복 366~370)을
  `history_065.md` 로 밀었다. `history_current.md` 는 **187줄**(항목 5)이고 다음 회전
  번호는 `history_066.md` 다.
