"""recrawl e2e — plan_recrawl.md 6절의 시나리오 넷을 그대로 실행한다.

**두 실행을 실제로 잇는 유일한 자다.** 단위 706건이 전부 초록인 채로 계획 80 의
결함 둘(리뷰 F1·F2)이 살아 있던 직접 원인이 「크롤과 색인을 잇는 e2e 가 없다」였다.
다른 e2e 는 재크롤을 `Store.upsert` 직접 호출로 흉내 내 `is_fresh` 게이트를 한 번도
안 지난다 — 여기서는 **CLI 를 두 번 실제로 돌리고 요청을 서버 수신 기록으로 센다.**

시나리오
  1. 31일 된 문서를 다시 받는다 → 새 본문이 검색되고 옛 본문은 안 나온다
  2. 29일 된 문서는 **서버에 요청 0건** (TTL 이 자를 갖는다는 음성 대조)
  3. 404 로 바뀐 URL 은 검색에서 빠지고 `pages` 묘비는 `status=404` 로 남는다
  4. 재크롤이 새 링크를 줍고, 그때도 도메인 간격이 **서버 수신 시각으로** 1초 이상

실행: PYTHONPATH=src python3 e2e/recrawl_e2e.py
"""
import http.server
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUEST_LOG = []  # (시각, 경로) — 「실제로 나갔나」의 정본. 크롤러 말이 아니라 서버 기록이다
ROUND = {"n": 1}  # 서버가 1회차/2회차에 다른 것을 내주게 하는 손잡이

