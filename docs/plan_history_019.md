# 계획 25 — number-flag: 숫자 인자 파서를 한 자리로 모은다

## 문제

**같은 함정이 파일 세 곳에서 되풀이됐다.** `str.isdigit()`·`int()` 가 비ASCII
숫자(`٨`=아랍-인도)를 받아 **운영자가 친 적 없는 값으로 조용히 돈다**.

- 019 `normalize-gaps` — `urls.py:57` 에서 처음 밟았다. 거기서만 `isascii()` 를 더했다.
- 24 `serve-port-guard` — `serve.py:323` 에서 다시 밟았다. 거기서만 또 더했다.
- **지금** — `crawl.py:215 _number_flag` 는 아직 그대로다. 실측(2026-08-29):

```
crawl._number_flag(['--max','٨٠'], '--max', 100)  ->  80      # 조용히 80페이지
crawl._number_flag(['--max','8_0'], '--max', 100) ->  80      # 파이썬 언더스코어 구분자
crawl._number_flag(['--max',' 80 '], '--max', 100)->  80      # 앞뒤 공백
crawl._number_flag(['--max','+80'], '--max', 100) ->  80
```

`--max`·`--workers`·`--deadline` 셋이 같은 파서를 쓰므로 셋 다 해당된다.
`--workers ٨` 는 워커 8개로, `--deadline ٦٠` 은 예산 60초로 돈다.

**반대 방향의 갭도 있다.** `serve.main` 은 붙임 형태를 모른다 — 실측:

```
serve.main(['prog','a.db','--port=8080'])  ->  rc 2 "usage: ... [--port N]"
```

`crawl` 은 `--max=3` 을 받는데(23 `deadline-patches`) `serve` 는 `--port=8080` 을
안 받는다. 거절이 조용하지는 않지만 **CLI 계약이 명령마다 다르다.**

## 목표

숫자 플래그 파싱을 **한 함수**로 모으고, 그 한 자리에서 `[0-9]+` 만 받는다.
`crawl`·`serve` 두 CLI 가 같은 형태(`--name N` / `--name=N`)와 같은 거절 규칙을 쓴다.

## 기대 결과

- `crawl --max ٨٠` / `--max 8_0` / `--max ' 80 '` → rc 2, `crawl()` 안 불림
- `serve --port=8080` → 8080 으로 뜬다 (지금은 rc 2)
- `serve --port ٨٠٨٠` → rc 2 (24 가 세운 계약 유지)
- 기존 412건 전부 OK

## 설계가 필요하다 — 다음 반복

`design.md` 1절 트리거 셋에 걸린다: **새 파일 후보** · **공개 함수 추가** ·
**3개 이상 파일**(`crawl.py`·`serve.py`·테스트 둘). 짧은 경로가 아니다.

갈림길은 **공유 파서를 어디 두는가** 하나다. 후보는 셋이고 어느 쪽이든 동작한다:

- **A** 새 모듈 `src/websearch/cli.py` — 축이 맞지만 파일이 는다
- **B** `crawl.py` 에 두고 `serve` 가 `crawl` 을 임포트 — 파일은 안 늘지만
  **검색 서버가 크롤러를 임포트한다**(`concurrent.futures`·`fetcher`·`frontier`…)
- **C** `src/websearch/__init__.py`(현재 `__version__` 한 줄) — 새 파일도 새 의존도
  없지만 패키지 `__init__` 에 CLI 헬퍼가 있는 것은 놀랍다

판정은 `docs/design_number-flag.md` 에서 한다. **이 계획서는 자리를 안 정한다** —
아래 스텝은 자리를 `<파서모듈>` 로 쓴다.

## 스텝

### 스텝 1 — 파서를 좁히고 `crawl` 을 옮긴다 · 의존: 없음

`crawl.py:215 _number_flag` 를 설계가 정한 `<파서모듈>.number_flag` 로 옮기면서
값 검사를 `int()` 에서 **`value.isascii() and value.isdigit()`** 로 바꾼다
(`serve.py:323` 이 이미 쓰는 식 그대로 — 새로 짓지 않는다).
음수는 이제 파서가 거절한다: `--max -5` 는 rc 2 그대로고 문구만 바뀐다.

- 먼저 쓸 실패 테스트 (`tests/test_crawl.py`): `--max ٨٠`·`--workers ٨`·
  `--deadline ٦٠`·`--max 8_0`·`--max ' 80 '` 가 각각 rc 2 이고
  `mock.patch("websearch.crawl.crawl")` 가 **안 불린다**
- 완료 기준: `PYTHONPATH=src python3 -m unittest discover tests` 전부 OK,
  위 테스트가 옮기기 전 코드에서는 실패하는 것을 눈으로 본다(`dev.md` 0절 2번)

### 스텝 2 — `serve.main` 이 같은 파서를 쓴다 · 의존: 1

`serve.py:318-327` 의 인라인 블록을 `<파서모듈>.number_flag(args, "--port", 8000)`
호출로 바꾸고 범위 검사(`0~65535`)만 `serve` 에 남긴다.

- 먼저 쓸 실패 테스트 (`tests/test_serve.py` `TestCliArgs`):
  `--port=8080` 이 rc 0 이고 `make_server` 가 8080 을 받는다
- 완료 기준: `TestCliArgs` 기존 8건 + 새것 전부 OK. 특히
  `test_non_ascii_digits_are_not_a_port`·`test_the_highest_real_port_still_serves`·
  `test_port_above_the_maximum_is_refused_not_a_traceback` 가 그대로 통과
- 변이로 확인: 파서에서 `isascii()` 를 떼면 `crawl`·`serve` **양쪽** 테스트가 죽는다
  (한 자리로 모았다는 증거다 — 한쪽만 죽으면 안 모인 것이다)

## 하지 않을 것

- **`argparse` 도입** — 세 CLI 의 종료 코드·한국어 문구·usage 를 전부 다시 쓰는 일이고
  `type=int` 는 `٨٠٨٠` 을 그대로 받는다(같은 버그). 지금 문제를 안 푼다
- **`indexer.main` 의 `--query`** — 문자열 플래그다. 붙임 형태를 모르지만 조용히
  새지 않고 usage rc 2 로 죽는다. 숫자 축이 아니라 이 계획 밖이다
- **`urls.py:57` 의 포트 검사** — URL 파싱이지 CLI 인자가 아니다. 축이 다르다
- **`serve` 의 없는 DB 경로** — `TestMissingDb` 가 계약으로 박아 뒀다 (24 의 결론)
- 크롤 동작·기본값(`--max 100`·`WORKERS 8`) 변경
