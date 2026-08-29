# 설계 25 — number-flag: 공유 숫자 파서를 어디 두는가

계획: `docs/plan_number-flag.md`. **정할 것은 하나다** — `--name N`/`--name=N` 을
읽는 함수의 **자리**. 함수 본문은 이미 정해져 있다(아래 4절).

## 1. 대안 — 서로 다른 출발점에서

### ① 최소 (사다리 1·2번) — 모으지 않는다

`crawl.py:215 _number_flag` 의 `int()` 만 좁히고 `serve.py:318-327` 은 그대로 둔다.
**3줄이고 되돌리기가 가장 쉽다.**

**기각.** 이 계획의 문제는 "비ASCII 숫자가 통과한다" 가 아니라 **"같은 함정이 파일마다
따로 막힌다"** 다. 019 가 `urls.py` 에서, 24 가 `serve.py` 에서 각자 막았고 이 안은
`crawl.py` 에서 세 번째로 각자 막는 것이다 — **네 번째 자리를 그대로 남긴다.**
`serve` 가 `--port=8080` 을 못 받는 CLI 계약 불일치도 안 없어진다.
사다리 1번은 "안 만들어도 되나" 를 묻지 `문제를 안 풀어도 되나` 를 묻지 않는다.

### ② 정공법 — 새 모듈 `src/websearch/cli.py`

`number_flag(args, name, default)` 하나만 있는 파일. `crawl`·`serve` 가 임포트한다.

### ③ 있는 것으로 때운다 — `crawl.py` 에 두고 `serve` 가 임포트

파일이 안 는다. `from websearch.crawl import number_flag`.