# 1회차 본문. 2회차에 `/` 는 링크가 하나 늘고, `/stale` 은 본문이 갈리고,
# `/gone` 은 404 가 된다. `/fresh` 는 안 갈리지만 어차피 요청이 오면 안 된다.
LINKS_1 = '<a href="/stale">s</a><a href="/fresh">f</a><a href="/gone">g</a>'
LINKS_2 = LINKS_1 + '<a href="/newlink">n</a>'
PAGES = {
    "/stale": ("<title>낡은 것</title><p>pyeongsan 옛 본문</p>",
               "<title>갈린 것</title><p>gwangju 새 본문</p>"),
    "/fresh": ("<title>신선</title><p>chuncheon 안 갈린다</p>",) * 2,
    "/gone": ("<title>사라질 것</title><p>tongyeong 곧 없어진다</p>", None),
    "/newlink": (None, "<title>새 링크</title><p>sokcho 이번에 생겼다</p>"),
}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        REQUEST_LOG.append((time.monotonic(), self.path, ROUND["n"]))
        if self.path == "/robots.txt":
            return self._send(b"User-agent: *\nAllow: /\n", "text/plain")
        if self.path == "/":
            links = LINKS_1 if ROUND["n"] == 1 else LINKS_2
            return self._send(("<title>시작</title>%s" % links).encode(), "text/html")
        body = PAGES.get(self.path, (None, None))[ROUND["n"] - 1]
        if body is None:
            self.send_error(404)  # 「없어졌다」 — 2회차의 /gone, 1회차의 /newlink
            return
        self._send(body.encode(), "text/html")

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def run(env, *args):
    proc = subprocess.run([sys.executable] + list(args), env=env,
                          capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, "exit %d\n%s%s" % (proc.returncode, proc.stdout, proc.stderr)
    return proc.stdout


def crawl(env, base, db):
    # CLI 는 db 경로 인자가 없어 crawl() 을 -c 로 감싼다 — 사용자 실행 형태(모듈 실행) 유지
    return run(env, "-c",
               "import sys; from websearch.crawl import crawl; "
               "print('수집 %d 페이지' % crawl([sys.argv[1]], 20, db_path=sys.argv[2]))",
               base + "/", db)


def index(env, db):
    return run(env, "-m", "websearch.indexer", db)


def query(env, db, q):
    return run(env, "-m", "websearch.indexer", db, "--query", q)


def age(db, url, days):
    """이 URL 을 `days` 일 전에 받은 것으로 되돌린다 — 30일을 실제로 기다릴 수는 없다."""
    con = sqlite3.connect(db)
    con.execute("UPDATE pages SET fetched_at = datetime('now', ?) WHERE url = ?",
                ("-%d days" % days, url))
    assert con.total_changes == 1, "되돌릴 행이 없다: %s" % url
    con.commit()
    con.close()


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % server.server_address[1]
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))

        # ---- 1회차: 사람이 처음 돌리는 그대로 ----
        assert "수집 4 페이지" in crawl(env, base, db), "1회차 수집이 4장이 아니다"
        assert "4 문서 색인" in index(env, db)
        assert "pyeongsan" in query(env, db, "pyeongsan"), "1회차에 옛 본문이 안 잡힌다"

        # ---- 시각을 되돌린다: 셋은 낡고 하나(/fresh)는 아직 신선하다 ----
        for path, days in (("/", 31), ("/stale", 31), ("/gone", 31), ("/fresh", 29)):
            age(db, base + path, days)

        # ---- 2회차 ----
        ROUND["n"] = 2
        mark = len(REQUEST_LOG)
        assert "수집 3 페이지" in crawl(env, base, db), "2회차 수집이 3장이 아니다"
        out = index(env, db)
        second = [(t, p) for t, p, r in REQUEST_LOG[mark:]]
        paths = [p for _, p in second]

        # 시나리오 2 — 신선한 것은 **서버에 요청이 안 온다**. 음성 대조가 먼저다:
        # 이것이 깨지면 나머지 셋은 "전부 다시 받아서" 통과한 것일 수 있다
        assert "/fresh" not in paths, "29일 된 문서를 다시 받았다: %s" % paths
        # 시나리오 1 — 낡은 셋은 다시 나갔다. `/` 를 다시 받아야 링크가 자란다
        for path in ("/", "/stale", "/gone"):
            assert path in paths, "31일 된 %s 를 다시 안 받았다: %s" % (path, paths)
        # 시나리오 4 — 재크롤이 이번에 생긴 링크를 주웠다
        assert "/newlink" in paths, "재크롤이 새 링크를 안 주웠다: %s" % paths

        # 시나리오 1 — 갱신이 검색까지 간다
        assert "gwangju" in query(env, db, "gwangju"), "새 본문이 안 잡힌다"
        assert "결과 없음" in query(env, db, "pyeongsan"), "옛 본문이 남았다 — 덧쓰기다"
        # 시나리오 3 — 삭제는 `docs` 에서만. `pages` 는 묘비다
        assert "결과 없음" in query(env, db, "tongyeong"), "없어진 문서가 검색에 남았다"
        assert "1 문서 색인 제외" in out, "삭제가 조용하다: %r" % out
        row = sqlite3.connect(db).execute(
            "SELECT status, html FROM pages WHERE url = ?", (base + "/gone",)).fetchone()
        assert row == (404, None), "묘비가 아니라 지워졌거나 상태가 틀렸다: %r" % row
        # 새 링크는 색인까지 들어왔다
        assert "sokcho" in query(env, db, "sokcho"), "새 링크가 색인이 안 됐다"

    server.shutdown()

    # 시나리오 4 — 재크롤도 예외가 아니다. **서버 수신 시각**으로 잰다
    page_times = [t for t, p in second if p != "/robots.txt"]
    gaps = [b - a for a, b in zip(page_times, page_times[1:])]
    # 간격 보장은 클라이언트 팝 시점 기준 — 서버 수신 시각에는 왕복 지터가 실려
    # 0.05s 여유를 둔다. 하한을 더 내리면 시나리오를 낮추는 것이다 (crawl_e2e 와 같은 자)
    bad = [g for g in gaps if g < 0.95]
    assert not bad, "재크롤에서 1초 미만 간격 %d건: %s" % (len(bad), ["%.3f" % g for g in bad])

    print("e2e 통과 — 2회차에 낡은 셋(/·/stale·/gone)만 다시 나가고 29일 된 /fresh 는 "
          "요청 0건, 새 본문이 옛 본문을 갈아 끼웠고, 404 는 검색에서 빠지되 pages 는 "
          "묘비로 남았으며, 새 링크 %d건을 주우면서도 최소 간격 %.3fs 를 지켰다"
          % (paths.count("/newlink"), min(gaps)))


if __name__ == "__main__":
    main()
