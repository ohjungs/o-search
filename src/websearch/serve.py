"""검색 결과를 JSON 으로 내는 HTTP 서버. 엔드포인트는 GET /search 하나뿐이다.

요청마다 sqlite 연결을 새로 연다 — 연결 open+close 가 0.04ms 로 질의(1.16ms)의
3% 라 아낄 것이 없다(docs/design_search-api.md 탐침). 그래서 indexer.search() 를
그대로 쓴다.
"""
import http.server
import json
import sys
import urllib.parse

from . import indexer

PAGE_SIZE = 10
MAX_QUERY = 200
# 성능이 아니라 자원 고갈 방어다 — OFFSET 은 선형으로 자란다(설계 탐침: 990에서 7.2ms).
# 상한이 없으면 page=99999 한 요청이 색인을 통째로 훑는 무료 고갈 경로가 된다.
MAX_PAGE = 100


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


def make_server(db_path, port=8000):
    """검색 서버를 만들어 돌려준다. serve_forever() 는 부르는 쪽 몫이다."""

    class Handler(http.server.BaseHTTPRequestHandler):
        # do_POST 등은 정의하지 않는다 — stdlib 이 501 을 낸다. 스텁을 두면
        # 방금 한곳에 모은 방어가 다시 메서드마다 흩어진다.

        def do_GET(self):
            parts = urllib.parse.urlsplit(self.path)
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
                    "has_next": len(hits) > PAGE_SIZE,
                    "results": [{"url": url, "title": title, "snippet": snippet}
                                for url, title, snippet in hits[:PAGE_SIZE]],
                })

        def _send(self, status, payload):
            # ensure_ascii=False: 한국어가 \uXXXX 로 나가면 눈으로 검증할 수 없다
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass  # ponytail: 요청 로그 없음. 운영에서 필요해지면 stdlib 기본 동작을 되살린다

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
