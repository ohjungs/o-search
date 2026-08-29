# 반복 기록 009 — 2026-08-29 (계획 25~29 + 반복 147 탐색)

<!-- 아카이브. 수정·삭제 금지. history_current.md 에서 밀려난 원본 그대로다. -->

## 반복 136 — 계획 25 `number-flag` (계획 phase)

- **문제**: 숫자 인자 파서가 두 벌이고 함정이 세 번째로 나타났다. `str.isdigit()`/`int()`
  가 비ASCII 숫자를 받는 것을 `urls.py:57`(019)·`serve.py:323`(24)이 **각자 자기 자리에서만**
  막았다. `crawl.py:215 _number_flag` 는 그대로다 — 실측 `--max ٨٠` → **80**,
  `8_0` → 80, `' 80 '` → 80, `'+80'` → 80. `--max`·`--workers`·`--deadline` 이 같은 파서다.
- 반대 방향 갭도 실측: `serve.main(['prog','a.db','--port=8080'])` → **rc 2**.
  `crawl` 은 `--max=3` 을 받는데 `serve` 는 `--port=8080` 을 안 받는다.
- **짧은 경로가 아니다** — `design.md` 1절 트리거 셋(새 파일 후보 · 공개 함수 추가 ·
  3개 이상 파일). 갈림길은 **공유 파서의 자리** 하나고 후보 셋(A `cli.py` 새 모듈 ·
  B `crawl.py` + serve 가 crawl 임포트 · C `__init__.py`)을 계획서에 적어 설계로 넘겼다.
- 스텝 2개(1 파서 좁히고 crawl 이관 · 2 serve 가 같은 파서 사용, 의존 1). 계획서에
  **argparse 를 안 쓰는 이유**를 박아 뒀다 — `type=int` 는 `٨٠٨٠` 을 그대로 받는다(같은 버그).
- 다음: 설계 phase — `docs/design_number-flag.md` 에서 자리 판정.

## 반복 137 — 계획 25 설계 (`docs/design_number-flag.md`)

- **정한 것**: 공유 파서의 자리 = **새 모듈 `src/websearch/cli.py`**. 모듈 11개가 전부
  축 하나씩인 관용구를 따르고, `serve`·`indexer` 가 `crawl` 을 임포트하지 않게 한다.
- **버린 것**: ① "모으지 않고 `crawl._number_flag` 만 좁힌다"(3줄, 되돌리기 최고)는
  **문제를 안 푼다** — 019·24 가 각자 자기 파일에서 막은 것을 세 번째로 반복하고
  네 번째 자리를 남긴다. ③ `crawl.py` 에 두는 안은 파일이 안 늘어 "더 적게 쓰나" 에서
  앞섰지만 **의존 방향**에서 졌다(검색 서버가 크롤러를 임포트, 실측 +6.3ms).
- **탐침(3-2절)**: "좁혀도 412건이 그대로 통과한다" 를 실제로 깨봤다 — `--max -5`·
  `--deadline -1` 은 지금 `int()` 가 받아서 호출부 `< 1` 이 rc 2 를 내는데 좁히면
  **파서가** 거절하므로 경로가 바뀐다. 임시로 좁혀 전체를 돌리니 **Ran 412 · OK**.
  rc 2 는 유지되고 바뀌는 것은 stderr 문구뿐이며 어느 테스트도 문구를 안 박아 뒀다.
  커밋 없이 되돌렸다(`git status --short` 비었음 확인).
- `argparse` 재기각: `type=int` 가 `int("٨٠٨٠")` 를 그대로 받아 **같은 버그다.**
- 다음: 스텝 1 개발 — 실패하는 테스트부터(`--max ٨٠` 이 rc 2 이고 `crawl()` 안 불림).

## 반복 138 — 계획 25 스텝 1 (개발): `cli.py` 신설, `crawl` 이관