(넷째로 `__init__.py`(현재 `__version__` 한 줄)에 두는 안도 계획서에 적었지만,
②·③ 과 같은 축의 변주라 따로 비교하지 않는다 — 판정은 ③ 과 같고 "패키지
`__init__` 에 CLI 헬퍼" 라는 놀라움만 더한다.)

## 2. 판정 — ② `src/websearch/cli.py`

기준 순서대로 본다.

| 기준 | ② `cli.py` | ③ `crawl.py` |
|---|---|---|
| 되돌릴 수 있나 | 커밋 하나 revert | 커밋 하나 revert (동점) |
| 더 적게 쓰나 | 파일 +1, 코드는 같음 | 파일 +0 — **③ 우세** |
| 기존 것과 맞나 | **축 하나 = 파일 하나** 관용구 그대로 | 크롤 루프 축에 CLI 파싱이 섞인다 |
| 다음이 편한가 | `indexer.main` 이 세 번째 호출자다 | **indexer 가 crawl 을 임포트하게 된다** |

**"더 적게 쓰나" 에서 ③ 이 앞서지만 뒤의 두 기준이 뒤집는다.** 결정적인 것은
**의존 방향**이다. ③ 은 검색 서버가 크롤러를 임포트한다 —
`concurrent.futures`·`fetcher`·`links`·`urls`·`frontier`·`robots`·`store` 가 딸려 온다.
실측(2026-08-29): `websearch.serve` 를 이미 임포트한 뒤 `websearch.crawl` 을 더 임포트하는
비용 **6.3ms**. 6ms 자체는 서버 기동에서 문제가 아니다 — **문제는 의미다.**
`serve.py` 첫 줄에 `from websearch.crawl import ...` 가 있으면 3시에 그것을 읽는 사람이
"검색 서버가 크롤러의 무엇을 쓰는가" 를 먼저 풀어야 한다.

이 저장소의 모듈 11개는 전부 **축 하나씩**이다(`urls`=URL, `links`=링크, `robots`,
`store`, `frontier`, `fetcher`, `extract`, `indexer`, `serve`, `crawl`). CLI 인자 파싱은
그중 어느 축도 아니다. **관용구를 따르는 쪽이 ② 다.**

`cli.py` 는 함수 하나로 시작하고 **커지면 그때 나눈다.** 지금 넣지 않는 것:
문자열 플래그 헬퍼(`indexer --query` — 계획 밖), 불리언 플래그, usage 생성기.
추측성 확장은 기준 4번에서 감점이다.

**되돌리기 수단: ③ 커밋 하나로 revert.** 피처 플래그는 없다(`project.md` 에 플래그
메커니즘이 없고, CLI 인자 파싱은 켜고 끌 대상이 아니다). 덧붙이기(②번 수단)도 아니다 —
`crawl._number_flag` 를 남겨 두면 **두 벌이 그대로**여서 이 계획을 부정한다.

## 3. 가장 위험한 가정을 깼다 (`design.md` 3-2절)

**가정:** "`int()` → `isascii() and isdigit()` 로 좁혀도 기존 412건이 그대로 통과한다."
틀리면 설계가 아니라 계획이 무너진다 — 특히 `--max -5`·`--deadline -1` 은 지금
`int()` 가 **받아서** 호출부의 `< 1` 검사가 rc 2 를 내는데, 좁히면 **파서가** 거절한다.
경로가 바뀌므로 rc 가 유지된다는 보장이 없다.

**탐침 실측(2026-08-29, 커밋 없이 되돌림):** `crawl.py:215` 본문만 4절의 형태로 바꾸고
`PYTHONPATH=src python3 -m unittest discover tests` → **Ran 412 tests · OK.**
`test_deadline_flag_errors_return_usage_not_traceback`(`--deadline -1` 포함)과
`test_equals_form_errors_return_usage_not_a_default_run` 이 그대로 통과한다.
rc 는 2 로 같고 바뀌는 것은 stderr 문구뿐이다 — 어느 테스트도 문구를 안 박아 뒀다.
**가정은 참이다. 개발로 간다.**

e2e 도 같이 봤다: `deadline_e2e.py:156` 이 `--deadline=%d`·`--workers=8`(붙임) 과
`--max N`(띄움) 을 섞어 준다 — 둘 다 유지되는 형태다. 음수·비ASCII 를 주는 e2e 는 없다.

## 4. 함수 본문 — 이미 정해졌다

`serve.py:323` 이 쓰는 식(`value.isascii() and value.isdigit()`)을 **그대로 옮긴다.**
새로 짓지 않는다(사다리 2번). 두 형태를 한 루프에서 처리한다:

```python
def number_flag(args, name, default):
    equals = name + "="
    for i, arg in enumerate(args):
        if arg == name:
            value, cut = (args[i + 1] if i + 1 < len(args) else ""), 2
        elif arg.startswith(equals):
            value, cut = arg[len(equals):], 1
        else:
            continue
        if not (value.isascii() and value.isdigit()):
            return None
        del args[i:i + cut]
        return int(value)
    return default
```

**계약:** 없으면 `default`, `[0-9]+` 하나가 아니면 `None`(그때 `args` 는 안 건드린다 —
호출부가 어차피 usage 로 죽는다). **음수는 이제 파서가 거절한다.** 범위는 파서가 안
본다 — `--max ≥ 1`·`--workers ≥ 1`·`--port ≤ 65535` 는 호출부마다 다르고, 파서에
넣으면 `maximum=` 같은 추측성 인자가 생긴다.

## 5. 안 고른 것을 다시 안 꺼내려고 적는다

- **`argparse`** — 계획서 `## 하지 않을 것` 과 같은 이유다. `type=int` 는
  `int("٨٠٨٠")` 을 그대로 받아 **이 버그를 안 고친다.** 종료 코드·한국어 문구·usage 를
  세 CLI 에서 다시 쓰는 값만 치른다.
- **`re.fullmatch(r"[0-9]+", value)`** — 같은 일을 `re` 임포트를 더해서 한다.
  `isascii() and isdigit()` 은 이미 이 저장소 두 곳(`urls.py:57`·`serve.py:323`)의
  관용구다. 셋째 표기를 들이면 다음 사람이 어느 것이 맞는지 묻게 된다.
