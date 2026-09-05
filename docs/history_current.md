# 최근 반복 기록

<!--
append 전용. 수정·삭제 금지.

상한 20회 / 300줄. 넘으면 오래된 것부터 history_<NNN>.md 로 밀어내고,
밀어낼 때 digest.md 에 1~2줄로 압축해 남긴다. (docs.md 룰)

이 파일은 매 반복 읽힌다. 그래서 상한이 있다.
-->

## 형식

```
## YYYY-MM-DD HH:MM | <plan-slug> | <phase> <step> | 시도N
- 한 일: <무엇을 했나. 파일 경로 포함>
- 결과: <검증 결과. 테스트 12/12 통과 / 린트 0건 / 실패 출력 요약>
- 다음: <다음 스텝 또는 정지 사유>
```

실패한 반복도 반드시 남긴다. 실패 기록이 없으면 같은 실수를 반복한다.

**회전 명부는 `digest.md` 의 `## 완료` 절 «아카이브 명부» 줄이 정본이다.**
여기 있던 스물한 회전의 서술(233줄)은 그 줄과 내용이 겹쳤고, 검사가 강제하는 명부도
그쪽 하나뿐이라(`tests/test_docs.py` 의 `ArchiveIndexTest`) **개발 9(반복 269)가 이
자리에서 지웠다** — 회전으로는 300줄 상한을 못 맞추던 세 반복(309 → 372 → 418줄)의
원인이 이 명부였다. **지운 것은 머리말이지 반복 기록이 아니다** — 항목은 여전히
append 전용이고 수정·삭제 금지다. 각 회전의 사유는 `digest.md` 의 같은 줄에, 원문은
`history_<NNN>.md` 에 그대로 있다.

## 2026-09-05 02:59 | loader-isolation | 계획 0/1 | 시도0

- 계획 55 아카이브(`plan/design_history_041.md`) · 새 기점 `main`(`fe4dd0d`, PR #10 병합 확인 ·
  열린 PR 0) · `history_current` 회전 없음(187줄 < 300).
- 탐색 1~5순위 0건 → 6순위 `digest [5]`③. **기록된 처방(전역 저장·복원 두 줄)보다 작은 답을
  탐침이 냈다** — `unittest.TestLoader()` 새 인스턴스(필터 아래 605 vs 5), 호출처는 한 곳뿐.
  실패 메시지가 README 를 틀리게 고치라고 지시하는 **함정**인 것이 새로 보였다.
- 러너 규율 **위반 1회(누적 35)** — `for` 루프로 `-k` 일곱 번을 `2>&1 | tail -6` 에 넣어 `rc` 를 잃었고
  즉시 맨몸 재실행했다. 새 방아쇠: 「한 번에 여러 번 돌린다」. 전수 **605 OK · rc 0** · 제품 0줄.
- 다음: 개발 1/1 (`tests/test_readme.py` 한 줄 + 주석 · 완료 기준은 계획서 4절).

## 2026-09-05 05:05 | loader-isolation | 개발 1/1 | 시도0

- 한 일: `tests/test_readme.py` 의 `test_verification_counts_match_reality` 가 세는 자를
  모듈 수준 싱글턴 `unittest.defaultTestLoader` 에서 **새 인스턴스 `unittest.TestLoader()`**
  로 바꿨다(실질 한 줄 + 왜인지 적는 주석 넉 줄). 제품 `src/` **0줄** · `e2e/` 0줄 ·
  저장소 코드 파일 **1개**. 착수 전에 계획서의 값을 맨몸으로 다시 쟀고 한 글자도 안 달랐다.
- 결과: **RED 를 눈으로 봤다** — `-k Readme` 가 `AssertionError: (605, 21) != (5, 21)` ·
  `Ran 5` · rc 1. 고친 뒤 `-k Readme` **`Ran 5 · OK · rc 0`**, 전수 **`Ran 605 tests · OK ·
  rc 0`**(13.579초 · 맨몸·단독 · 고치기 전 605 와 같다). 기전 실측: 전역에
  `testNamePatterns=["*Readme*"]` 를 심으면 `defaultTestLoader` **5** · `TestLoader()` **605**.
  호출처는 저장소 전체에 **한 곳뿐**(다시 셌다).
  **완료 기준 3 을 변이 셋으로 쟀다**(전부 저장소 밖 사본): ①검사 안에서 전역을 손으로
  오염 → `OK` rc 0(고친 줄이 막아 냈다) · ②그 위에서 `TestLoader()` 를 되돌림 →
  **`FAILED` rc 1**(확인이 살아 있다) · ③`README` 의 `단위 605건`→`604건` →
  **`FAILED` rc 1**(자가 안 멀었다).
  `README.md` 무변(완료 기준 4) · `git status --short` 에 계획 밖 코드 파일 **0개**(기준 5).
  `data/crawl.db` sha256 `85c96744…5bda18` 무변 · `docs/specs/` 무변 · 서버 잔여 0 ·
  **PR 무접촉(조회 0회)** · `--no-verify`·`--force` 0 · 러너 규율 위반 **0회**.
