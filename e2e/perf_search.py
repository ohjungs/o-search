"""GET /search 의 p50·p95 를 재서 기준선을 만든다.

컨셉 성능 1 은 **100만 문서에서 p95 300ms** 다. 여기서 재는 색인은 그보다 훨씬
작으므로 나오는 숫자는 **합격 판정이 아니라 기준선**이다 — 색인이 커지거나 질의
경로가 바뀌었을 때 이 숫자와 비교해 회귀를 잡는 것이 목적이다
(`docs/plan_search-api.md` 가정 절).

순차 측정이다. 동시 요청 부하 곡선은 서버 구조를 바꿀 근거가 필요할 때 잰다
(`docs/design_search-api.md` 범위 밖).

실행: PYTHONPATH=src python3 e2e/perf_search.py [문서수] [질의당_반복]
"""
import json
import os
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

from websearch import indexer, serve

# 컨셉 성능 1. 100만 문서 기준이라 이 규모에서는 한참 밑이어야 한다 —
# 여기에 닿았다면 규모 때문이 아니라 질의 경로가 망가진 것이다.
BUDGET_MS = 300

NARROW = "문서 %04d"  # 색인 제목 형식. 질의 셋과 색인이 이 하나를 같이 본다


def query_paths(docs):
    """넓게 걸리는 질의·좁은 질의·무결과·깊은 페이지를 섞는다.

    깊은 페이지가 가장 느린 쪽이고, 기준선은 가장 느린 쪽을 포함해야 쓸모가 있다.
    좁은 질의는 **문서 수에서 유도한다** — 제목을 고정 문자열로 박으면 규모를 줄여
    돌렸을 때 조용히 무결과 버킷이 하나 더 되고, 재려던 것이 사라진 줄 모른다.
    """
    q = urllib.parse.quote("김치")
    return [
        "/search?q=" + q,                                   # 전 문서에 걸린다
        "/search?q=%s&page=%d" % (q, serve.MAX_PAGE),       # 상한 페이지 — 가장 깊은 OFFSET
        "/search?q=" + urllib.parse.quote(NARROW % (docs // 2)),  # 한 문서만
        "/search?q=" + urllib.parse.quote("우주선"),         # 무결과
        "/search?q=beginners",                              # 영어
    ]


def build_index(db_path, docs):
    """crawl 을 거치지 않고 pages 테이블을 직접 채운다 — 측정 대상은 질의 경로다."""
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, html TEXT, status INTEGER)")
    db.executemany("INSERT INTO pages VALUES (?, ?, 200)", [
        ("http://p.test/%05d" % i,
         "<html><title>%s</title><body><p>김치 %s "
         "Learning Python for beginners. 배추와 고춧가루가 필요하다.</p></body></html>"
         % (NARROW % i, "김치 " * (i % 5)))
        for i in range(docs)
    ])
    db.commit()
    db.close()
    return indexer.index_pages(db_path)


def measure(base, path, repeat):
    """왕복 시간(ms) 목록. 응답 본문까지 다 읽어야 실제 왕복이다."""
    url = base + path
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        with urllib.request.urlopen(url, timeout=30) as resp:  # 비2xx 는 HTTPError 로 터진다
            resp.read()
        samples.append((time.perf_counter() - start) * 1000)
    return samples


def pct(samples, q):
    """관측된 표본 중 하나를 고른다 — 보간하지 않는다(지연 보고의 관례)."""
    return sorted(samples)[min(int(len(samples) * q), len(samples) - 1)]


def main(argv):
    docs = int(argv[1]) if len(argv) > 1 else 3000
    repeat = int(argv[2]) if len(argv) > 2 else 200

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        t0 = time.perf_counter()
        indexed = build_index(db, docs)
        index_s = time.perf_counter() - t0

        server = serve.make_server(db, port=0)
        threading.Thread(target=server.serve_forever,
                         kwargs={"poll_interval": 0.01}, daemon=True).start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            paths = query_paths(docs)
            for path in paths:  # 워밍업 — 첫 요청의 임포트·페이지캐시를 표본에서 뺀다
                measure(base, path, 3)

            # 버킷이 의도한 것을 재고 있는지 확인한다 — 조용히 무결과가 되면 측정이 거짓말한다
            with urllib.request.urlopen(base + paths[2], timeout=30) as resp:
                narrow = json.loads(resp.read().decode())["results"]
            assert len(narrow) == 1, "좁은 질의 버킷이 %d건이다 (1건이어야 한다)" % len(narrow)

            per_query = [(path, measure(base, path, repeat)) for path in paths]
        finally:
            server.shutdown()
            server.server_close()

    every = [ms for _, samples in per_query for ms in samples]
    print("색인 %d 문서 (%.1fs) / 질의 %d종 × %d회 = %d 요청, 순차·로컬"
          % (indexed, index_s, len(paths), repeat, len(every)))
    print("  전체   p50 %6.2fms   p95 %6.2fms   최대 %6.2fms   평균 %6.2fms"
          % (pct(every, 0.50), pct(every, 0.95), max(every), statistics.mean(every)))
    for path, samples in per_query:
        print("  %-46s p50 %6.2fms  p95 %6.2fms"
              % (urllib.parse.unquote(path), pct(samples, 0.50), pct(samples, 0.95)))

    p95 = pct(every, 0.95)
    assert p95 < BUDGET_MS, ("p95 %.1fms 가 예산 %dms 를 넘었다 — 이 규모에서 이 숫자는 "
                             "규모 탓이 아니라 질의 경로가 망가진 것이다" % (p95, BUDGET_MS))
    print("기준선 — p95 %.2fms (예산 %dms 의 %.1f%%). docs/project.md 품질 기준과 비교할 것"
          % (p95, BUDGET_MS, p95 / BUDGET_MS * 100))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