- **RED 를 먼저 봤다**: `crawl.main(["prog","http://a.com/","--max","٨٠"])` → **rc 0**.
  80페이지로 진짜 돌았다는 뜻이다(`crawled.assert_not_called()` 도 같이 죽었다).
- `src/websearch/cli.py` 신설 — `number_flag(args, name, default)` 하나.
  `crawl.py` 의 `_number_flag` 는 지웠고(`grep` 으로 잔존 참조 0 확인) 호출 셋이
  `cli.number_flag` 를 쓴다. 값 검사는 `value.isascii() and value.isdigit()`.
- **파서가 안 보는 것**: 범위. `--max ≥ 1`·`--workers ≥ 1` 검사는 호출부에 그대로 뒀다.
  `maximum=` 같은 인자를 파서에 넣으면 추측성 확장이다(설계 2절).
- 검증: `PYTHONPATH=src python3 -m unittest discover tests` → **Ran 413 · OK**(412 + 새것 1).
- 다음: 스텝 2 — `serve.py:318-327` 의 인라인 블록을 `cli.number_flag` 로.

## 반복 139 — 계획 25 스텝 2 (개발): `serve` 도 같은 파서

- **RED**: `serve.main(["prog","a.db","--port=8080"])` → rc 2. `crawl --max=3` 은 되는데
  `serve --port=8080` 은 안 되던 CLI 계약 불일치다.
- `serve.py` 의 인라인 검증 10줄 → `cli.number_flag(args, "--port", 8000)` + 상한
  `port is None or port > 65535` 셋째 줄. **상한만 이 명령의 것으로 남았다.**
- **변이 3종**(`PYTHONDONTWRITEBYTECODE=1`):
  - **M1 파서에서 `isascii()` 제거 → `test_crawl` 1건 + `test_serve` 2건이 함께 죽는다.**
    한 자리로 모였다는 증거다 — 한쪽만 죽으면 아직 두 벌이었을 것이다.
  - M2 붙임 형태에서 `del` 폭 1→2 → `test_flags_accept_the_equals_form` 죽음(시드가 샌다).
  - M3 상한 65535→65536 → `test_port_above_the_maximum...`(65536) 죽음. 24 가 세운
    양쪽 경계가 그대로 산다.
- 검증: **Ran 414 · OK**(412 → 413 → 414). 변이 되돌린 뒤에도 OK.
- 다음: 테스트 phase — 빠뜨린 것 찾기(`indexer.main` 은 계획 밖, e2e 17종은 e2e phase).

## 반복 140 — 계획 25 테스트 phase (갭 탐색)

- **처리(1건)**: `--max -5` 는 이 계획 전까지 **rc 0** 이었다. `int("-5")` → -5 이고
  `--max` 에는 `--workers`·`--deadline` 과 달리 `< 1` 검사가 없어 `crawl(seeds, -5)` 로
  갔다. 파서가 부호를 거르면서 rc 2 로 **조용히 고쳐졌는데 단언이 하나도 없었다** —
  `test_non_ascii_digits_and_python_int_forms_are_not_numbers` 에 `-5`·`--max=-5` 를 더했다.
  변이 확인: 파서 검사를 `value.lstrip('+-')` 로 되돌리면 이 테스트만 죽는다.
- **안 한 것(8점 미만 → `digest.md ## 다음 계획 후보 (테스트 phase 갭)`)**:
  `--max 0` 가드 비대칭[5] · 같은 플래그 두 번이면 뒤엣것이 시드로 샘[5] ·
  `--port 0` 단위 무커버[4] · `int_max_str_digits`[4].
- **`tests/test_cli.py` 를 안 만들었다.** `cli.number_flag` 는 새 public 함수지만
  호출부 둘이 각각 8·5가지로 덮고 **M1 변이가 양쪽을 함께 죽인다** — `test.md` 5절
  "이미 통합 테스트가 덮고 있는 것" 이다. 직접 테스트는 같은 것을 세 번째로 센다.
