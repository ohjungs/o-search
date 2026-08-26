#!/usr/bin/env python3
"""컨셉 디자인 4축(`docs/specs/concept.md:49-54`)을 실제 응답 바이트로 판정한다.

    1. 결과 페이지 LCP 1.5s 이하    2. JS 번들 50KB(gzip) 이하
    3. 텍스트 대비 4.5:1 이상        4. 모바일(360px)에서 가로 스크롤 없음

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
MOBILE_WIDTH = 360         # concept.md:54
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


# ---------- 응답에서 CSS·토큰 뽑기 ----------

TOKEN_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)")
DARK_RE = re.compile(r"@media\s*\(prefers-color-scheme\s*:\s*dark\)\s*\{(.*?)\}\s*\}", re.S)


def stylesheet(page):
    """인라인 <style> 본문. 없으면 ValueError — 잴 것이 없다."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", page, re.S)
    if not blocks:
        raise ValueError("<style> 이 없다 — 색을 잴 수 없다")
    return "\n".join(blocks)


def token_maps(css):
    """(라이트 맵, 다크 맵). 다크는 기본 위에 미디어쿼리 선언을 덮은 것이다.

    다크만 대비가 깨지는 것이 가장 흔한 회귀라 같은 쌍을 두 맵 모두에 돌린다.
    """
    dark_block = "".join(DARK_RE.findall(css))
    light = dict(TOKEN_RE.findall(css.replace(dark_block, "")))
    dark = dict(light, **dict(TOKEN_RE.findall(dark_block)))
    return {k: v.strip() for k, v in light.items()}, {k: v.strip() for k, v in dark.items()}


# ---------- 축별 검사 ----------

def check_contrast(css, fail, unmeasurable):
    light, dark = token_maps(css)
    if not light:
        unmeasurable.append("CSS 에 색 토큰(--…)이 하나도 없다")
        return
    # 규약이 커버리지를 강제한다 — --fg- 토큰을 새로 만들고 PAIRS 에 안 적으면 여기서 멈춘다.
    # 이게 없으면 "검사기에 안 적었으니 안 재고 넘어간다"가 가능해진다.
    declared = {k for k in light if k.startswith("--fg-")}
    missing = declared - {fg for fg, _ in PAIRS}
    if missing:
        unmeasurable.append("PAIRS 에 짝이 없는 전경색 토큰: %s" % ", ".join(sorted(missing)))
        return
    for label, tokens in (("라이트", light), ("다크", dark)):
        for fg, bg in PAIRS:
            if fg not in tokens or bg not in tokens:
                unmeasurable.append("%s: 토큰 %s 가 CSS 에 없다"
                                    % (label, fg if fg not in tokens else bg))
                continue
            try:
                ratio = contrast(tokens[fg], tokens[bg])
            except ValueError as exc:
                unmeasurable.append("%s: %s/%s — %s" % (label, fg, bg, exc))
                continue
            mark = "OK" if ratio >= MIN_CONTRAST else "**미달**"
            print("    %-6s %-14s on %-12s %5.2f:1  %s" % (label, fg, bg, ratio, mark))
            if ratio < MIN_CONTRAST:
                fail.append("%s %s/%s 대비 %.2f:1 < %.1f"
                            % (label, fg, bg, ratio, MIN_CONTRAST))


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


def check_mobile(page, css, fail):
    if "name=\"viewport\"" not in page:
        fail.append("viewport meta 가 없다 — 360px 에서 확대되어 가로로 넘친다")
    wide = [(prop, int(px)) for prop, px in
            re.findall(r"(?<!-)\b((?:min-)?width)\s*:\s*(\d+)px", css)
            if int(px) > MOBILE_WIDTH]
    # 결과에 나가는 것은 크롤한 남의 URL 이다. 공백 없는 긴 URL 하나가 360px 을
    # 그대로 밀어낸다 — 이 제품에서 가로 스크롤의 진짜 원인이라 따로 못박는다.
    wraps = css.count("overflow-wrap:anywhere") + css.count("overflow-wrap: anywhere")
    print("    viewport %s · 360px 초과 고정폭 %d건 · overflow-wrap:anywhere %d곳"
          % ("있음" if "name=\"viewport\"" in page else "없음", len(wide), wraps))
    for prop, px in wide:
        fail.append("%s:%dpx > %dpx" % (prop, px, MOBILE_WIDTH))
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
    check_js(results, fail)

    print("\n  [3] 텍스트 대비 4.5:1 이상")
    if css:
        check_contrast(css, fail, unmeasurable)

    print("\n  [4] 모바일 360px 가로 스크롤 없음 — 넘치게 만드는 원인으로 대리")
    if css:
        check_mobile(results, css, fail)

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
