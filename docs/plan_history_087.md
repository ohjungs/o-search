# 계획 112 — `docs/*.md` 의 계획·설계 인용을 무는 자

- 슬러그: `doc-cite-roots`
- 브랜치: `loop/doc-cite-roots`
- 상태: 개발 (설계 완료 — `docs/design_doc-cite-roots.md`)
- 근거: `docs/digest.md` `## 다음 계획 후보` 의 `[6] docs/*.md 44종의 인용은 해석 뿌리가
  넷으로 갈려 같은 자로 못 잰다` (2026-09-28 반복 650 등재) + **2026-10-07 반복 680 실측**:
  살아 있는 `docs/*.md` 9개 안에서 백틱 안 `` `plan_*.md` ``·`` `design_*.md` `` 토큰이
  **41자리에서 없는 파일을 가리킨다**(계획 phase 실측). 전수 857 OK 가 **하나도 안 문다.**
  **설계 phase 가 그 수를 깼다 — 백틱을 안 보는 실물 정규식으로는 47이고**, 자기 글 5자리를
  표기 정책대로 고친 뒤 개발이 받는 것은 **40**(`index.md` 28 · `digest.md` 8 ·
  `baselines.md` 2 · `metrics.md` 2) **+ 자리표시자 2**(`digest.md` 의 두 후보 항목)다.

## 1. 문제 · 목표 · 기대 결과

**문제.** 계획을 마감하면 `plan_<슬러그>.md` → `plan_history_<NNN>.md` 로 옮긴다
(`rules/docs.md` 4절). 옮기는 절차만 적혀 있고 **인용을 고치라는 말이 없으며 재는 자도 없다.**
계획 109 가 같은 구멍을 **코드 쪽**에만 막았다 — `tests/test_docs.py:2485` 의
`CitationAliveTest` 는 `ALIVE_DIRS = ("src", "tests", "e2e", "scripts")` 만 훑고,
같은 파일 2320~2322행 주석이 **`docs/` 는 이 축 밖이다**라고 그 제외를 못박아 뒀다.

**목표.** 살아 있는 `docs/*.md` 가 대는 계획·설계 인용이 실재하는 파일을 가리키는지
무는 자 하나를 세우고, 지금 끊긴 41자리를 고친다.

**기대 결과.** 다음에 계획을 아카이브하면서 인용을 안 고치면 **전수가 RED 로 막는다.**
지금은 `index.md` 가 다 끊긴 채로 857건 초록이다.

## 2. 이미 참인 것 — 이 대화를 못 본 사람이 이어받을 지점

- **판정은 새로 안 만든다.** `tests/test_docs.py:2352` 의 `citation_alive_gap(sites, docs)` 가
  `(경로, 줄번호, 이름)` 목록을 받아 없는 파일을 `파일:줄 — 이름` 으로 돌려준다.
  이 계획이 더하는 것은 **모으는 자**(`docs/*.md` 순회)와 **면제 정책**뿐이다.
- **아카이브 판별자도 있다.** 같은 파일의 `ARCHIVE` 정규식이 `*_history_*.md` 를 가른다
  (`DocCitationTest` 가 쓰는 그것).
- **뿌리 넷의 서술은 이미 적혀 있다** — `docs/plan_history_084.md` 3절. 설계 phase 가 읽는다.
- 실측 스크립트는 남기지 않았다. 재현은 설계 phase 가 다시 잰다.
- **이 계획서 자신이 기존 자에게 두 번 물렸다** — 초고가 append 전용 문서를 줄번호로
  가리켜 `DocCitationTest` 가, 스텝 3 기록이 금지된 꼴을 그대로 적어 새 자가 물었다.
  **세울 자의 형제가 이미 돌고 있다**는 실물 증거다. 접힌 3절의 나머지는 설계 문서에 있다.
- **같은 축의 셋째 사례**(범위 밖): 아카이브 명부가 없는 파일 `history_075.md` 를 든다 —
  `ArchiveIndexTest` 는 한 방향만 본다. 서술은 `docs/design_doc-cite-roots.md` 「범위 밖」 절.