- 검증: `PYTHONPATH=src python3 -m unittest discover tests` → **Ran 414 · OK**.
- 다음: 리뷰 phase(백지 패스).

## 반복 141 — 계획 25 리뷰 (패스 A 백지 → 패스 B 대조)

- **패스 A 를 배경 없는 별도 세션에 넘겼다.** diff(`src`·`tests`만)와 저장소 경로만 주고
  `docs/` 는 못 열게 했다. 그쪽이 테스트·변이 2종·e2e 2종을 직접 돌리고 답했다.
- **[높음·반영] 모듈 이름이 실재 파손이었다.** README 13~15줄이
  `python -m websearch.cli crawl|index|serve` 를 안내한다 — 그 모듈은 없어서 rc 1 이었는데
  `cli.py` 를 만들자 **rc 0 에 아무 출력 없음**이 됐다(실측). 실패가 성공으로 위장됐다.
  → `src/websearch/flags.py` 로 개명. README 원래 상태(크게 실패)로 복귀 확인.
- **[중간·반영] docstring 이 없는 검사를 있다고 썼다** — "`--max ≥ 1`" 은 호출부에 없다.
  문구를 실제와 맞췄다(`--max` 는 0 도 받는다).
- **[중간·반영] `--deadline` 의 형태 지식이 여전히 두 벌이었다** —
  `any(a.startswith("--deadline=") ...)` 가 파서와 별개로 형태를 다시 셌다.
  파서가 닫은 함정을 호출부가 다시 열어 둔 꼴이다. **센티널**로 바꿔 그 줄을 없앴다.
- **센티널이 새 갭을 만들었고 변이가 잡았다**: `deadline = None` 줄을 지우는 M5 가
  **415건을 전부 통과**했다(센티널 객체가 `crawl()` 로 새면 예산 비교가 죽는다).
  `test_absent_deadline_is_none_not_the_parser_sentinel` 을 더하니 M5 가 죽는다.
- **[낮음·digest] README 명령 셋이 통째로 없다**[5] — 이번 계획은 이름 충돌만 피했다.
  중복 플래그 잔여물은 회귀가 아니라 기존 갭(이미 digest[5]).
- 패스 B 대조: 계획 `## 하지 않을 것` 넷(argparse · `indexer --query` · `urls.py` ·
  없는 DB 축) 전부 안 건드렸다. 기본값(`--max 100`·`WORKERS 8`·`--port 8000`) 그대로.
- 검증: **Ran 415 · OK**. 변이 M5 재확인(반영 전 통과 → 반영 후 죽음).
- 다음: e2e phase.

## 반복 142 — 계획 25 e2e + DONE

- **기존 e2e 17종 전부 rc=0**(회귀 잣대). 새 e2e 파일은 **안 만들었다** —
  `deadline_e2e.py:156` 이 이미 진짜 argv 로 붙임/띄움 형태를 섞어 준다.
- **실제 셸에서 CLI 12가지**: `crawl --max ٨٠`·`--max=٨٠`·`--max 8_0`·`--max -5`·
  `--workers ٨`·`--deadline ٦٠` 여섯 다 **rc 2** + 한 줄 메시지. `serve --port ٨٠٨٠`·
  `--port=99999`·`--port=abc` rc 2. **`serve --port=8123` 은 진짜 뜨고**
  `curl /search?q=김치` 가 결과를 냈다(전에는 rc 2). 거절 뒤 **8080 에 아무도 없다** —
  `٨٠٨٠` 이 조용히 8080 에 서버를 띄우던 자리를 포트로 직접 확인했다.
- 품질 기준 넷(`design_check`·`perf_search`·`perf_crawl`·`quality_eval`) 전부 rc 0.
- 아카이브: `plan_history_019.md`·`design_history_019.md`. `docs/e2e/number-flag/result.md`.
  `index.md` 25번 · `digest.md ## 완료` 한 줄.
