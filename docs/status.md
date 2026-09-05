---
signal: GREEN
phase: e2e
step: 1/1
attempt: 0
iteration: 330
updated: 2026-09-05
ctx: 63
night_iterations: 152
night_red: 2
night_retries: 0
plan: loader-isolation # 계획 56 — 리뷰 phase 완료 · 다음은 e2e
---

# 현재 상태

**계획 56 리뷰를 백지에서 돌렸다 — 고친 한 줄은 옳고, 그것을 정당화한 기록 둘이 틀렸다.**
저장소 코드는 여전히 **0줄** 늘었다. 리뷰가 고친 것은 `docs/digest.md` 의 문장 둘뿐이다.

## 패스 A (백지) — diff 만 보고 판정

`git diff fe4dd0d..HEAD` 의 코드 변경은 `tests/test_readme.py` 한 줄(+주석 넉 줄)뿐이다.

`unittest.defaultTestLoader.discover(...)` → `unittest.TestLoader().discover(...)`

**열거형 완전성을 diff 밖에서 셌다.** 「`-k` 만 오염원인가」를 CPython 3.9.6 전수로 물었더니
`unittest.main` 이 로더 인스턴스에 심는 상태는 **정확히 둘**이다 — `testNamePatterns`
(`main.py:151`)과 `_top_level_dir`(`loader.py:286`, `discover` 가 자기 안에서 심는다).
**새 인스턴스 하나가 둘 다 닫는다.** 러너 인자 다섯을 직접 때려 확인했다.

| 인자 | 결과 |
|---|---|
| `discover -b tests` (전수) | `Ran 605` · **OK** · rc 0 · 13.489초 |
| `-k Readme` | `Ran 5` · **OK** · rc 0 |
| `-k '*counts*'` | `Ran 3` · **OK** · rc 0 |
| `-p 'test_r*.py'` | `Ran 37` · **OK** · rc 0 (패턴은 로더에 안 남고 인자로만 간다) |
| `--locals -k Readme` · `-f -k Readme` | 각 `Ran 5` · **OK** · rc 0 |
| `-t . -s tests` | **도달 불가** — `ImportError: Start directory is not importable` (재현) |

전역 대조도 직접 다시 쟀다: 전수 뒤 `sys.path` **+4**(`e2e` ×3 · `tests` ×1),
`defaultTestLoader` 축 셋(`testNamePatterns`·`_top_level_dir`·`errors`) **전부 무변**.
테스트 phase 의 숫자가 한 자리도 안 틀렸다.

## 지적 셋 — 전부 「판정은 맞고 근거가 틀렸다」

직전 phase 가 리뷰에 넘긴 물음은 「`[5]` 등재 판정 셋이 변명이 아닌가」였다.
**[5] 라는 값은 유지한다. 그러나 셋 중 둘은 근거가 무너진다.**

### [R56-1] 「누출이 프로세스 경계를 넘는다」는 틀렸다 — medium · 95점 · **고쳤다**

`digest.md` 와 `history_current.md` 가 *"러너들이 `sys.path.insert(0, E2E)` 를 자식
부트스트랩에 그대로 넘긴다 — 누출이 프로세스 경계를 넘는다"* 라고 적었다.
**`sys.path` 는 자식에게 상속되지 않는다** — 마커를 심고 `subprocess.run` 으로
`-c` 를 띄워 실측했다(`CHILD_HAS_MARKER=False`).
자식에 `E2E` 가 있는 진짜 이유는 `tests/test_passage_eval.py:47` 이 `-c` 소스에
`import sys; sys.path.insert(0, %r)` 를 **직접 써 넣기** 때문이다. 의도된 배선이고,
부모 `sys.path` 가 완벽히 깨끗해도 똑같이 들어간다.

### [R56-2] 변이 E 는 누출을 잰 적이 없다 — medium · 90점 · **고쳤다**

저장소 밖 사본에 `e2e/tempfile.py` 를 다시 심어 전수를 돌렸다. 실패가 두 갈래로 갈린다:
**자식 9건**(`test_passage_eval`, 트레이스백에 `<string>` 프레임 — [R56-1] 의 배선)과
**같은 프로세스 13건**(`test_quality_eval`, `<string>` 프레임 없음).
**둘 중 어느 것도 «끝나고 남은 칸» 이 원인이 아니다** — 후자는 `test_quality_eval.py:17`
자신의 **살아 있는** insert 로 들어간다. 즉 판정 ②(「터질 때 시끄럽게 터진다」)는
결론은 맞지만 **다른 현상을 잰 증거** 위에 서 있었다.