## 3. 갈림길 — **설계가 닫았다** (원본: `docs/design_doc-cite-roots.md`)

**결정**: ① 모으는 자만 분리(판정·정규식은 공유) ② 끊긴 자리는 **아카이브 이름으로 고친다**
③ **면제 기제를 안 만든다** — 자리표시자는 슬러그/꺾쇠 꼴로 글을 고친다.
대안 A/B/C 비교와 버린 ①안의 근거(`ALIVE_CITATION_FLOOR` 무력화), 깬 가정(41 → 47)은
**전부 설계 문서에 있다** — 여기 적었던 착수 전 서술은 그래서 접었다(`rules/docs.md` 1절).
**설계 트리거 2건**(파일 5개 · 대안 2개 이상)에 걸려 설계를 돌렸다.

## 4. 스텝

### 스텝 1 — 자를 세운다 (실패부터)
- 의존: 없음 (설계 결정 필요)
- 할 일: `tests/test_docs.py` 에 `doc_citation_sites()` 와 그 패턴 테스트,
  실물 축 하나를 더한다. 판정은 `citation_alive_gap` 을 그대로 부른다.
  2320~2322행의 「`docs/` 는 이 축 밖이다」 주석을 설계가 고른 경계로 고쳐 적는다.
- 건드릴 파일: `tests/test_docs.py`
- 완료 기준: `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests`
  가 **RED** 이고 메시지가 설계 결정 후 남은 자리를 `파일:줄 — 이름` 으로 전부 댄다.
  패턴 테스트와 하한(`순회가 죽으면 0건 초록`) 자리는 **초록**이다.

### 스텝 2 — `index.md` 28자리를 고친다
- 의존: 1 (자가 대는 목록을 읽어야 어디를 고칠지 안다)
- 건드릴 파일: `docs/index.md`
- 완료 기준: 전수에서 `index.md` 자리가 0 으로 줄고 `StepSyncTest`·`StrikeGapTest` 가 초록.

### 스텝 3 — `digest.md` 8+2 · `baselines.md` 2 · `metrics.md` 2 를 고친다
- 의존: 1 (2 와는 의존 없음 — 파일이 겹치지 않는다. 야간이라 순차로 돈다)
- 건드릴 파일: `docs/digest.md` · `docs/baselines.md` · `docs/metrics.md`
- 완료 기준: 전수 **초록** · 건수가 857 이상 · `ReadBudgetTest` 초록(합계 600 이내).

### 스텝 4 — 자가 실제로 무는지 변이로 확인한다
- 의존: 3
- 할 일: 변이 최소 4판 — ① 순회 디렉터리를 빼기 ② 면제 목록을 통째로 넓히기
  ③ 아카이브된 이름 하나를 살아 있는 이름으로 되돌리기(실물 재발 모양)
  ④ 패턴에서 `design_` 빼기. `PYTHONDONTWRITEBYTECODE=1` **과**
  `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를 함께 준다(`project.md` 변이 검사 절).
- 건드릴 파일: 없음 (변이는 심고 되돌린다)
- 완료 기준: 네 변이가 전부 **잡힘**. 살아남으면 갭 테스트를 세우고 재측정한다.

## 5. 하지 않을 것

- **`docs/candidates.md` 29자리** — 하네스가 만들 파일이고 축이 다르다. 후보 `[6]` 소관
- **저장소 밖 루프 룰 인용**(`rules/*.md`·`SKILL.md`·`severity.md` 등 약 100자리) — 뿌리가
  `~/.claude/skills/loop-harness` 라 이 저장소가 못 잰다. 범위 밖
- **아카이브 문서**(`history_*.md`·`plan_history_*.md`·`design_history_*.md`) — 접힌 기록이다
- **줄번호 인용 축**(`DocCitationTest`) — 이미 다른 자가 물고 있다. 건드리지 않음
- **`docs/specs/` · `docs/e2e/<슬러그>/result.md`** — 뿌리가 또 갈린다. 별도 계획
- **`rules/docs.md` 4절에 「인용도 고친다」를 적는 것** — 저장소 밖이다. 사람 몫
