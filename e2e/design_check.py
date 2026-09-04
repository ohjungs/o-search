#!/usr/bin/env python3
"""컨셉 디자인 4축(`docs/specs/concept.md:49-54`)을 실제 응답 바이트로 판정한다.

    1. 결과 페이지 LCP 1.5s 이하    2. JS 번들 50KB(gzip) 이하
    3. 대비 — 텍스트 4.5:1 · 비텍스트 3:1   4. 모바일(360px)에서 가로 스크롤 없음

실행: PYTHONPATH=src python3 e2e/design_check.py
종료: 0 통과 · 1 기준 위반 · 2 측정 불능

측정 불능(2)을 0 과 가르는 이유는 `e2e/quality_eval.py` 와 같다 — 잴 것이 없어진
검사는 조용히 통과하면 안 된다. 색 토큰을 통째로 지워도 "위반 0건"은 참이 된다.

ponytail: **1번과 4번은 대리 지표다.** LCP 와 레이아웃은 브라우저 없이 못 잰다.
헤드리스 브라우저를 붙이는 것은 의존성 추가라 야간에 할 일이 아니어서, LCP 를
*나쁘게 만드는 원인*(추가 왕복·문서 크기·서버 시간)과 360px 을 *넘치게 만드는
원인*(viewport 없음·고정폭·안 접히는 긴 문자열)을 대신 잰다.
못 잡는 것: 브라우저 레이아웃/페인트 시간, 웹폰트(지금 0개), 실제 네트워크 RTT.
업그레이드 경로: 사람이 헤드리스를 붙이기로 하면 Lighthouse LCP 로 1번을 교체한다.
"""
import gzip
import os
import re
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

from websearch import indexer, serve

JS_BUDGET = 50 * 1024      # concept.md:50 — gzip 기준
MIN_CONTRAST = 4.5         # concept.md:53
MIN_CONTRAST_NONTEXT = 3.0 # WCAG 2.1 SC 1.4.11 — 비텍스트 UI 지시자. concept.md 는 텍스트만 적었다
MOBILE_WIDTH = 360         # concept.md:54
ROOT_FONT_PX = 16          # rem→px 환산. 사용자가 기본 글꼴을 키우면 실제로는 더 크다
DOC_BUDGET = 100 * 1024    # LCP 대리: 왕복이 1이므로 전송 시간의 유일한 변수다
SERVER_BUDGET_MS = 300     # LCP 대리: 서버 생성 시간. perf_search.py 의 예산과 같은 값

# **이름만 여기 있고 값은 매번 CSS 에서 읽는다** (docs/design_search-ui.md 갈림길 2).
# 검사기가 색값을 들고 있으면 CSS 를 고쳐도 옛 값으로 통과를 내준다 — 드리프트한다.
PAIRS = [
    ("--fg-body", "--bg-page"),
    ("--fg-body", "--bg-input"),     # 입력창 안의 글자
    ("--fg-muted", "--bg-page"),
    ("--fg-url", "--bg-page"),
    ("--fg-snippet", "--bg-page"),
    ("--fg-link", "--bg-page"),
    ("--fg-button", "--bg-button"),
]

# 비텍스트 UI 지시자는 다른 자로 잰다(3:1). 링의 이웃이 페이지 배경인 것은
# **outline-offset 이 0 보다 클 때뿐**이고, 그 전제는 이제 단언이 아니라 `focus_rule` 이
# 매 실행 확인하는 조건이다 — 0 이 되는 날 여기서 재는 대신 측정 불능으로 멈춘다.
# 그때 --bg-button 짝을 적을지가 열린다(status.md `## 사람이 정할 것` 2번).
NONTEXT_PAIRS = [("--focus", "--bg-page")]

# 짝이 없어도 되는 토큰과 **그 사유**. 아래 커버리지 강제가 이름을 안 보므로,
# 여기 사유를 적는 것만이 검사를 빠져나가는 길이다 — dict 라 사유 없이는 문법이 안 된다.
# 사유가 곧 그때까지의 기록이다(설계 `## 계약`) — 틀린 사유를 적으면 문이 거짓으로 열린다.
NO_PAIR = {"--line": "구분선(header·pager)은 순수 장식이다. 입력창 테두리는 판단 보류 — "
                     "라이트에서 --bg-input 이 --bg-page 와 같은 #ffffff 라 이 1.34:1 선이 "
                     "입력창의 유일한 경계다(다크도 1.27:1). SC 1.4.11 대상일지는 계획 43 범위 밖"}