**그래서 항목의 틀 자체가 틀렸다.** 세 insert 중 둘(`test_design_check.py:25` ·
`test_quality_eval.py:17`)은 **임포트 시점**에 돈다 — `discover()` 중, 첫 테스트가
돌기 전이다. 위험한 것은 «스위트가 끝나고 네 칸을 남긴다»(프로세스가 곧 죽으니 거의 무해)가
아니라 **`e2e/` 가 전수 내내 `sys.path[0]` 에 앉아 있다**는 쪽이다. 「끝에 남는다」로 읽은
미래의 독자는 이 항목을 과소평가한다.

### [R56-3] ③ 「강제할 규칙을 저장소가 못 지킨다」는 과장이다 — low · 85점 · **고쳤다**

`TestLoader.discover` 가 `loader.py:285` 에서 `top_level_dir` 을 안 뺀다는 것은 **사실이다**
(원문을 열어 확인). 그러나 그것이 「검사가 불가능하다」를 세우지는 못한다 —
**앞뒤 대조가 저장소 몫(`e2e` ×3)과 stdlib 몫(`tests` ×1)을 경로로 가른다.**
테스트 phase 의 탐침이 이미 그 다섯 줄이었다. 그리고 **더 싼 처방이 아예 따로 있다**:
세 자리에 `if E2E not in sys.path` 한 줄씩. 지금 `e2e` 칸이 **셋으로 중복**되는 것이
그 가드가 없다는 증거다. `digest.md` 가 *"답은 이름 충돌 목록 하나를 세는 것"* 이라고
절반은 물러서 있어 **값은 `[5]` 로 둔다** — 고친 것은 문장이다.

## 판정 유지 — ①은 오히려 더 세게 재확인됐다

판정 ①(이름 충돌 0)은 독립적으로 다시 셌고 **축을 넓혀도 버틴다**:
`tests/`+`e2e/` 파일 **38개 · 고유 스템 38개**(서로 충돌 0),
**stdlib 0건 · `src/` 스템 0건 · `site-packages` 0건**. 테스트 phase 는 stdlib 만 봤는데
셋 다 비어 있다. **잠복이라는 판정은 그대로 옳다.**

## 다음 행동

**e2e phase.** 지적 셋이 전부 문서 정정으로 닫혔고 저장소 코드는 0줄이라
e2e 는 회귀 확인(21종 전수 rc 0)이 본체다.

**집안일 예고 — `history_current.md` 가 298줄이다(상한 300).** 이번엔 안 넘어 회전하지
않았지만 **다음 append 는 반드시 넘는다.** e2e phase 가 기록 전에 회전부터 한다.

## 러너 규율 — **이번 반복 0회 (누적 35회)**

러너를 여덟 번 돌렸다(전수 1 · 인자 매트릭스 5 · 탐침 1 · 사본 변이 1).
**전부 맨몸이고 파이프 왼쪽에 둔 적 0회 · `2>&1`·`2>/dev/null`·`>/dev/null` 0회 ·
백그라운드 0회.** 판정 줄과 `rc=` 를 전부 화면에 남겼다.

## 한도

제품 `src/` **0줄** · 저장소 코드 **0줄** · `tests/`·`e2e/` **0줄** · 새 파일 0 ·
`data/crawl.db` **무변**(sha256 `85c96744…5bda18` 대조 통과) · `docs/specs/` 무변 ·
`README.md` 무변 · 새 의존성 0 · 스키마·마이그레이션·재색인 0 ·
`pgrep -f websearch.serve` **0건** · `__pycache__` **0개** · `--no-verify`·`--force` 0 ·
`main` 직접 커밋 0 · **PR 무접촉(조회·생성·병합 0회)** · 브랜치 병합·삭제 0 ·
변이 재현은 **스크래치패드 사본**에서 돌고 지웠다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **3시간 자동 스냅샷 잡을 루프 작업 중에도 세울 것인가**(반복 328 의 사고).
   이번 반복에도 **안 끼어들었다**. RED 중간을 덮치면 깨진 상태가 원격에 올라간다는
   위험은 그대로다. 루프가 도는 동안 `.mutation-lock` 을 켜 두는 안이 있다.

## 정지 사유

없음 — 계획 56 e2e phase 로 이어간다.
