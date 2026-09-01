"""검색 HTTP 서버. 경로 둘이다.

    GET /          검색 홈 (HTML)          GET /?q=…      결과 페이지 (HTML)
    GET /search?q= 검색 결과 (JSON)

요청마다 sqlite 연결을 새로 연다 — 연결 open+close 가 0.04ms 로 질의(1.16ms)의
3% 라 아낄 것이 없다(docs/design_search-api.md 탐침). 그래서 indexer.search() 를
그대로 쓴다.

**HTML 과 JSON 을 경로로 가른다** — 같은 URL 을 Accept 헤더로 협상하면
e2e/perf_search.py 가 재는 p95 가 "어느 코드의 p95 인지 헤더에 달리게" 된다
(docs/design_search-ui.md 갈림길 1). /search 의 응답은 화면이 붙은 뒤에도 그대로다.
"""
import html
import http.server
import json
import sys
import urllib.parse

from . import flags, indexer

PAGE_SIZE = 10
MAX_QUERY = 200
# 성능이 아니라 자원 고갈 방어다 — OFFSET 이 깊어질수록 정렬 결과에서 뽑아 버리는 행이
# 선형으로 는다(설계 탐침: offset 0 에서 1.1ms, 990 에서 7.2ms).
MAX_PAGE = 100
# 요청 라인을 끝내지 않는 연결은 스레드를 무기한 점유한다(슬로로리스). 깊은 OFFSET 을
# 막으면서 이쪽을 열어두면 균형이 안 맞는다 — 이게 훨씬 싼 고갈 경로다.
REQUEST_TIMEOUT = 10
# JSON 응답 스키마의 버전(사양 기능 9). `_send` 한 곳에서 붙어 200·400·404·500·503 이
# 전부 갖는다 — 호출부마다 붙이면 다섯 벌이고 언젠가 하나가 빠진다.
# **화면(`_send_html`)에는 안 붙는다** — 계약은 기계가 읽고 화면은 사람이 읽는다.
# **올리는 규칙**: 필드를 빼거나 뜻을 바꿀 때만 +1 한다. 필드를 **더하는** 변경은 1 그대로다
# (소비자가 모르는 키를 무시하면 그대로 산다). 정수라 소비자가 `>=` 로 비교한다.
VERSION = 1


def _parse(params):
    """질의 파라미터를 검증해 (query, page) 를 돌려준다. 위반이면 ValueError(사람이 읽는 사유).

    진입점 방어를 여기 한 곳에 모은다 — 핸들러 메서드마다 흩으면 하나가 빠진다.
    질의 문자열 자체의 FTS5 문법·NUL·제어문자는 indexer._fts_query() 가 이미 막는다.
    여기서 두 번 막지 않는다(막는 자리가 둘이면 한쪽만 고쳐진다).
    """
    query = (params.get("q") or [""])[0].strip()
    if not query:
        raise ValueError("q 파라미터에 질의 문자열이 필요하다")
    if len(query) > MAX_QUERY:
        raise ValueError("질의는 %d자 이하여야 한다" % MAX_QUERY)
    # isdecimal: isdigit 은 "²" 에 참이지만 int() 는 거부한다 — 그러면 파이썬 예외 문구가 샌다
    raw = (params.get("page") or ["1"])[0]
    if not raw.isdecimal() or not 1 <= int(raw) <= MAX_PAGE:
        raise ValueError("page 는 1 이상 %d 이하의 정수여야 한다" % MAX_PAGE)
    return query, int(raw)


BRAND = "websearch"
MAX_SNIPPET = 200