- **핵심 발견 — 함정이 사라진 것을 변이 ③이 같이 보여 줬다.** 고친 뒤엔 같은 실패가
  `-k` 아래에서도 「실제는 **(605, 21)**」라고 말한다. 고치기 전 그 자리의 문구는
  「실제는 (5, 21)」이었고, 그것을 믿고 README 를 고치면 전수가 뒤집혔다.
  **이 계획의 산출물은 「검사가 산다」가 아니라 「검사가 참말을 한다」였다.**
- **사고 — 3시간 자동 스냅샷 잡이 스텝 중간을 덮쳤다.** launchd
  `com.ohjungs.osearch-autocommit`(`StartInterval 10800`)이 04:50 에 작업 트리의 코드
  변경을 `bfaa3d8 자동 스냅샷 … 미커밋 작업 보존` 으로 커밋하고 **원격에 밀었다**.
  되돌리려면 `push --force` 인데 한도가 금지해 **고치지 않고 뒀다** — 브랜치의 코드는
  계획대로고 값도 같지만 **스텝 커밋이 둘로 갈렸다**(코드 `bfaa3d8` · 기록 이번 커밋).
  계획 45 의 `.mutation-lock` 관례가 이 잡을 세우려고 있던 것인데, 그 관례는 «변이를
  심는 동안» 만 덮고 **정상 작업 중간**은 안 덮는다. 다음에 RED 중간을 덮치면 깨진
  상태가 원격에 올라간다 — `status.md` 사람 결정 4번으로 올렸다.
- 다음: **테스트 phase.** 개발이 이미 변이 셋으로 재고 왔으니 볼 것은 「그 셋이 충분한
  축인가」다. 안 잰 축 하나가 보인다 — 오늘 센 것은 **호출처**(1곳)인데 안 센 것은
  **오염원**이다(`unittest.main` 말고 `defaultTestLoader` 에 상태를 심는 진입점이 또 있나).

## 2026-09-05 07:40 | loader-isolation | 테스트 1/1 | 시도0

- 한 일: 개발이 남긴 단서(*"센 것은 호출처(1곳)인데 안 센 것은 **오염원**"*)를 본체로 삼아
  **모듈 수준 싱글턴을 건드리는 자리를 저장소 전체에서 세고, 새는지를 실측으로 갈랐다.**
  저장소 코드 **0줄** · 새 파일 0(탐침 넷은 전부 스크래치패드).
- 결과 — **오염원 후보 7종 12자리 중 실제로 새는 것은 1종**: `sys.path`(4자리 전부 안
  되돌린다 — `test_design_check.py:25`·`test_quality_eval.py:17`·`test_passage_eval.py:184`,
  그리고 **`TestLoader.discover` 자신**). 나머지는 되돌리거나(`signal.SIGINT` 2자리 ·
  `PAGES` 의 `mock.patch.dict` · `sys.stdout/stderr` 의 `with`) 단위 스위트 밖이거나
  (`urllib` 전역 opener 는 `e2e/` 3자리) 저장소 코드에 **0자리**다
  (`logging`·`socket`·`sqlite3`·`warnings`·`locale`·`decimal`·`os.environ`).
- **「진입점이 또 있나」에 CPython 을 세어 답했다** — `defaultTestLoader` 에 쓰는 자리는
  표준 라이브러리 **전체에 한 곳**(`unittest/main.py:151`, 3.9.6 실측)이고 대상은
  `testNamePatterns` 뿐이다. 그것은 **클래스 속성**인데 `main` 은 **인스턴스**에만 쓰므로
  새 인스턴스는 구조적으로 면역이다. 도달 가능한 CLI 경로 넷을 다 때려 **전부 GREEN**:
  `discover -k Readme`(5 OK) · `-k '*counts*'`(3 OK) · `python3 tests/test_readme.py -k
  counts`(1 OK · `unittest.main` 직행) · `-m unittest -k counts test_readme`(1 OK).
  **다섯째 가설은 실측이 지웠다** — 「`-t .` 로 최상위를 루트로 두면 검사가 테스트 모듈을
  두 번 임포트한다」를 세웠는데 `tests/` 에 `__init__.py` 가 없어 **경로 자체가 안 열린다**
  (`ImportError: Start directory is not importable`).
