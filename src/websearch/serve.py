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

from . import indexer

PAGE_SIZE = 10
MAX_QUERY = 200
# 성능이 아니라 자원 고갈 방어다 — OFFSET 이 깊어질수록 정렬 결과에서 뽑아 버리는 행이
# 선형으로 는다(설계 탐침: offset 0 에서 1.1ms, 990 에서 7.2ms).
MAX_PAGE = 100
# 요청 라인을 끝내지 않는 연결은 스레드를 무기한 점유한다(슬로로리스). 깊은 OFFSET 을
# 막으면서 이쪽을 열어두면 균형이 안 맞는다 — 이게 훨씬 싼 고갈 경로다.
REQUEST_TIMEOUT = 10


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
# **--fg- 토큰을 새로 만들면 design_check.PAIRS 에도 짝을 적어야 한다.** 안 적으면
# 검사기가 종료 2(측정 불능)를 낸다 — 재지 않고 넘어가는 길을 규약으로 막았다.
# 색 표기는 #rrggbb 만 쓴다(검사기가 그것만 해석한다).
CSS = """
:root{color-scheme:light dark;
--bg-page:#ffffff;--bg-input:#ffffff;--bg-button:#c2410c;
--fg-body:#1a1a1a;--fg-muted:#6b6b6b;--fg-url:#7c6f64;--fg-snippet:#4d4d4d;
--fg-link:#c2410c;--fg-button:#ffffff;--line:#e5ddd8;--focus:#f97316}
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
.home .brand{display:block;font-size:2.5rem;margin-bottom:1.5rem}
.home .sb{margin:0 auto}
.meta{color:var(--fg-muted);font-size:.85rem;margin:0 0 1.5rem}
.hits{list-style:none;margin:0;padding:0}
.hit{margin-bottom:1.6rem}
/* 결과에 나가는 것은 크롤한 남의 URL 이다 — 공백 없는 긴 URL 하나가 360px 을 밀어낸다 */
.hit .url{color:var(--fg-url);font-size:.8rem;overflow-wrap:anywhere}
.hit h2{margin:.1rem 0 .2rem;font-size:1.15rem;font-weight:500;overflow-wrap:anywhere}
.hit p{margin:0;color:var(--fg-snippet);font-size:.9rem;overflow-wrap:anywhere}
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
    """
    return url if url.split(":", 1)[0].lower() in ("http", "https") else None


def _render(title, body):
    return (PAGE % {"title": html.escape(title), "css": CSS, "body": body}).encode()


def _home():
    return _render("%s — 웹 검색" % BRAND,
                   '<main class="home"><span class="brand">%s</span>%s</main>'
                   % (BRAND, SEARCHBOX % ("", " autofocus")))


def _results(query, hits):
    """결과 페이지. **여기 들어가는 네 값이 전부 남이 쓴 문자열이다** —
    질의어(사용자)·제목·URL·스니펫(크롤한 문서). 넷 다 html.escape() 를 지난다."""
    box = SEARCHBOX % (html.escape(query, quote=True), "")
    head = '<header><a class="brand" href="/">%s</a>%s</header>' % (BRAND, box)
    if not hits:
        return _render("%s — %s" % (query, BRAND),
                       head + '<main><p class="meta">검색 결과가 없습니다.</p></main>')
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
    return _render("%s — %s" % (query, BRAND),
                   head + '<main><p class="meta">%d건</p><ol class="hits">%s</ol></main>'
                   % (len(items), "".join(items)))


def _error_page(reason):
    return _render("%s — 검색할 수 없습니다" % BRAND,
                   '<main><p class="meta">%s</p>%s</main>'
                   % (html.escape(reason), SEARCHBOX % ("", " autofocus")))


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
                # limit+1 로 받아 11번째 유무로 has_next 를 판정한다 — 개수 질의는
                # 두 번째 전수 질의라 p95 에 그대로 얹힌다 (design_search-api.md 계약)
                hits = indexer.search(db_path, query, limit=PAGE_SIZE + 1,
                                      offset=(page - 1) * PAGE_SIZE)
            except ValueError as exc:
                self._send(400, {"error": str(exc)})
            except Exception as exc:  # 트레이스백을 응답 본문에 싣지 않는다
                self.log_error("search 실패: %r", exc)
                self._send(500, {"error": "검색 중 오류가 났다"})
            else:
                self._send(200, {
                    "query": query,
                    "page": page,
                    # 상한도 서버가 정한 것이니 마지막이라는 사실도 서버가 알려야 한다.
                    # 아니면 has_next 를 따라가는 클라이언트가 반드시 400 을 맞는다.
                    "has_next": len(hits) > PAGE_SIZE and page < MAX_PAGE,
                    "results": [{"url": url, "title": title, "snippet": snippet}
                                for url, title, snippet in hits[:PAGE_SIZE]],
                })

        def _do_html(self, params):
            # 홈은 q 가 없는 것이 정상이라 _parse() 앞에서 가른다. _parse() 를 고치면
            # /search 의 400 계약이 바뀐다 — 검증은 재사용하되 손대지는 않는다.
            if not (params.get("q") or [""])[0].strip():
                self._send_html(200, _home())
                return
            try:
                query, page = _parse(params)
                hits = indexer.search(db_path, query, limit=PAGE_SIZE,
                                      offset=(page - 1) * PAGE_SIZE)
            except ValueError as exc:
                self._send_html(400, _error_page(str(exc)))
            except Exception as exc:  # 트레이스백을 응답 본문에 싣지 않는다
                self.log_error("검색 화면 실패: %r", exc)
                self._send_html(500, _error_page("검색 중 오류가 났다"))
            else:
                self._send_html(200, _results(query, hits))

        def _send_html(self, status, body):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send(self, status, payload):
            # ensure_ascii=False: 한국어가 \uXXXX 로 나가면 눈으로 검증할 수 없다
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
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
    port = 8000
    if "--port" in args:
        i = args.index("--port")
        if i + 1 >= len(args) or not args[i + 1].isdigit():
            print("--port 는 포트 번호 하나를 받는다", file=sys.stderr)
            return 2
        port = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        print("usage: python3 -m websearch.serve <db> [--port N]", file=sys.stderr)
        return 2
    server = make_server(args[0], port)
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
