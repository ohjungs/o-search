---
signal: GREEN
phase: 계획
step: 0/1
attempt: 0
iteration: 327
updated: 2026-09-05
ctx: 45
night_iterations: 149
night_red: 2
night_retries: 0
plan: loader-isolation # 계획 56 — 계획서 작성 완료 · 다음은 개발 1/1
---

# 현재 상태

**계획 55 `db-state-invariant` 를 아카이브하고 계획 56 `loader-isolation` 을 열었다.**
계획서는 `docs/plan_loader-isolation.md`, 브랜치는 `loop/loader-isolation`,
기점은 `main`(`fe4dd0d`).

## 새 기점 — 원격을 읽어서 확인했다

`git fetch origin` → `c0be72f..fe4dd0d main`. `git ls-remote origin main` =
`fe4dd0d61018a04e52fc077273c6ef70c57f7011` 이고 `git diff --stat HEAD origin/main` 은
빈손이다. 코디네이터가 PR #10(`loop/db-state-invariant` → `main`)을 병합해 **계획 55 의
코드·문서가 전부 원격에 있다.** 열린 PR **0건**. 병합된 `loop/db-state-invariant` 는
지우지 않았다.

## 아카이브 (계획 55)

`docs/plan_db-state-invariant.md` → `docs/plan_history_041.md`,
`docs/design_db-state-invariant.md` → `docs/design_history_041.md`(둘 다 `git mv`).
`digest.md` 의 가리키는 곳과 완료 항목, `index.md` 의 계획 55 행·원격 줄·사양 분할 10번을
맞췄다. **`history_current.md` 회전은 없다** — 187줄 · 상한 300줄, 반복 수도 20 미만이라
둘 다 안 걸린다. `ArchiveIndexTest` 명부는 `history_<NNN>.md` 만 세므로 이번엔 더할 것이 없다.

## 탐색 — 6순위에서 하나

1~5순위 **0건**: 전수 `Ran 605 tests · OK · rc 0`(실패 0) · 타입·린트 도구 없음 ·
`TODO`/`FIXME` 는 `tests/test_indexer.py` 의 설명용 문자열 하나뿐(작업 아님) ·
`docs/candidates.md` 없음 · `digest ## 보류` **비어 있음**.
6순위(`digest ## 다음 계획 후보`)에서 **`[5]`③** 을 골랐다 — `-k` 를 붙이면
`test_verification_counts_match_reality` 가 **항상 RED**.

**중복 검사 통과**(`discover.md` 5절): `index.md` 의 계획 슬러그 56개 · `digest ## 완료` ·
활성 `plan_*.md` · 보류 · `docs/patches/` 어디에도 로더 격리 건이 없다.

**기록된 답을 실행 전에 다시 쟀다 — 처방이 더 작아졌다.** 후보가 적어 둔 것은 「패턴을
잠시 비웠다 되돌리는 두 줄」인데, 탐침이 잰 값은 새 인스턴스 하나면 전역을 아예 안 만진다는
것이다.

| 상태 | `defaultTestLoader` | `TestLoader()` |
|---|---|---|
| 필터 없음 | 605 | 605 |
| `testNamePatterns = ["*Readme*"]` | **5** | **605** |

**함정인 것이 새로 보였다** — 실패 메시지가 「실제는 (5, 21)」이라 그대로 믿으면
`README.md` 에 `단위 5건` 을 적게 되고, 그러면 전수가 뒤집힌다. 호출처는 저장소 전체에
`tests/test_readme.py` 한 곳뿐이라 공유 지점 수정이다.

## 설계

**건너뛴다.** 대안이 갈리지 않는다 — 「전역 저장·복원」보다 「새 인스턴스」가 엄격히 작고
(한 낱말 vs 두 줄), 전역을 안 만지므로 실패 경로에서 복원을 빠뜨릴 자리도 없다.
파일 1개 · 한 줄 · 제품 `src/` 0줄 · 보안 무관이라 `design.md` 1절 트리거 0.
계획서를 파일로 남긴 것은 「함정」이라는 진단과 완료 기준 3(변이로 잰다)이
`status.md` 세 줄에 안 들어가기 때문이다.

## 다음 행동

**개발 1/1** — `tests/test_readme.py` 의 `unittest.defaultTestLoader.discover(...)` 를
`unittest.TestLoader().discover(...)` 로. 완료 기준은 `docs/plan_loader-isolation.md` 4절
다섯 줄이고, 그중 3(전역 패턴을 세팅해도 605 가 나오는지)이 「고쳤는데 아무것도 안 막는다」를
막는 자다.

## 러너 규율 — **이번 반복 1회 (누적 35회)**

`-k` 의 폭발 반경을 재려고 `for` 루프 안에서 러너를 `2>&1 | tail -6` 으로 일곱 번 돌렸다.
**`rc` 가 통째로 사라졌다.** 즉시 필요한 둘을 맨몸·단독으로 다시 돌려 읽었다 —
`-k Serve` → `Ran 15 tests · OK · rc=0`, `-k readme` → `FAILED (failures=1) · rc=1`.
**기록한 값은 전부 맨몸 실행의 것이다.** 전수(605 OK · rc 0)에는 위반 0회.
누적이 35 인 근거: `digest` 항목이 33 에서 멈춰 있었고 계획 54 설계 반복의 1회가 거기
안 들어와 있어 34 로 맞춘 뒤 오늘 것을 더했다. **새로 보이는 방아쇠: 「한 번에 여러 번
돌린다」** — 루프로 N회 돌리면 화면 예산을 회당으로 나누게 되고 그 나눗셈이 파이프를 부른다.

## 한도

제품 `src/` **0줄** · `data/crawl.db` 무접촉(열지 않았다) · `docs/specs/` 무변 ·
새 의존성 0 · 스키마·마이그레이션·재색인 0 · `pgrep -f websearch.serve` **0건** ·
`--no-verify`·`--force` 0 · `main` 직접 커밋 0 · **PR 무접촉(생성·병합 0)** ·
탐침은 스크래치패드에서만 돌았고 저장소 파일은 한 글자도 안 고쳤다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.

## 정지 사유

없음 — 계획 56 개발 1/1 로 이어간다.
