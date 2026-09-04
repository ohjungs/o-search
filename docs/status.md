---
signal: GREEN
phase: 리뷰
step: 1/1
attempt: 0
iteration: 329
updated: 2026-09-05
ctx: 58
night_iterations: 151
night_red: 2
night_retries: 0
plan: loader-isolation # 계획 56 — 테스트 phase 완료 · 다음은 리뷰
---

# 현재 상태

**계획 56 테스트 phase 를 닫았다 — 오염원을 전수로 세고, 안 잰 축 하나를 실측으로 찾았다.**
저장소 코드 **0줄** 추가. 개발이 남긴 단서(*"센 것은 호출처(1곳)인데 안 센 것은 오염원"*)를
본체로 삼아, 「모듈 수준 싱글턴을 건드리는 자리」를 저장소 전체에서 세고 **실제로 새는지**를
프로세스 전역 대조로 판정했다.

## 오염원 전수 조사 — 후보 7종 · 12자리

grep 이 아니라 **실측이 판정했다**. 후보는 grep 으로 세고, 새는지는 전수 실행 앞뒤의
프로세스 전역 상태를 대조해 갈랐다.

| # | 싱글턴 | 자리 | 되돌리나 | 실측 판정 |
|---|---|---|---|---|
| 1 | `unittest.defaultTestLoader` | `tests/test_readme.py:87` (고쳐짐) | — | **안 샌다** |
| 2 | **`sys.path`** | `test_design_check.py:25` · `test_quality_eval.py:17` · `test_passage_eval.py:184` · **`TestLoader.discover` 자신** | **아니오 (4자리 전부)** | **샌다 — 4칸 남는다** |
| 3 | `signal.SIGINT` | `crawl.py:394` · `test_crawl.py:1904` | 예 (저장·복원 둘 다) | 안 샌다 |
| 4 | 모듈 전역 `PAGES` | `test_crawl.py:156` | 예 (`mock.patch.dict`) | 안 샌다 |
| 5 | `sys.stdout`·`sys.stderr` | `test_serve.py` 등 다수 | 예 (`with` 문) | 안 샌다 |
| 6 | `urllib.request` 전역 opener | `e2e/` 3자리 | 예 (`finally`) | 단위 스위트 **밖** |
| 7 | `logging`·`socket`·`sqlite3`·`warnings`·`locale`·`decimal`·`os.environ` | 저장소 코드 **0자리** | — | 안 샌다 |

**후보 7종 중 실제로 새는 것은 1종(`sys.path`)뿐이다.**

### 「진입점이 또 있나」에 답이 나왔다 — CPython 을 세어서

`defaultTestLoader` 에 쓰는 자리는 **표준 라이브러리 전체에 한 곳**이다 —
`unittest/main.py:151` 의 `self.testLoader.testNamePatterns = …`(3.9.6 실측 grep).
`testNamePatterns`·`testMethodPrefix` 는 **클래스 속성**이고 `main` 은 **인스턴스**에만
쓰므로, `TestLoader()` 새 인스턴스는 그 경로 전부에 면역이다. 그래서 도달 가능한
CLI 경로 넷을 다 때려 봤고 **전부 GREEN**이다.

| 경로 | 결과 |
|---|---|
| `discover -b -s tests -k Readme` | `Ran 5` · **OK** · rc 0 |
| `discover -b -s tests -k '*counts*'` | `Ran 3` · **OK** · rc 0 |
| `python3 tests/test_readme.py -k counts` (`unittest.main` 직행) | `Ran 1` · **OK** · rc 0 |
| `-m unittest -b -k counts test_readme` (비-discover) | `Ran 1` · **OK** · rc 0 |
| `discover -t . -s tests` | **도달 불가** — `tests/` 에 `__init__.py` 가 없어 `ImportError: Start directory is not importable` |

다섯째 줄이 이번에 세운 **못**이다 — 「최상위를 저장소 루트로 두면 검사가 테스트 모듈을
두 번 임포트한다」는 가설을 세웠는데, 재 보니 **그 경로 자체가 안 열린다**. 추측을 실측이
지웠다.

## 순서 뒤집기 — 네 방향 전부 605 OK

| 무엇 | 결과 |
|---|---|
| 전수 (기준) | `Ran 605` · **OK** · 13.593초 |
| **역순** (605건을 통째로 뒤집음) | `Ran 605` · **OK** · 13.438초 |
| **무작위 순열** seed=1 | `Ran 605` · **OK** · 13.743초 |
| **무작위 순열** seed=20260905 | `Ran 605` · **OK** · 13.847초 |
| **모듈 단독 17회** | 17/17 **OK** · rc 0 · 건수 합 **정확히 605** |

역순은 순열 하나뿐이라 무작위 둘을 더 얹었다. 모듈 단독 17회가 가장 센 자다 —
「A 가 심어 놓은 것을 B 가 먹고 산다」면 B 를 혼자 돌릴 때 죽는다. **한 건도 안 죽었다.**

## 전역 대조 — 24축 중 3축이 움직인다

전수를 한 프로세스에서 돌리고 앞뒤를 찍었다(스크래치패드 탐침, 저장소 무접촉).

| 움직인 축 | 값 | 판정 |
|---|---|---|
| `sys.path` | **+4** (`e2e` ×3 · `tests` ×1) | **저장소가 낸 진짜 누출** |
| `logging.Logger.manager.loggerDict` | 0 → 3 (`asyncio`·`concurrent`·`concurrent.futures`) | `import concurrent.futures` 부산물 — **root 로거의 level·handlers 는 무변**이라 테스트끼리 안 섞인다 |
| `tempfile.tempdir` | `None` → `/var/folders/…` | `gettempdir()` 의 stdlib 메모이제이션 — 저장소 코드 아님 |

