#!/usr/bin/env python3
"""변이 앵커가 파일에 **정확히 하나**인지 적용 전에 잰다.

왜 있나 — 2026-11-01 반복 792 에 변이 M8 이 **거짓 생존**을 냈다. 앵커
`if not missing:` 가 `tests/test_docs.py` 에 둘이라 `str.replace(앵커, …, 1)` 이
**남의 함수**를 고쳤고, 남의 함수는 그 변경에 무던해 전수가 초록이라 「생존」으로
읽혔다. 「생존」은 「테스트가 약하다」로 읽히고 그 판정이 다음 테스트를 더 짜게
만들므로, **재지 못한 것이 테스트 설계로 흘러든다.**

**세는 술어가 적용기와 같아야 한다.** `grep -c` 는 **줄**을 세고 적용기는
**부분문자열**을 센다 — 실물 `tests/test_docs.py` 에서 둘이 갈리는 자리가 7개이고
그중 하나가 하필 `dup_def_gap` 의 픽스처다(`"class A:\n    def go(self):\n …"` —
`go(self):\n` 가 **한 물리 줄 안에 두 번**). 그래서 여기서는 `str.count` 와 **같은
수**가 나오게 센다(겹치는 적중은 세지 않는다 — `count` 의 규약이다).

쓰는 법:

    scripts/mutate.py --check <파일> <앵커>

종료 코드는 이 저장소 관용구를 따른다 — **`2` 는 판정이 아니라 「재지 못했다」** 다.
`0` 앵커가 유일하다 · `2` 0곳이거나 여럿이다(또는 파일을 못 읽었다).
판정은 **stdout 의 마지막 한 줄**로 다시 찍으므로 `| tail -1` 을 붙여도 산다
(`scripts/verdict.sh` 와 같은 관례).

설계는 `docs/design_mutant-anchor-unique.md` · 계약은 그 문서의 「계약」 절.
"""
import pathlib
import sys

USAGE = "쓰는 법: scripts/mutate.py --check <파일> <앵커>"


def anchor_sites(text, anchor):
    """앵커가 든 줄 번호 전부. **`text.count(anchor)` 와 같은 수**를 돌려준다.

    겹치는 적중을 안 세는 것이 `str.count` 의 규약이라 보폭을 `len(anchor)` 로
    둔다 — 보폭 1 로 두면 `"aa"` 를 `"aaa"` 에서 둘로 세어 **적용기와 갈린다**.
    적용기와 갈리는 판정은 이 자가 닫으려는 사고의 새 통로다.
    """
    sites, at = [], text.find(anchor)
    while at != -1:
        sites.append(text.count("\n", 0, at) + 1)
        at = text.find(anchor, at + len(anchor))
    return sites


def verdict(말, rc):
    """판정을 마지막 한 줄로 찍고 종료 코드를 돌려준다."""
    print("── %s rc=%d" % (말, rc))
    return rc


def check(path, anchor):
    """앵커 유일성만 본다. **파일을 쓰지 않는다.**"""
    if not anchor:
        return verdict("앵커가 빈 문자열이다 — 재지 못했다", 2)
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as 왜:
        return verdict("파일을 못 읽었다(%s) — 재지 못했다" % 왜.strerror, 2)
    sites = anchor_sites(text, anchor)
    if len(sites) == 1:
        return verdict("앵커 유일 — %s:%d" % (path, sites[0]), 0)
    if not sites:
        return verdict("앵커 0곳 — **썩었다**. 파일이 움직였으니 앵커를 다시 뜬다"
                       " (좁히는 것이 아니다) — 재지 못했다", 2)
    print("앵커가 %d곳에 있다 — 적용은 **첫 하나**만 바꾸므로 나머지가 조용히 남고,"
          " 그 초록은 「생존」이 아니라 「재지 못했다」다. 걸린 자리:" % len(sites))
    for 줄 in sites:
        print("  %s:%d" % (path, 줄))
    return verdict("앵커 %d곳 — 유일해지도록 **넓혀** 다시 뜬다(앞뒤 줄을 붙인다)"
                   " — 재지 못했다" % len(sites), 2)


def main(argv):
    if len(argv) == 4 and argv[1] == "--check":
        return check(argv[2], argv[3])
    return verdict("인자가 맞지 않는다 — 재지 못했다. %s" % USAGE, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
