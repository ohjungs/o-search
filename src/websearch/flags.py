"""CLI 인자 파싱. 지금은 숫자 플래그 하나다.

**여기 있는 이유는 함정이 파일마다 따로 막혔기 때문이다.** `str.isdigit()`·`int()` 가
비ASCII 숫자를 받는 것을 `urls.py`(019)와 `serve.py`(24)가 각자 자기 자리에서만
막았고, `crawl.py` 가 세 번째 자리였다 — 파서가 두 벌이면 함정도 두 벌이다.
새 CLI 플래그는 여기를 거친다 (docs/design_number-flag.md).

이름이 `cli` 가 아닌 이유: README 가 `python -m websearch.cli ...` 를 안내하는데
그 모듈은 없다(rc 1). 여기가 그 이름을 가져가면 **없는 명령이 rc 0 으로 조용히
성공한다** — 실패를 성공으로 위장하는 쪽이 더 나쁘다.
"""


def number_flag(args, name, default):
    """`--name N` 과 `--name=N` 을 뽑아 args 에서 지운다.

    없으면 default, **`[0-9]+` 하나가 아니면 None** — 그때 args 는 안 건드린다
    (호출부가 어차피 usage 로 죽는다).

    **두 형태를 여기 한 자리에서 안다** — 호출부가 각자 알면 하나만 고쳐지고
    나머지는 조용히 무시된다(실제로 그랬다: `deadline-patches`). 모르는 형태를
    args 에 남기면 그것이 **시드로 새어** 크롤이 기본값으로 돈다.

    범위는 안 본다 — 상한·하한이 호출부마다 다르다(`--workers ≥ 1`·`--port ≤ 65535`,
    `--max` 는 0 도 받는다). 음수는 파서가 거절한다 — `-` 는 숫자가 아니다.
    """
    equals = name + "="
    for i, arg in enumerate(args):
        if arg == name:
            value, cut = (args[i + 1] if i + 1 < len(args) else ""), 2
        elif arg.startswith(equals):
            value, cut = arg[len(equals):], 1
        else:
            continue
        # int() 로 바로 받으면 안 된다 — `int("٨٠")` 은 **80 이고**(아랍-인도 숫자),
        # `int("8_0")`·`int(" 80 ")`·`int("+80")` 도 전부 80 이다. `isdigit()` 만으로도
        # `٨٠` 이 참이라 모자란다. isascii() 를 같이 봐야 `[0-9]+` 가 된다.
        if not (value.isascii() and value.isdigit()):
            return None
        del args[i:i + cut]
        return int(value)
    return default