**안 움직인 21축**: `socket.getdefaulttimeout` · `sqlite3.adapters`·`converters` ·
`warnings.filters` · `sys.getrecursionlimit` · `decimal` prec · `locale.LC_ALL` ·
`signal.SIGINT`·`SIGTERM` · `os.environ`(추가·삭제·변경 0) · `cwd` ·
`sys.stdout`/`stderr` 동일성 · 그리고 **`defaultTestLoader` 축 셋
(`testNamePatterns`·`_top_level_dir`·`errors`) 전부**.

**마지막 줄이 이 계획의 산출물을 처음으로 직접 잰 것이다** — 지금까지는 「`-k` 아래에서
값이 옳다」로 간접 확인했는데, 여기서는 **싱글턴 자체가 안 움직인다**를 봤다.

## 변이 재판 — 둘, 전부 저장소 밖 사본

| 변이 | 무엇 | 결과 |
|---|---|---|
| **D** | 사본에서 `TestLoader()` → `defaultTestLoader` 되돌림 | 전역 대조에서 **`loader._top_level_dir` 이 추가로 움직인다**(3축 → **4축**). 같은 사본에 `-k Readme` → `AssertionError: (605, 21) != (5, 21)` · `Ran 5` · **FAILED · rc 1** |
| **E** | 사본 `e2e/tempfile.py` 로 표준 `tempfile` 을 가림 | 전수 `Ran 605` · **FAILED (failures=22)** · rc 1 |

**변이 D 가 「고친 줄이 곧 싱글턴을 안 건드리는 이유」임을 축 하나로 못 박는다** —
되돌리면 움직이는 축이 정확히 하나 늘고, 그 축이 `_top_level_dir` 이다.

**변이 E 가 2번 후보의 값을 정했다.** `sys.path` 누출은 실재하고 **하위 프로세스까지
전파된다**(러너들이 `sys.path.insert(0, E2E)` 를 자식 부트스트랩에 그대로 넘긴다 —
22건의 실패 트레이스백이 전부 자식 프로세스의 `import tempfile` 이었다).

## 판정 — 새 검사를 안 붙였다 (룰 4절, 8점 미만)

`sys.path` 누출을 **[5]점**으로 매기고 `digest.md` 에 등재했다. 근거 셋:

1. **지금 겹치는 이름이 0개다** — `tests/`+`e2e/` 모듈 이름 **38개**를 표준 라이브러리
   전체와 대조해 충돌 **0건**(38개가 서로도 안 겹친다 — 이름 집합 크기가 17+21 과 같다).
2. **터질 때 시끄럽게 터진다** — 변이 E 가 낸 것은 거짓 초록이 아니라 **즉시 22 FAILED**다.
   이 저장소가 8점을 매겨 온 것은 언제나 「조용히 초록인 것」이었다.
3. **강제할 규칙을 저장소가 못 지킨다** — 「`sys.path` 에 남기지 마라」를 검사로 세우면
   `TestLoader.discover`(stdlib, `loader.py:285`)가 **자기도 위반**한다. 고친 줄 자신이다.

## 다음 행동

**리뷰 phase.** 테스트 phase 가 축을 넷(진입점·순서·전역·이름 충돌)으로 넓혀 전부 초록이고
저장소 코드는 0줄 늘었다. 리뷰가 볼 것은 「이 판정 셋(특히 3번 사유)이 변명이 아닌가」다.

## 러너 규율 — **이번 반복 0회 (누적 35회)**

러너를 스물여덟 번 돌렸다(전수 1 · 역순 1 · 무작위 2 · 모듈 단독 17 · `-k` 계열 5 ·
사본 변이 2). **전부 맨몸이고 파이프 왼쪽에 둔 적 0회 · `2>&1`·`2>/dev/null`·`>/dev/null`
0회 · 백그라운드 0회.** 모듈 단독 17회는 `for` 루프를 썼는데, 앞 반복이 새로 적어 둔
방아쇠(「한 번에 여러 번 돌린다」)가 겨냥한 것은 **루프 자체가 아니라 판정을 가리는 것**이라
루프 안에서 러너를 맨몸으로 두고 `echo "rc=$?"` 를 뒤에 붙여 **17개 판정 줄과 rc 17개를
전부 화면에 남겼다**. 건수 합이 605 로 떨어지는 것도 그 화면에서 셌다.

## 한도

제품 `src/` **0줄** · 저장소 코드 **0줄** · `e2e/` 0줄 · 새 파일 0 ·
`data/crawl.db` **무변**(sha256 `85c96744…5bda18` 대조 통과, 열지 않았다) ·
`docs/specs/` 무변 · `README.md` 무변 · 새 의존성 0 · 스키마·마이그레이션·재색인 0 ·
`pgrep -f websearch.serve` **0건** · `__pycache__` **0개** · `--no-verify`·`--force` 0 ·
`main` 직접 커밋 0 · **PR 무접촉(조회·생성·병합 0회)** · 브랜치 병합·삭제 0 ·
변이 D·E 와 순서 탐침은 **전부 스크래치패드 사본**에서 돌았고 `git status --short` 는 빈 줄이다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **3시간 자동 스냅샷 잡을 루프 작업 중에도 세울 것인가**(반복 328 의 사고).
   이번 반복에는 **안 끼어들었다**(작업 중 커밋 0건 — 아래 커밋만 있다). 다음에 RED
   중간을 덮치면 **깨진 상태가 원격에 올라간다**는 위험은 그대로다. 루프가 도는 동안
   `.mutation-lock` 을 항상 켜 두는 안이 있다.

## 정지 사유

없음 — 계획 56 리뷰 phase 로 이어간다.