PAGES = {
    "http://a.test/%d" % i: ("<html><head><title>김치찌개 만드는 법 %d</title></head>"
                             "<body><p>김치 와 돼지고기를 넣고 끓인다. 김치 김치</p>"
                             "</body></html>" % i)
    for i in range(12)
}


# ---------- WCAG 2.x 상대휘도 ----------

def _channel(c):
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    """#rrggbb → 상대휘도. 해석 못 하면 ValueError (조용히 건너뛰면 커버리지 구멍이다)."""
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError("#rrggbb 로만 쓴다: %r" % hex_color)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return .2126 * _channel(r) + .7152 * _channel(g) + .0722 * _channel(b)


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + .05) / (lo + .05)


# WCAG 공표값. **유채색이 반드시 들어가야 한다** — 무채색은 R=G=B 라 채널 가중치가
# 무엇이든 같은 답을 낸다. 회색만으로 짠 자기 점검은 계수가 틀려도 통과한다
# (실측: 가중치를 전부 1/3 로 바꿔도 #767676→4.54, #000000→21.00 그대로. 반면
#  #0000ff 는 8.59 → 2.74 로 갈린다). 이 목록이 회색뿐이면 점검이 아니라 장식이다.
WCAG_REFERENCE = [
    ("#000000", "#ffffff", 21.00),
    ("#ffffff", "#ffffff", 1.00),
    ("#767676", "#ffffff", 4.54),   # 흰 배경에서 4.5 를 넘기는 가장 어두운 회색
    ("#0000ff", "#ffffff", 8.59),   # 유채색 — 채널 가중치를 잡는 것은 이쪽이다
    ("#ff0000", "#ffffff", 4.00),
    ("#008000", "#ffffff", 5.14),
    ("#fff", "#000", 21.00),        # #rgb 축약형도 같은 답
]


def self_check():
    """대비 수식을 WCAG 공표값에 맞춰본다. **이 검사기의 유일한 자기 검증이다.**

    수식이 틀리면 모든 비율이 조용히 틀리고, 그러면 [3]번 축은 숫자를 찍으면서
    아무것도 판정하지 않는다 — 검사기가 검사처럼 생긴 상수가 된다. 여기서 멈춘다.
    """
    for fg, bg, expected in WCAG_REFERENCE:
        got = contrast(fg, bg)
        assert abs(got - expected) < 0.01, \
            "대비 수식이 틀렸다: %s on %s → %.2f, WCAG 공표 %.2f" % (fg, bg, got, expected)


# ---------- 응답에서 CSS·토큰 뽑기 ----------

TOKEN_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)")
# `@media (prefers-color-scheme:dark) and (min-width:20em)` 처럼 조건이 더 붙어도 찾는다.
# 여는 중괄호까지만 정규식으로 잡고 끝은 중괄호를 세어 찾는다 — non-greedy `.*?\}\s*\}` 는
# 중첩 깊이를 모른다(리뷰 지적: 블록이 2개면 조용히 어긋난다).
DARK_START_RE = re.compile(r"@media[^{]*prefers-color-scheme\s*:\s*dark[^{]*\{")


