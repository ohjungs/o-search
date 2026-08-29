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

**반복 97~122 는 `history_006.md`, 123~128(계획 020 `deadline` 전체)은
`history_007.md`, 계획 21~24(짧은 경로 3건 + 보류 패치 소진, 2026-08-29 14:20~17:40)는
`history_008.md` 로 밀려났다** (2026-08-29 회전 3회).

---

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