- **순서 뒤집기 네 방향 전부 605 OK**: 역순(13.438초) · 무작위 seed=1 · seed=20260905 ·
  **모듈 단독 17회**(17/17 OK · rc 0 · 건수 합 **정확히 605**). 역순은 순열 하나뿐이라
  무작위 둘을 얹었고, 가장 센 자는 모듈 단독이다 — 「A 가 심은 것을 B 가 먹고 산다」면
  B 혼자 돌릴 때 죽는데 **한 건도 안 죽었다**.
- **전역 대조 24축 중 3축만 움직인다**(전수를 한 프로세스에서 돌리고 앞뒤를 찍었다):
  `sys.path` **+4** · `logging.Logger.manager.loggerDict` 0→3(`asyncio`·`concurrent`·
  `concurrent.futures` — `import concurrent.futures` 부산물이고 **root 로거의 level·handlers
  무변**) · `tempfile.tempdir` None→경로(`gettempdir()` 의 stdlib 메모이제이션).
  **안 움직인 21축에 `defaultTestLoader` 축 셋이 전부 들어 있다**
  (`testNamePatterns`·`_top_level_dir`·`errors`) — 지금까지 「`-k` 아래 값이 옳다」로
  간접 확인하던 것을 **싱글턴 자체가 안 움직인다**로 처음 직접 쟀다.
- **변이 재판 둘(전부 저장소 밖 사본)**: **D** 사본에서 `TestLoader()`→`defaultTestLoader`
  되돌림 → 움직이는 축이 **3 → 4** 로 정확히 하나 늘고 그것이 `_top_level_dir` 이다,
  같은 사본의 `-k Readme` 는 `(605, 21) != (5, 21)` · `Ran 5` · **FAILED rc 1**(함정 재현).
  **E** 사본 `e2e/tempfile.py` 로 표준 `tempfile` 을 가림 → 전수 `Ran 605` ·
  **FAILED(failures=22)** · rc 1.
- **핵심 발견 — `sys.path` 누출은 실재하고 하위 프로세스까지 전파된다.** 변이 E 의 실패
  22건은 전부 **자식 프로세스의 `import tempfile`** 트레이스백이었다 — 러너들이
  `sys.path.insert(0, E2E)` 를 자식 부트스트랩에 그대로 넘기기 때문이다. 그런데도
  **[5]점으로 등재만 했다**(룰 4절): ① 지금 겹치는 이름이 **0개**다(`tests/`+`e2e/` 모듈
  이름 **38개**를 표준 라이브러리와 대조, 충돌 0 · 서로도 안 겹친다) ② **터질 때 시끄럽게
  터진다** — 거짓 초록이 아니라 즉시 22 FAILED 이고, 이 저장소가 8점을 매겨 온 것은 언제나
  「조용히 초록인 것」이었다 ③ **강제할 규칙을 저장소가 못 지킨다** — 「`sys.path` 에
  남기지 마라」를 검사로 세우면 `TestLoader.discover`(stdlib `loader.py:285`)가 자기도
  위반한다. **고친 줄 자신이 그 규칙의 첫 위반자다.**
- **일반화 — grep 은 「저장소가 쓴 코드」만 보고 전역 대조는 「실제로 움직인 전역」을 본다.**
  이번에 저장소 코드 0자리로 판정한 일곱 축(`logging`·`socket`·`sqlite3` 등)은 grep 만으로는
  «안 쓴다» 까지밖에 못 말한다 — 저장소가 부른 표준 라이브러리가 몰래 바꾼 것은 앞뒤 대조가
  아니면 안 보인다. 실제로 `logging` 과 `tempfile` **둘이 그렇게 잡혔고 둘 다 무해로 판정**됐다.
- 러너 규율 **0회(누적 35)** — 스물여덟 번 전부 맨몸·단독. 모듈 단독 17회에 `for` 루프를
  썼으나 방아쇠가 겨냥한 것은 루프가 아니라 **판정을 가리는 것**이라 러너를 맨몸으로 두고
  `echo "rc=$?"` 를 뒤에 붙여 판정 줄 17개와 rc 17개를 전부 남겼다.