def stylesheet(page):
    """인라인 <style> 본문. 없으면 ValueError — 잴 것이 없다."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", page, re.S)
    if not blocks:
        raise ValueError("<style> 이 없다 — 색을 잴 수 없다")
    return "\n".join(blocks)


def dark_blocks(css):
    """다크 미디어쿼리들의 (시작, 끝, 본문). 중괄호를 세어 끝을 찾는다."""
    found = []
    for match in DARK_START_RE.finditer(css):
        depth, i = 1, match.end()
        while i < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        if depth:
            raise ValueError("다크 미디어쿼리의 중괄호가 닫히지 않았다")
        found.append((match.start(), i, css[match.end():i - 1]))
    return found


def token_maps(css):
    """(라이트 맵, 다크 맵). 다크는 기본 위에 미디어쿼리 선언을 덮은 것이다.

    다크만 대비가 깨지는 것이 가장 흔한 회귀라 같은 쌍을 두 맵 모두에 돌린다.
    **다크 블록이 없으면 ValueError** — 예전에는 다크 맵이 라이트 맵을 그대로
    복사해 "다크 7쌍 전부 OK"를 찍었다. 다크 CSS 를 통째로 지워도 종료 0 이었다.
    잴 것이 없어진 검사가 조용히 통과하는 것을 이 파일 첫머리가 금지한다.
    """
    blocks = dark_blocks(css)
    if not blocks:
        raise ValueError("prefers-color-scheme:dark 블록이 없다 — 다크 대비를 잴 수 없다")
    # 인덱스로 잘라낸다. 문자열 replace 는 블록이 2개일 때 join 결과가 원문에 없어
    # 무동작이 되고, 그러면 라이트 맵이 다크 값으로 오염된다(리뷰 실측).
    light_src, prev = "", 0
    for start, end, _ in blocks:
        light_src += css[prev:start]
        prev = end
    light_src += css[prev:]
    light = {k: v.strip() for k, v in TOKEN_RE.findall(light_src)}
    dark = dict(light)
    for _, _, body in blocks:
        dark.update({k: v.strip() for k, v in TOKEN_RE.findall(body)})
    return light, dark


# 선택자와 본문으로 규칙을 쪼갠다. 중첩 at-rule 안쪽 규칙도 이 안쪽 짝에 걸린다.
# ponytail: 중괄호 없는 선언만 있는 평평한 CSS 를 전제하는 순진한 쪼개기다 — 중첩
# 선택자(CSS Nesting)는 못 읽는다. 그런 CSS 가 생기면 규칙 수가 틀리고 아래 첫
# 갈래가 측정 불능으로 멈춘다(조용히 통과하지는 않는다). 주석·문자열은 `focus_rule`
# 이 먹이기 전에 지우므로 여기까지 안 온다.
RULE_RE = re.compile(r"([^{}]*)\{([^{}]*)\}")
# 링이 그려지는지를 정하는 속성들. outline-offset 은 링을 없애지 못하므로 뺀다.
OUTLINE_RE = re.compile(r"outline(?:-width|-style|-color)?\s*:")
# 링을 **키보드 포커스에** 그리는 셀렉터인가(조건 5). 부분 문자열 `":focus"` 로는
# 두 갈래가 새 나갔다 — `:not(:focus-visible)` 은 극성이 뒤집혀 포커스가 아닐 때만
# 그리고, `:focus-within` 은 자식이 받은 포커스라 링이 부모 상자에 그려진다.
# `:has(…:focus-visible)` 은 `:focus-within` 과 의미가 같아 함께 지운다 — 링이
# 조상 상자로 옮겨간다. **`:is()`·`:where()` 는 안 지운다**: 투명해서 그 안의
# 포커스는 여전히 이 요소가 받는다(오탐 표가 그 둘을 붙든다).
# 이름은 대소문자를 안 가린다 — CSS 셀렉터 규정이라 `:NOT(` 도 `:not(` 이고
# `:FOCUS-VISIBLE` 도 링을 그린다. 소문자만 읽으면 앞쪽은 거짓 초록, 뒤쪽은 오탐이다.
# ponytail: 괄호 중첩은 **한 겹**까지 읽는다(`:not(:is(:focus-visible))`). 두 겹부터는
# 못 지워 거짓 초록이 된다 — 그런 셀렉터는 지금 0곳이고 제품 CSS 에는 괄호가 없다.
INDIRECT_RE = re.compile(r":(?:not|has)\((?:[^()]|\([^()]*\))*\)", re.I)
FOCUS_RE = re.compile(r":focus(?:-visible)?(?![\w-])", re.I)
# 링 규칙이 at-rule **밖**인가는 그 앞의 중괄호를 세서 본다(조건 6). 세기의 함정은
# 블록을 안 여는 중괄호 — 주석 안의 `{` 와 `content:"}"` 는 짝이 없어도 CSS 로는
# 정상이다. 세기 전에 지운다. 주석을 먼저 지우는 순서라 주석 안의 따옴표는 안 문다.
COMMENT_OR_STRING_RE = re.compile(r"/\*.*?\*/|\"[^\"\n]*\"|'[^'\n]*'", re.S)


def _top_level(text, seps):
    """괄호 `()`·대괄호 `[]` **밖**의 `seps` 에서만 가른다. 깊이만 세고 문법은 안 읽는다.

    `str.split` 이 아닌 이유는 괄호 안이다 — `:is(.x, .y)` 의 쉼표도 `:not(.x + .y)` 의
    결합자도 셀렉터를 가르지 않고, `[class~=btn]` 의 `~` 는 결합자가 아니라 속성
    연산자다. 깊이를 안 세면 그 여섯 모양이 전부 **정상 CSS 를 거절하는 오탐**이 된다
    (설계서 2절 표가 세 대안을 가른 행이 전부 이쪽이다).

    ponytail: **괄호 안은 세기만 하고 읽지는 않는다.** 그래서 이 계획이 닫은 미탐이
    괄호 한 겹 안에서는 그대로 산다 — `:is(a:focus-visible > .hint)` 는 링을 `.hint` 에
    그리는데 마지막 compound 가 `:is(…)` 통째라 **통과한다**(리뷰 1 실측). 안쪽까지
    보려면 투명 의사클래스의 인자를 다시 갈라 재귀해야 하고 그것은 설계서 6절이 그은
    「CSS 파서를 안 만든다」 밖이다. 제품 CSS 에 괄호가 0곳이라 여는 조건은
    `digest` 의 이웃 후보들과 같다 — «제품 CSS 에 괄호 있는 셀렉터가 처음 생길 때».
    """
    depth, buf, out = 0, [], []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)   # 안 열린 닫기에 음수로 내려가지 않는다
        elif depth == 0 and ch in seps:
            out.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    out.append("".join(buf))
    return out


def focus_rule(css):
    """링을 그리는 규칙 하나를 읽어 (색 토큰, outline-offset 문자열). 안 그려지면 ValueError.

    **색을 재기 전에 잴 것이 살아 있는지를 본다.** 규칙을 지워도 --focus 의 대비는
    그대로 나오고, 그러면 아무에게도 안 보이는 링이 8일째 초록으로 재진다(계획 44).

    자국은 문자열이 아니라 **규칙**이다 — `"var(--focus)" in css` 는 그 문자열이
    *어디에* 있는지 안 보므로 `body{color:var(--focus)}` 만 남아도 통과한다.
    규칙 수를 :focus 아래에서만 세지 않고 **CSS 전체에서** 세는 것이 요점이다:
    뒤에 오는 규칙이 링을 덮는 갈래(outline:none · outline-width:0 · 다크 블록 안의
    덮어쓰기)가 캐스케이드를 흉내내지 않고 조건 하나로 닫힌다. 둘이면 어느 쪽이
    이기는지는 브라우저 일이지 바이트가 답할 것이 아니다.

    ponytail: `:focus-visible` 리터럴은 요구하지 않는다 — `:focus` 도 키보드 포커스에
    링을 그리므로 이 축이 재는 것(키보드 사용자에게 링이 보이나)이 안 깨진다.
    한 규칙 **안에서** `outline-width:0` 으로 자기를 뒤엎는 형태도 못 잡는다(지금 0곳,
    잡으려면 한 규칙 안의 선언 순서를 해석해야 한다).
    """
    css = COMMENT_OR_STRING_RE.sub("", css)
    rules = [m for m in RULE_RE.finditer(css) if OUTLINE_RE.search(m.group(2))]
    if len(rules) != 1:
        raise ValueError("outline 을 정하는 규칙이 %d개 — 캐스케이드를 바이트로 못 정한다"
                         % len(rules))
    selector, body = rules[0].group(1), rules[0].group(2)
    # `:not(…)`·`:has(…)` 안은 링을 **이 요소에** 그릴 조건이 아니라 그리지 않을 조건이거나
    # 조상에 그릴 조건이라 먼저 지운다. 남은 자리에서 `:focus`/`:focus-visible` 이
    # **낱말로** 있어야 한다 — `:focus-within` 은 뒤에 `-` 가 붙어 안 남는다.
    # `:not(.foo):focus-visible` 은 괄호 밖 포커스가 남아 그대로 통과한다.
    # 보는 자리는 셀렉터 전체가 아니라 **쉼표 조각마다 마지막 compound** 다 — 링은
    # 셀렉터가 고르는 그 요소에 그려지므로 `a:focus-visible+.hint` 는 포커스받은 요소가
    # 아니라 **옆 상자**에 그린다. 낱말이 어디에 있든 통과시키면 아무도 못 보는 링
    # 위에서 대비를 재게 된다(계획 44 가 막으려던 그 자리). 조각 하나라도 어긋나면
    # 거절한다 — 쉼표 목록은 전부 같은 규칙을 받으므로 한 조각만 딴 데 그려도 틀린 잣대다.
    # `strip()` 은 꼬리 공백에서 마지막 compound 가 빈 문자열이 되는 것을 막는다.
    for part in _top_level(selector, ","):
        if not FOCUS_RE.search(INDIRECT_RE.sub(
                "", _top_level(part.strip(), " \t\n>+~")[-1])):
            raise ValueError("outline 을 정하는 유일한 규칙이 키보드 포커스용이 아니다: %s"
                             % " ".join(selector.split()))
    # 규칙 앞의 중괄호가 안 닫혀 있으면 링은 어떤 at-rule 안이다(조건 6). **prelude 를
    # 안 읽는다** — 「이 조건은 늘 참」을 고르기 시작하면 `@layer`·`@supports`·
    # `forced-colors` 처럼 모르는 것이 안전으로 분류돼 새 나간다(설계서 1절 F1~F4).
    before = css[:rules[0].start()]
    if before.count("{") != before.count("}"):
        raise ValueError("outline 을 정하는 유일한 규칙이 at-rule 안에 있다 "
                         "— 라이트 화면에 늘 그려지지 않는다")
    decl = re.search(r"outline\s*:\s*([^;}]+)", body)
    value = decl.group(1).strip() if decl else "없음"
    token = re.search(r"var\(\s*(--[a-z0-9-]+)\s*\)", value)
    if not token:
        raise ValueError("outline 이 색 토큰을 안 쓴다 (%s)" % value)
    measured = [fg for fg, _ in NONTEXT_PAIRS]
    if token.group(1) not in measured:
        raise ValueError("그려지는 색 %s ≠ 재는 색 %s"
                         % (token.group(1), ", ".join(measured)))
    off = re.search(r"outline-offset\s*:\s*([^;}]+)", body)
    offset = (off.group(1).strip() if off else "0")
    # 없는 것과 0 과 음수는 같은 결과다 — 링이 요소에 붙어 이웃이 페이지 배경이 아니게 된다.
    if float(re.match(r"[\d.]*", offset).group() or 0) <= 0:
        raise ValueError("outline-offset 이 0 이다 — 링의 이웃이 페이지 배경이 아니다")
    return token.group(1), offset


# ---------- 축별 검사 ----------

def check_contrast(css, fail, unmeasurable):
    try:
        light, dark = token_maps(css)
    except ValueError as exc:
        unmeasurable.append(str(exc))
        return
    if not light:
        unmeasurable.append("CSS 에 색 토큰(--…)이 하나도 없다")
        return
    # 규약이 커버리지를 강제한다 — 색 토큰을 새로 만들고 짝도 사유도 안 적으면 여기서 멈춘다.
    # 이게 없으면 "검사기에 안 적었으니 안 재고 넘어간다"가 가능해진다.
    # **이름을 보지 않는다** — 접두어 허용 목록(--fg-)은 그 밖의 --focus 를 통째로 놓쳤고,
    # 그래서 다음 --ring·--accent 도 같은 자리로 샌다. 허용은 이름이 아니라 NO_PAIR 로만 받는다.
    # **두 맵의 합집합**이다 — 다크에만 있는 토큰이 강제를 빠져나가던 구멍(리뷰 지적).
    paired = {t for pair in PAIRS + NONTEXT_PAIRS for t in pair}
    missing = (set(light) | set(dark)) - paired - set(NO_PAIR)
    if missing:
        unmeasurable.append("짝도 제외도 없는 색 토큰: %s" % ", ".join(sorted(missing)))
        return
    # 비텍스트 짝은 **링이 실제로 그려질 때만** 잰다. 안 그려지면 그 비율은 무효라
    # 종료 1(기준 위반)이 아니라 2(측정 불능)다 — 고장의 크기가 아니라 "찍은 숫자가
    # 아직 참인가" 가 둘을 가른다(설계 `## 갈림길 A`). 텍스트 7짝은 어느 쪽이든 잰다.
    scales = [(PAIRS, MIN_CONTRAST)]
    try:
        ring_token, ring_offset = focus_rule(css)
    except ValueError as exc:
        unmeasurable.append(str(exc))
    else:
        print("    포커스 링 규칙 1개 · outline var(%s) · offset %s" % (ring_token, ring_offset))
        scales.append((NONTEXT_PAIRS, MIN_CONTRAST_NONTEXT))
    # 두 자(텍스트 4.5 · 비텍스트 3.0)가 한 절에 섞이므로 **출력 행에 기준값을 적는다** —
    # 화면만 보고 어느 자로 잰 행인지 알 수 있어야 한다.
    for pairs, floor in scales:
        for label, tokens in (("라이트", light), ("다크", dark)):
            for fg, bg in pairs:
                if fg not in tokens or bg not in tokens:
                    unmeasurable.append("%s: 토큰 %s 가 CSS 에 없다"
                                        % (label, fg if fg not in tokens else bg))
                    continue
                try:
                    ratio = contrast(tokens[fg], tokens[bg])
                except ValueError as exc:
                    unmeasurable.append("%s: %s/%s — %s" % (label, fg, bg, exc))
                    continue
                mark = "OK" if ratio >= floor else "**미달**"
                print("    %-6s %-14s on %-12s %5.2f:1 / 기준 %.1f  %s"
                      % (label, fg, bg, ratio, floor, mark))
                if ratio < floor:
                    fail.append("%s %s/%s 대비 %.2f:1 < %.1f"
                                % (label, fg, bg, ratio, floor))


def check_js(page, fail):
    """페이지가 싣는 JS 를 gzip 해 예산과 비교한다. 인라인·외부 둘 다 센다."""
    inline = "".join(re.findall(r"<script[^>]*>(.*?)</script>", page, re.S))
    external = re.findall(r"<script[^>]+src=", page)
    size = len(gzip.compress(inline.encode())) if inline.strip() else 0
    print("    JS gzip %d B (인라인 %d자 · 외부 %d개) / 예산 %d B"
          % (size, len(inline), len(external), JS_BUDGET))
    if external:
        # 크기를 못 재니 예산 판정 자체가 성립하지 않는다. 지금 구조에선 나올 일이 없다.
        fail.append("외부 스크립트 %d개 — 크기를 재지 못한다" % len(external))
    if size > JS_BUDGET:
        fail.append("JS gzip %d B > 예산 %d B" % (size, JS_BUDGET))


def check_lcp_proxy(page, server_ms, fail):
    subresources = (re.findall(r"<script[^>]+src=", page)
                    + re.findall(r"<link[^>]+rel=[\"']?stylesheet", page)
                    + re.findall(r"<img[^>]", page)
                    + re.findall(r"@import", page))
    doc = len(gzip.compress(page.encode()))
    print("    외부 서브리소스 %d건 · 문서 gzip %d B / %d B · 서버 %.1f ms / %d ms"
          % (len(subresources), doc, DOC_BUDGET, server_ms, SERVER_BUDGET_MS))
    if subresources:
        fail.append("외부 서브리소스 %d건 — 첫 화면에 왕복이 더 붙는다" % len(subresources))
    if doc > DOC_BUDGET:
        fail.append("문서 gzip %d B > %d B" % (doc, DOC_BUDGET))
    if server_ms > SERVER_BUDGET_MS:
        fail.append("서버 생성 %.1f ms > %d ms" % (server_ms, SERVER_BUDGET_MS))


def check_mobile(page, css, fail, unmeasurable):
    if "name=\"viewport\"" not in page:
        fail.append("viewport meta 가 없다 — 360px 에서 확대되어 가로로 넘친다")
    # px 만 보던 검사는 이 제품에서 아무것도 못 봤다 — CSS 가 rem 으로 쓰여 있다(리뷰 지적).
    # 뷰포트 상대 단위(%·vw)는 100 이하면 정의상 안 넘친다.
    wide = []
    for prop, num, unit in re.findall(
            r"(?<![-\w])((?:min-)?width)\s*:\s*([\d.]+)(r?em|px|vw|%)", css):
        px = float(num) * ROOT_FONT_PX if unit in ("rem", "em") else float(num)
        limit = 100 if unit in ("vw", "%") else MOBILE_WIDTH
        if px > limit:
            wide.append(("%s:%s%s" % (prop, num, unit), px, limit))
    # 해석 못 한 단위를 조용히 넘기면 "위반 0건"이 거짓말이 된다.
    for prop, value in re.findall(r"(?<![-\w])((?:min-)?width)\s*:\s*([^;}]+)", css):
        # 0 은 단위가 없어도 유효하고, auto 는 넘칠 수 없다. 나머지 모르는 표기는 못 잰 것이다.
        if not re.fullmatch(r"0|auto|[\d.]+(r?em|px|vw|%)", value.strip()):
            unmeasurable.append("고정폭 단위를 해석 못 했다: %s:%s" % (prop, value.strip()))
    # 결과에 나가는 것은 크롤한 남의 URL 이다. 공백 없는 긴 URL 하나가 360px 을
    # 그대로 밀어낸다 — 이 제품에서 가로 스크롤의 진짜 원인이라 따로 못박는다.
    wraps = css.count("overflow-wrap:anywhere") + css.count("overflow-wrap: anywhere")
    print("    viewport %s · 360px 초과 고정폭 %d건 · overflow-wrap:anywhere %d곳"
          % ("있음" if "name=\"viewport\"" in page else "없음", len(wide), wraps))
    for decl, px, limit in wide:
        fail.append("%s (= %.0f) > %d" % (decl, px, limit))
    if not wraps:
        fail.append("overflow-wrap:anywhere 가 없다 — 긴 크롤 URL 이 360px 을 넘친다")


# ---------- 실행 ----------

def fetch(base, path):
    """(본문, 서버 왕복 ms). 로컬 서버라 네트워크를 타지 않는다."""
    start = time.perf_counter()
    with urllib.request.urlopen(base + path, timeout=30) as resp:
        body = resp.read().decode()
    return body, (time.perf_counter() - start) * 1000


def main():
    self_check()
    fail, unmeasurable = [], []
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, html TEXT, status INTEGER)")
        conn.executemany("INSERT INTO pages VALUES (?, ?, 200)", list(PAGES.items()))
        conn.commit()
        conn.close()
        indexer.index_pages(db)

        server = serve.make_server(db, port=0)
        threading.Thread(target=server.serve_forever,
                         kwargs={"poll_interval": 0.01}, daemon=True).start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            home, home_ms = fetch(base, "/")
            results, results_ms = fetch(base, "/?q=" + urllib.parse.quote("김치"))
        finally:
            server.shutdown()
            server.server_close()

    print("컨셉 디자인 4축 (docs/specs/concept.md:49-54)\n")
    try:
        css = stylesheet(results)
    except ValueError as exc:
        unmeasurable.append(str(exc))
        css = ""

    print("  [1] LCP 1.5s — 대리 지표 (브라우저 없이 직접 못 잰다)")
    print("      홈:")
    check_lcp_proxy(home, home_ms, fail)
    print("      결과:")
    check_lcp_proxy(results, results_ms, fail)

    print("\n  [2] JS 번들 50KB(gzip) 이하")
    check_js(home, fail)
    check_js(results, fail)

    print("\n  [3] 대비 — 텍스트 4.5:1 · 비텍스트(포커스 링) 3:1 이상")
    if css:
        check_contrast(css, fail, unmeasurable)

    print("\n  [4] 모바일 360px 가로 스크롤 없음 — 넘치게 만드는 원인으로 대리")
    if css:
        check_mobile(results, css, fail, unmeasurable)

    if unmeasurable:
        print("\n측정 불능 %d건:" % len(unmeasurable))
        for m in unmeasurable:
            print("  - %s" % m)
        return 2
    if fail:
        print("\n기준 위반 %d건:" % len(fail))
        for m in fail:
            print("  - %s" % m)
        return 1
    print("\n4축 전부 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