# 색은 **전부 토큰으로만** 선언한다. e2e/design_check.py 가 --fg-* 와 --bg-* 를 여기서
# 읽어 WCAG 대비를 매번 다시 계산하기 때문이다 — 검사기가 값을 따로 들면 색을 고쳐도
# 옛 값으로 통과를 내준다(docs/design_search-ui.md 갈림길 2).
# **색 토큰을 새로 만들면 design_check 의 PAIRS/NONTEXT_PAIRS 에 짝을 적거나
# NO_PAIR 에 사유를 적어야 한다.** 안 적으면
# 검사기가 종료 2(측정 불능)를 낸다 — 재지 않고 넘어가는 길을 규약으로 막았다.
# 색 표기는 #rrggbb 만 쓴다(검사기가 그것만 해석한다).
CSS = """
:root{color-scheme:light dark;
--bg-page:#ffffff;--bg-input:#ffffff;--bg-button:#c2410c;
--fg-body:#1a1a1a;--fg-muted:#6b6b6b;--fg-url:#7c6f64;--fg-snippet:#4d4d4d;
--fg-link:#c2410c;--fg-button:#ffffff;--line:#e5ddd8;--focus:#ea580c}
@media(prefers-color-scheme:dark){:root{
--bg-page:#141110;--bg-input:#1e1917;--bg-button:#f97316;
--fg-body:#eeeeee;--fg-muted:#a89a92;--fg-url:#a1897a;--fg-snippet:#c9c1bc;
--fg-link:#fdba74;--fg-button:#1a1008;--line:#3a2a22;--focus:#fdba74}}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
color:var(--fg-body);background:var(--bg-page)}
a{color:var(--fg-link)}
.sb{display:flex;flex:1;max-width:36rem}
.sb input{flex:1;min-width:0;font:inherit;padding:.6rem 1rem;border:1px solid var(--line);
border-right:0;border-radius:1.5rem 0 0 1.5rem;background:var(--bg-input);color:var(--fg-body)}
.sb input:focus-visible,.sb button:focus-visible,a:focus-visible{outline:3px solid var(--focus);
outline-offset:2px}
.sb button{font:inherit;font-weight:600;padding:.6rem 1.2rem;border:1px solid var(--bg-button);
background:var(--bg-button);color:var(--fg-button);border-radius:0 1.5rem 1.5rem 0;cursor:pointer}
header{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;
padding:.9rem 1rem;border-bottom:1px solid var(--line)}
.brand{font-size:1.25rem;font-weight:700;letter-spacing:-.03em;text-decoration:none}
main{max-width:44rem;padding:1.5rem 1rem}
.home{margin:12vh auto;text-align:center}
.home .brand{display:block;font-size:2.5rem;margin:0 0 1.5rem}
.home .sb{margin:0 auto}
/* h1 이지만 화면에서는 작은 안내문이다 — 제목 계층은 의미용, 크기는 시안용 */
.meta{color:var(--fg-muted);font-size:.85rem;font-weight:400;margin:0 0 1.5rem}
.hits{list-style:none;margin:0;padding:0}
.hit{margin-bottom:1.6rem}
/* 결과에 나가는 것은 크롤한 남의 URL 이다 — 공백 없는 긴 URL 하나가 360px 을 밀어낸다 */
.hit .url{color:var(--fg-url);font-size:.8rem;overflow-wrap:anywhere}
.hit h2{margin:.1rem 0 .2rem;font-size:1.15rem;font-weight:500;overflow-wrap:anywhere}
.hit p{margin:0;color:var(--fg-snippet);font-size:.9rem;overflow-wrap:anywhere}
/* 고정폭을 두지 않는다 — 360px 을 밀어내면 design_check.check_mobile 이 잡는다 */
.pager{display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:2rem;padding-top:1rem;
border-top:1px solid var(--line)}
.pager a{font-size:.9rem;padding:.4rem 0}
"""

PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<style>%(css)s</style></head>
<body>%(body)s</body></html>
"""

# autofocus 는 홈에서만 준다 — 결과 페이지에서 주면 스크린리더·키보드 사용자가
# 방금 받은 결과를 지나쳐 입력창으로 끌려간다.
SEARCHBOX = ('<form class="sb" action="/" method="get" role="search">'
             '<input name="q" value="%s" placeholder="검색어" aria-label="검색어"%s>'
             '<button type="submit">검색</button></form>')


def _safe_href(url):
    """href 에 넣어도 되는 URL 이면 그대로, 아니면 None.

    **html.escape() 만으로는 못 막는다** — `javascript:alert(1)` 에는 & < > " 가
    하나도 없어서 이스케이프를 그대로 통과한다. 크롤러가 http/https 만 담는다는
    성질에 기대지 않고 렌더 시점에 확인한다(그 성질이 깨지는 날 여기가 유일한 방어다).
    허용 목록이라 새 스킴(data:, vbscript:)이 생겨도 자동으로 막힌다.
    콜론까지 봐야 한다 — `"http".split(":")[0]` 은 `"http"` 라, 스킴이 아예 없는
    상대 경로(`//evil.test/x`)가 통과했다.
    """
    scheme, sep, _ = url.partition(":")
    return url if sep and scheme.lower() in ("http", "https") else None


def _render(title, body):
    return (PAGE % {"title": html.escape(title), "css": CSS, "body": body}).encode()


def _home():
    return _render("%s — 웹 검색" % BRAND,
                   '<main class="home"><h1 class="brand">%s</h1>%s</main>'
                   % (BRAND, SEARCHBOX % ("", " autofocus")))


def _page_hits(db_path, query, page):
    """한 페이지 + **탐침 한 줄**. `_has_next` 의 전제가 여기 붙어 있다.

    `+ 1` 을 호출부에 두 벌로 두면 한쪽만 `PAGE_SIZE` 로 되돌아갔을 때 `_has_next` 가
    예외 없이 조용히 `False` 를 내고 그 경로의 다음 링크가 영영 사라진다. 판정과 그
    판정을 성립시키는 질의는 같은 자리에 있어야 한다.
    """
    return indexer.search(db_path, query, limit=PAGE_SIZE + 1,
                          offset=(page - 1) * PAGE_SIZE)


def _has_next(hits, page):
    """다음 페이지가 있는가. **JSON 화면 두 경로가 나눠 쓰는 한 벌이다.**

    `limit=PAGE_SIZE + 1` 로 받아 **11번째의 유무**로 판정한다 — 개수 질의는 두 번째
    전수 질의라 p95 에 그대로 얹힌다(docs/design_search-api.md 계약).
    상한도 서버가 정한 것이니 마지막이라는 사실도 서버가 알려야 한다 — 아니면
    다음을 따라간 사용자가 400 을 맞는다.
    """
    return len(hits) > PAGE_SIZE and page < MAX_PAGE


def _pager(query, page, has_next):
    """이전/다음. 갈 곳이 없으면 빈 문자열.

    **번호 목록(1 2 3 …)을 안 그린다** — 총 건수를 모르기 때문이다. 알려면 COUNT 를
    한 번 더 돌려야 하는데 그것이 `_has_next` 가 피한 바로 그 질의다. 지금 아는
    정보로 정직하게 그릴 수 있는 것은 **양옆 한 칸씩**이다.

    `query` 는 사용자가 쓴 문자열이다. **속성을 깨는 것을 막는 쪽은 `urlencode` 다** —
    `"`·`<`·`&` 를 전부 퍼센트 인코딩하므로 이스케이프 없이도 XSS 는 안 난다.
    `html.escape` 가 하는 일은 그 뒤에 **하나 남는 `&`**(파라미터 구분자)를 `&amp;` 로
    바꾸는 것뿐이다 — 속성값 안의 날 `&` 는 HTML 유효성 위반이다.
    (넓게 적으면 아무도 안 본다: digest `[6]` 주장은 참인 범위까지만)
    """
    steps = ([("prev", page - 1, "이전")] if page > 1 else []) + \
            ([("next", page + 1, "다음")] if has_next else [])
    if not steps:
        return ""
    links = "".join(
        '<a rel="%s" href="/?%s">%s</a>'
        % (rel, html.escape(urllib.parse.urlencode({"q": query, "page": n}), quote=True), label)
        for rel, n, label in steps)
    return '<nav class="pager" aria-label="검색 결과 페이지">%s</nav>' % links


def _results(query, hits, page):
    """결과 페이지. **여기 들어가는 네 값이 전부 남이 쓴 문자열이다** —
    질의어(사용자)·제목·URL·스니펫(크롤한 문서). 넷 다 html.escape() 를 지난다.

    `hits` 는 `PAGE_SIZE + 1` 건까지 온다 — 마지막 하나는 **다음 장이 있는지 보려고
    받은 탐침**이라 그리지도 세지도 않는다.
    """
    has_next = _has_next(hits, page)
    hits = hits[:PAGE_SIZE]
    box = SEARCHBOX % (html.escape(query, quote=True), "")
    head = '<header><a class="brand" href="/">%s</a>%s</header>' % (BRAND, box)
    # h1 이 결과 목록의 주제를 말한다 — 없으면 스크린리더에 h2 만 늘어선다.
    if not hits:
        # 이동은 여기서도 낸다 — 3페이지가 비었다고 감추면 **막다른 길**이 된다
        return _render("%s — %s" % (query, BRAND),
                       head + '<main><h1 class="meta">‘%s’ 검색 결과가 없습니다.</h1>%s</main>'
                       % (html.escape(query), _pager(query, page, has_next)))
    items = []
    for url, title, snippet in hits:
        safe_url = html.escape(url, quote=True)
        label = html.escape(title or url)
        href = _safe_href(url)
        # 링크로 못 내보내는 URL 은 제목을 글자로만 낸다 — 결과를 숨기지는 않는다
        heading = ('<h2><a href="%s">%s</a></h2>' % (html.escape(href, quote=True), label)
                   if href else "<h2>%s</h2>" % label)
        items.append('<li class="hit"><div class="url">%s</div>%s<p>%s</p></li>'
                     % (safe_url, heading, html.escape(snippet[:MAX_SNIPPET])))
    # "N건"은 전체 건수가 아니라 이 페이지에 실린 수다 — 그렇게 읽히게 적는다.
    return _render("%s — %s" % (query, BRAND),
                   head + '<main><h1 class="meta">‘%s’ 검색 결과 %d건</h1>'
                          '<ol class="hits">%s</ol>%s</main>'
                   % (html.escape(query), len(items), "".join(items),
                      _pager(query, page, has_next)))


def _error_page(reason, query=""):
    """질의어를 되돌려준다 — 버리면 사용자가 다시 친다.
    autofocus 는 주지 않는다(:104 와 같은 이유로, 오류 문구를 지나쳐 끌려간다)."""
    return _render("%s — 검색할 수 없습니다" % BRAND,
                   '<main><h1 class="meta">%s</h1>%s</main>'
                   % (html.escape(reason), SEARCHBOX % (html.escape(query, quote=True), "")))


def make_server(db_path, port=8000):
    """검색 서버를 만들어 돌려준다. serve_forever() 는 부르는 쪽 몫이다."""

    class Handler(http.server.BaseHTTPRequestHandler):
        # do_POST 등은 정의하지 않는다 — stdlib 이 501 을 낸다. 스텁을 두면
        # 방금 한곳에 모은 방어가 다시 메서드마다 흩어진다.
        timeout = REQUEST_TIMEOUT

        def do_GET(self):
            parts = urllib.parse.urlsplit(self.path)
            if parts.path == "/":
                self._do_html(urllib.parse.parse_qs(parts.query))
                return
            if parts.path != "/search":
                self._send(404, {"error": "없는 경로: %s" % parts.path})
                return
            try:
                query, page = _parse(urllib.parse.parse_qs(parts.query))
                # 탐침 한 줄로 has_next 를 판정한다 — 개수 질의는 두 번째 전수 질의라
                # p95 에 그대로 얹힌다 (design_search-api.md 계약)
                hits = _page_hits(db_path, query, page)
            except ValueError as exc:
                self._send(400, {"error": str(exc)})
            # **`except Exception` 앞이어야 한다** — 뒤면 영영 안 닿는다. 색인을 다시
            # 돌리면 낫는 상태에 500(재시도 안 함)은 틀린 신호다. 이 코드를 읽는 것은
            # 사람이 아니라 인프라다(사양 디자인 5 · design_json-contract.md 갈림길 B).
            # 본문은 고정 문구다 — `str(exc)` 는 곧 DB 경로다.
            except (FileNotFoundError, indexer.StaleIndexError) as exc:
                self.log_error("색인 없음: %r", exc)
                self._send(503, {"error": "색인이 아직 준비되지 않았다"})
            except Exception as exc:  # 트레이스백을 응답 본문에 싣지 않는다
                self.log_error("search 실패: %r", exc)
                self._send(500, {"error": "검색 중 오류가 났다"})
            else:
                self._send(200, {
                    "query": query,
                    "page": page,
                    # 상한도 서버가 정한 것이니 마지막이라는 사실도 서버가 알려야 한다.
                    # 아니면 has_next 를 따라가는 클라이언트가 반드시 400 을 맞는다.
                    "has_next": _has_next(hits, page),
                    "results": [{"url": url, "title": title, "snippet": snippet}
                                for url, title, snippet in hits[:PAGE_SIZE]],
                })

        def _do_html(self, params):
            # 홈은 q 가 없는 것이 정상이라 _parse() 앞에서 가른다. _parse() 를 고치면
            # /search 의 400 계약이 바뀐다 — 검증은 재사용하되 손대지는 않는다.
            typed = (params.get("q") or [""])[0].strip()
            if not typed:
                self._send_html(200, _home())
                return
            try:
                query, page = _parse(params)
                hits = _page_hits(db_path, query, page)  # JSON 경로와 **같은 한 벌**
            except ValueError as exc:
                self._send_html(400, _error_page(str(exc), typed))
            except (FileNotFoundError, indexer.StaleIndexError) as exc:  # JSON 과 같은 값
                self.log_error("색인 없음: %r", exc)
                self._send_html(503, _error_page("색인이 아직 준비되지 않았다", typed))
            except Exception as exc:  # 트레이스백을 응답 본문에 싣지 않는다
                self.log_error("검색 화면 실패: %r", exc)
                self._send_html(500, _error_page("검색 중 오류가 났다", typed))
            else:
                self._send_html(200, _results(query, hits, page))

        def _send_html(self, status, body):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            # 이스케이프가 뚫린 날 남는 두 번째 방어선이다. JS 가 0KB 라 잃을 것이 없다.
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'; "
                             "script-src 'none'; form-action 'self'; base-uri 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send(self, status, payload):
            # ensure_ascii=False: 한국어가 \uXXXX 로 나가면 눈으로 검증할 수 없다
            body = json.dumps({"version": VERSION, **payload}, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_request(self, *args):
            # 끄는 것은 **접근 로그뿐**이다. log_message 를 덮으면 log_error 도 같이
            # 죽는다(stdlib 이 log_error → log_message 로 넘긴다) — 그러면 위에서
            # 응답 밖으로 뺀 500 의 원인이 어디에도 안 남아 고칠 수가 없다.
            pass

    return http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv):
    args = list(argv[1:])
    # 값 검사는 flags.number_flag 가 한다 — `--port ٨٠٨٠` 이 조용히 8080 이 되던 함정을
    # crawl 과 **같은 자리에서** 막는다. 여기 남는 것은 이 명령만의 상한이다.
    port = flags.number_flag(args, "--port", 8000)
    if port is None or port > 65535:
        print("--port 는 0~65535 의 포트 번호 하나를 받는다", file=sys.stderr)
        return 2
    if len(args) != 1:
        print("usage: python3 -m websearch.serve <db> [--port N]", file=sys.stderr)
        return 2
    try:
        server = make_server(args[0], port)
    except OSError as exc:
        # 이미 쓰이는 포트(EADDRINUSE)·특권 포트(EACCES). 사용자 입력이 아니라
        # 환경이라 usage(2)가 아니고, 안 잡았을 때도 rc 는 1 이었다 — 종료 코드는
        # 그대로고 바뀌는 것은 트레이스백뿐이다.
        print("포트 %d 를 열 수 없다: %s" % (port, exc), file=sys.stderr)
        return 1
    # 실제 포트를 찍는다 — --port 0 으로 띄우는 e2e·측정 스크립트가 이것을 읽는다
    print("http://127.0.0.1:%d/search?q=" % server.server_address[1], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