- 한도: 제품 `src/` 0줄 · 저장소 코드 **0줄** · `README.md` 무변 · `data/crawl.db` sha256
  `85c96744…5bda18` 무변 · `docs/specs/` 무변 · `pgrep -f websearch.serve` 0건 ·
  `__pycache__` 0개 · PR 무접촉 · `--no-verify`·`--force` 0 · **자동 스냅샷 안 끼어들었다**.
- 다음: **리뷰 phase.** 리뷰가 볼 것은 「등재 판정 셋, 특히 ③(«stdlib 도 위반한다») 이
  변명이 아닌가」다.

## 2026-09-05 09:00 | loader-isolation | 리뷰 1/1 | 시도0

- **판정은 유지, 근거 둘이 무너졌다.** 백지 패스로 `fe4dd0d..HEAD` 를 다시 읽고 러너 인자 여섯(`-k`×2·`-p`·`--locals`·`-f`·`-t`)을 직접 때렸다 — 전수 `Ran 605 · OK · rc 0`(13.489초), `-k` 둘 다 OK, `-t .` 는 `ImportError` 로 도달 불가(재현). **열거형을 diff 밖에서 셌다**: `unittest.main` 이 로더에 심는 상태는 `testNamePatterns`(`main.py:151`)와 `_top_level_dir`(`loader.py:286`) **정확히 둘**이고 새 인스턴스가 둘 다 닫는다. 전역 대조도 재현(`sys.path` +4 · `defaultTestLoader` 축 셋 무변).
- **[R56-1] 「누출이 프로세스 경계를 넘는다」는 틀린 문장이었다(medium·95·고침).** `sys.path` 는 자식에게 상속되지 않는다 — 마커를 심고 `subprocess.run` 으로 확인해 `CHILD_HAS_MARKER=False`. 자식에 `E2E` 가 있는 이유는 `tests/test_passage_eval.py:47` 이 `-c` 소스에 `sys.path.insert(0, E2E)` 를 **직접 써 넣기** 때문이고, 부모가 완벽히 깨끗해도 똑같이 들어간다.
- **[R56-2] 변이 E 는 누출을 잰 적이 없다(medium·90·고침).** 사본에 `e2e/tempfile.py` 를 다시 심으니 실패가 자식 9건(`<string>` 프레임)과 **같은 프로세스 13건**(`test_quality_eval`, 프레임 없음)으로 갈리는데 **어느 쪽도 «남은 칸» 이 원인이 아니다** — 후자는 `test_quality_eval.py:17` 의 **살아 있는** insert 다. **일반화 — 「전역이 오염됐다」를 재려면 오염이 *남은 뒤*를 재야 한다. 오염이 *켜져 있는 동안* 터지는 것을 재면 다른 현상을 재고 그 값을 원래 항목에 적게 된다.** 항목의 틀도 그래서 틀렸다: 셋 중 둘이 **임포트 시점**(=`discover()` 중, 첫 테스트 전)에 돌아 위험은 「끝에 네 칸 남는다」가 아니라 **`e2e/` 가 전수 내내 `sys.path[0]` 에 앉아 있다**는 쪽이다.
- **[R56-3] ③ 은 사실이나 과장이다(low·85·고침).** `discover` 가 `loader.py:285` 에서 안 빼는 것은 원문 확인으로 참인데 그것이 「검사 불가」를 세우지는 못한다 — 앞뒤 대조가 저장소 몫 `e2e`×3 과 stdlib 몫 `tests`×1 을 **경로로** 가르고, 더 싼 처방(`if E2E not in sys.path` 세 줄)이 따로 있다. **`e2e` 칸이 셋으로 중복되는 것이 그 가드가 없다는 증거다.** `[5]` 값은 유지하고 문장만 고쳤다.
- **판정 ①은 축을 넓혀도 버틴다** — 38파일·고유 스템 38, 충돌이 stdlib **0** · `src/` 스템 **0** · `site-packages` **0**(테스트 phase 는 stdlib 만 봤다). 한도: 저장소 코드 **0줄** · `README.md`·`docs/specs/` 무변 · `data/crawl.db` sha256 `85c96744…5bda18` 무변 · `__pycache__` 0 · `pgrep -f websearch.serve` 0 · PR 무접촉 · 러너 규율 0회(누적 35). 고친 파일은 `docs/digest.md` 문장 둘뿐. 다음: **e2e phase**(21종 전수 회귀).