- **재시도 0 · RED 0.** 단위 412 → **415건**.
- 다음: 지시받은 스텝이 끝났다 — 정지. 새 계획은 `digest.md` 후보 큐에서.

---

## 2026-08-29 20:40 | crawl-max-guard | 짧은 경로 | 시도0

- **지시받은 것을 골랐다.** 앞 세션이 판단 대기로 남긴 `digest.md ## 다음 계획 후보`
  `[5]`(`--max 0` 가드 비대칭). 중복 방지(`discover.md` 5절) 통과 — `index.md` 25개
  항목·`docs/patches/`(비었다) 어디에도 없다.
- **착수 전 실측했다**(로컬 서버가 요청을 세는 탐침, 카파시 1):

  | 준 인자 | rc | 서버가 받은 요청 | 출력 |
  |---|---|---|---|
  | `--max 0` | **0** | **0건** | `수집 0 페이지` |
  | `--workers 0` | 2 | 0건 | `--workers 는 1 이상의…` |
  | `--deadline 0` | 2 | 0건 | `--deadline 은 1 이상의…` |

- **판단: `--max 0` 도 rc 2 로 거절한다.** 근거는 대칭 자체가 아니라 **낸 결과의 모양**이다
  — `수집 0 페이지` + rc 0 은 **크롤이 아무것도 못 찾은 것과 구별되지 않는 성공**이다.
  이 저장소가 이미 두 번 닫은 실패 유형이다(21 `indexer-cli-guard` 의 "없는 DB 를 0건
  성공으로 합치지 않는다" · 25 리뷰의 "없는 명령이 rc 0 으로 위장된다").
- **0 을 일괄 금지한 것이 아니다.** `serve --port 0` 은 "임의 포트" 라는 뜻이 있어 그대로
  받는다 — 하한은 파서가 아니라 **플래그의 뜻**이 정한다. `flags.number_flag` 는 범위를
  여전히 안 본다(설계 019 의 결정 유지). 가드는 호출부 한 줄이다.
- TDD: 먼저 빨갛게(`FAILED (failures=1)`) 만들고 구현했다.
- 변이 3종 전부 잡힘(사본 + `PYTHONDONTWRITEBYTECODE=1`, 기준선 416 OK):
  M1 하한 제거(원래 버그) → 1건 실패 · M2 하한 `< 0`(0 을 다시 통과) → 1건 실패 ·
  **M3 하한 `< 2`(1페이지 크롤 사망) → 1건 실패**. M3 가 잡힌 것은 테스트에 **하한 자체를
  재는 대조군**(`--max 1` 이 `crawl(..., 1)` 로 간다)을 넣었기 때문이다 — 기존
  `--max=3` 단언은 `< 2` 를 못 본다.
- 곁가지 1건: `flags.number_flag` 독스트링이 "`--max` 는 0 도 받는다" 고 적고 있었다.
  변경으로 **거짓말이 된 주석**이라 같이 고쳤다(직교 편집 아님).
- 검증: 단위 **415 → 416건 OK** · e2e **17종 전부 rc=0** · 실측 재확인(`--max 0` → rc 2,
  요청 0건 / 대조군 `--max 1` → rc 0, 요청 2건).
- 브랜치 `loop/crawl-max-guard`(기점 `d2337fb`). 계획서·e2e 문서 없음(짧은 경로).
  `index.md` 26번에 한 줄 — 안 적으면 중복 방지가 이 작업을 못 본다.
- 집안일: `history_current.md` 293줄(상한 300)이라 **회전 먼저** 했다 —
  계획 21~24 를 `history_008.md` 로(293 → 139줄).

---

## 2026-08-29 21:15 | crawl-unknown-arg | 짧은 경로 | 시도0

- **탐색(`discover.md` 1절)을 순서대로 돌렸다.** 1~4순위가 전부 비었다 — 단위 416건 OK,
  e2e 17종 rc=0, `docs/candidates.md` 없음, `TODO/FIXME/HACK` **진짜 0건**(grep 이 2건을
  잡았지만 `serve.py:297`·`test_serve.py:115` 의 `\uXXXX` 표기 오탐이다 — `discover.md`
  1절이 경고하는 "그 줄이 실행되는 코드인지 확인한다" 에 걸린다).
  6순위 `digest.md ## 다음 계획 후보` 의 `[5]`(중복 플래그가 시드로 샌다)를 집었다.
- **후보가 적어 둔 것보다 넓었다**(digest `[7]` 관용구 — 처방은 그때의 추정이다).
  후보는 "같은 플래그를 두 번 주면" 이라고 적었는데, 실측하니 **모르는 플래그 전부**다:

  | 준 인자 | 고치기 전 | 시드로 샌 것 |
  |---|---|---|
  | `--maxx 3` (오타) | rc **0** · `수집 0 페이지` | `['http://a.com/', '--maxx', '3']` |
  | `-max 3` (하이픈 하나) | rc **0** | `['http://a.com/', '-max', '3']` |
  | `--max 3 --max 5` | rc **0** | `['http://a.com/', '--max', '5']` |
  | `--workers 2 --workers 0` | rc **0** | `0` 은 **검사조차 안 된다** |

  오타 하나면 크롤이 **기본값 100페이지로 조용히 돌고**, 새어 나간 토큰은 시드로
  요청까지 나갔다(`unknown url type: ':///robots.txt'`). 26 이 닫은 것과 같은 부류다.
- **뿌리를 먼저 찾았다**(ponytail: 호출부 전수). `indexer.main`·`serve.main` 은
  `len(args) != 1` 이 남은 것을 이미 rc 2 로 거른다 — **시드 개수가 가변인 `crawl` 만
  셀 수가 없어 구멍**이었다. 공통 헬퍼를 만들지 않고 그 한 곳에 가드 한 벌.
- TDD: 먼저 빨갛게(`FAILED (failures=1)`) 만들고 구현했다.
- **변이 4종 중 M4 가 처음엔 살아남았다** — `startswith("-")` 를 `not startswith("http")`
  로 **넓히는** 변이가 419건을 전부 통과했다. 등가 변이가 아니라 **다른 계약**이다:
  스킴 없는 시드(`example.com`)까지 rc 2 가 되는데, 오늘 그것은 `crawl()` 로 넘어가고
  왜 못 받았는지는 `crawl()` 이 시드마다 알린다. 가드의 경계를 재는 대조군을 넣어
  닫았다. **변이가 "덜 잡는" 쪽뿐 아니라 "더 잡는" 쪽으로도 있어야 한다.**
- 최종 변이 3종 전부 잡힘: M1 가드 무력화 · M2 `--` 만 봄(하이픈 하나 놓침) ·
  M4 과잉 거절.
- 검증: 단위 **416 → 419건 OK** · e2e **17종 전부 rc=0** · 실측 재확인(위 표 전부 rc 2).
- **곁가지는 안 고치고 후보로 남겼다**: 스킴 없는 시드 `example.com` 이 rc 0 에
  `unknown url type` 을 낸다 — 시드 검증 계약이라 이 가드의 범위 밖이다(`digest.md`).
- 브랜치 `loop/crawl-max-guard` 계속. `index.md` 27번에 한 줄.

## 2026-08-29 22:05 | readme-commands | 짧은 경로 | 시도0

- **내가 저지른 오류를 되돌린 스텝이다.** 25 리뷰가 `cli.py` 를 `flags.py` 로
  개명했는데 README 는 `python -m websearch.cli crawl ...` 세 줄을 그대로 뒀다.
  실측: `PYTHONPATH=src python3 -m websearch.cli --help` → `No module named websearch.cli`.
- **`flags.py` docstring 은 이 사실을 이미 알고 있었다** — "README 가
  `python -m websearch.cli ...` 를 안내하는데 그 모듈은 없다(rc 1)" 고 적어 두고
  자기 이름을 `cli` 로 안 가져간 근거로 썼다. 알면서 안 고친 것이고, 25 는
  직교 편집이라 미뤘다. **알고 있다는 기록은 고쳐졌다는 뜻이 아니다.**
- 실측으로 다시 썼다. 로컬 `http.server` 로 문서 2장을 띄우고 crawl→indexer→serve
  를 끝까지 돌렸다(외부 네트워크 안 침):

  | 명령 | 결과 |
  |---|---|
  | `crawl http://127.0.0.1:8731/index.html --max 5` | `수집 2 페이지` rc 0 |
  | `indexer data/crawl.db` | `2 문서 색인` rc 0 |
  | `indexer data/crawl.db --query 검색` | 제목·URL·스니펫 1건 |
  | `serve data/crawl.db --port 0` | `/` 200 · `/search?q=` JSON 1건 |

- **곁가지 둘이 같이 나왔다**: `python` 은 이 환경에 없고(`command not found: python`),
  `PYTHONPATH=src` 가 빠져 있었다(설치 단계가 없어 그것 없이는 임포트 실패).
  README 의 `unittest` 줄도 같은 두 오류를 갖고 있었다 — 그대로 치면 안 돈다.
- **검사를 하나 남겼다.** 깨진 것이 코드가 아니라 **코드와 문서 사이**라
  소스만 보는 단위 테스트로는 영원히 안 잡힌다. `tests/test_readme.py` 가 README 를
  입력으로 읽어 `-m websearch.<모듈>` 을 뽑고 `find_spec` 으로 실재를 본다
  (임포트 안 함 · 네트워크 없음 · 서브프로세스 없음).
- **변이 검증에서 검사 명령 자체가 거짓 초록을 냈다.** M2(`python3`→`python`)를
  `sed -i '' '0,/re/s//.../'` 로 심었더니 `OK` 가 나왔다 — 잡은 게 아니라
  **BSD sed 가 `0,/re/` 를 조용히 무시해 변이가 안 심어진 것**이었다. Python 으로
  다시 심어 확인하니 잡힌다. `SKILL.md` 가 경고하는 "검사 명령이 돌아가면서 틀린
  답을 낸다" 의 재발이다 — **변이가 실제로 심어졌는지를 먼저 단언**해야 한다
  (이후 `assert n != t` 를 넣었다).
- 최종 변이 3종 전부 잡힘: 모듈 오타(`websearch.index`) · `python3`→`python` · `cli` 부활.
- 검증: 단위 419 → **422건 OK**. 브랜치 `loop/readme-commands`(기점 `main` `8224207`).

## 2026-08-29 22:40 | seed-scheme-guard | 짧은 경로 | 시도0

- 근거: `digest.md ## 다음 계획 후보` `[4]` — 27 의 변이 M4 가 드러내고 일부러 안
  건드린 곁가지. 실측: `crawl example.com --max 1` → stderr `unknown url type:
  ':///robots.txt'` + `수집 0 페이지` **rc 0**.
- **실측이 앞 세션 권고와 갈렸고, 실측을 따랐다.** 권고는 "0페이지 수집이면 rc 1":

  | 실측 | 결과 | 이게 말하는 것 |
  |---|---|---|
  | `urls.normalize("example.com")` | `'example.com'` (그대로) | `None` 은 IDNA 실패에만 — "시드가 안 살아남는다" 갈래는 **안 밟힌다** |
  | `normalize("javascript:alert(1)")` | 그대로 | 스킴 검사가 **아무 데도 없다** |
  | `links.py:30` | `http(s)` 만 통과 | 계약은 **이미 있다**. 시드만 안 지나갔다 |
  | `crawl http://nonexistent.invalid/` | `수집 0 페이지` rc 0, stderr 없음 | robots 를 못 받아 **차단 처리**(예의상 옳다) |

- **(ㄷ) 이 계약을 갈랐다.** "0페이지면 rc 1" 로 하면 robots 가 정당하게 막은
  사이트와 도달 불가 호스트가 **오류**가 된다 — 예의를 오작동으로 보고하는 쪽이다.
  절대 조건(크롤 윤리를 낮추지 않는다)의 반대 방향이라 택하지 않았다.
- 골라 든 계약: **시드 스킴 화이트리스트 → rc 2.** 새 계약이 아니라 `links.py` 가
  이미 건 조건의 구멍을 시드 쪽에서 메운 것이다. 경계를 양쪽에서 고정하는 대조군:
  `https://nope.com/` 은 404 로 0페이지지만 **예외가 아니다**(rc 0) — "거절당했다" 와
  "받아 갔는데 못 가져왔다" 는 다른 일이다.
- `urls.scheme_of` 가 이미 있어 **URL 을 다시 파싱하는 자리를 새로 안 만들었다.**
- **변이가 형제 구멍을 하나 더 냈다.** M2(`if not ascii_seeds` → `if seeds and not
  ascii_seeds`)가 살아남았다 — 등가 변이가 아니라 **커버 안 된 경로**였다:
  `crawl --max 1` 은 플래그가 `len(argv) < 2` 를 채워 usage 검사를 통과하고
  시드 0건으로 `수집 0 페이지` rc 0 이었다. "다 거절당해 0건" 과 "처음부터 0건" 은
  크롤이 못 도는 이유로는 같아서 `seeds and` 를 빼 한 자리에서 막았다.
  덤: `file:///etc/passwd`·`javascript:`·`mailto:` 도 시드로 안 들어간다.
- 판정은 `crawl()`, rc 변환만 `main`. 미지 인자 가드(`-` 로 시작)와 **합치지 않았다** —
  합치면 27 의 M4 가 경고한 다른 계약으로 조용히 넓어진다. 27 이 세운 대조군
  (`main` 은 `example.com` 을 그대로 넘긴다)이 그대로 통과하는 것이 그 증거다.
- 최종 변이 6종 전부 잡힘: 화이트리스트 무력화 · 빈 시드 통과 · 가드 제거 ·
  하나라도 나쁘면 거절(계약 넓히기) · `ftp` 슬쩍 허용 · rc 2→0.
- 검증: 단위 422 → **428건 OK** · e2e **17종 전부 rc=0** · 실측 재확인
  (`example.com` rc 2 · `--max 1` 단독 rc 2 · `nonexistent.invalid` rc 0 유지).

## 2026-08-29 23:20 | (없음) | 계획 · 탐색 | 시도0

- **코드 0줄.** 회전·색인 번호·탐색 셋을 확인했고 전부 "할 일 없음" 이었다.
- 회전 **안 함**: `docs.md` 3절 방아쇠는 20회 또는 300줄인데 실측 284줄·11항목.
  앞 세션의 "다음 스텝은 회전 먼저" 는 방아쇠가 아니라 예고였다. 다음 항목이 붙으면
  넘으니 그때 25~29 를 `history_009.md` 로 뺀다.
- `index.md` 번호 불일치(커밋 제목 `28` vs 색인 `29`) 기록은 **실제와 맞아 그대로 뒀다.**
- 탐색 0건: 실패 0(428 OK) · 린터 없음 · 코드 `TODO` 0 · 패치 0 · 보류 0 · 활성 계획 0.
  6순위 후보는 남았으나 이 밤 계획 4건으로 `discover` 6절 상한 3개 초과 → 정지.
- **겹쳐 돈 구간이 있었다.** "앞 세션이 57분 끊겼다" 는 전제로 같은 시드 스킴 건에
  착수했는데 앞 세션이 살아서 `876d969` 로 먼저 끝냈다. 작업 트리의 미커밋분이 그
  커밋과 동일해(`git diff loop/readme-commands` 빈 출력) 버려도 잃은 것이 없다.
  **갈랐어야 할 것은 침묵의 길이가 아니라 `git status` 였다.**
