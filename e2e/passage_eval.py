"""근거 문단(`GET /passages`)의 정확도와 지연을 잰다.

`docs/specs/concept.md` 기능 8 은 **반환 문단의 90% 이상이 질의어 또는 그 2-gram 을
포함**할 것을, 성능 5 는 **p95 500ms** 를 요구한다. 이 스크립트가 그 두 숫자를 내는
유일한 수단이고, 계약은 `docs/design_passage-api.md` 갈림길 4 다.

**코퍼스·질의는 `quality_eval` 과 같은 동결 fixture 를 그대로 읽는다** — 새로 하는
것은 HTML 포장 하나뿐이다. `quality_eval` 은 본문 전체를 `<p>` 하나로 감싸 문서당
블록이 1개라 문단을 잴 수가 없다. 여기서는 같은 본문을 **문장 단위 `<p>`** 로 감싼다.
정규화 뒤 색인 본문은 글자 하나까지 같고(`wrap` 의 단언이 매 실행 확인한다) 같은
색인이라 채택률을 recall 숫자 옆에 놓고 읽을 수 있다.

**정확도 100% 는 기본값이다** — 고르는 규칙(`indexer.passages`)과 여기 판정 규칙이
같은 술어라 그렇다. 숨기지 않고 적는다. 그래서 숫자를 **둘** 찍는다: 사양이 요구하는
**정확도**와, 실제로 움직이는 **채택률**(매치 문서 중 문단이 나온 비율, 기록만).
**가드가 이 도구의 이빨이다** — 거짓 초록을 잡는 것은 정확도가 아니라 종료 2 넷이다.

**p95 는 HTTP 로 잰다** — 사양 성능 5 는 API 예산이라 인프로세스 호출로는 그 예산을
잰 것이 아니다. 코퍼스가 64문서라 **FTS 축은 여기 안 들어 있고**(`perf_search.py`
3000문서가 그쪽이다) 코퍼스 문서가 작아 **문서 크기 축도 안 들어 있다**.

종료 코드: **0** 통과 · **1** 미달(정확도 <90% 또는 p95 >500ms) · **2** 측정 불능

실행: PYTHONPATH=src e2e/passage_eval.py [--corpus PATH] [--queries PATH] [--repeat N]
"""
import argparse
import html
import json
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import extract, indexer, serve  # noqa: E402
from websearch.store import Store  # noqa: E402
import perf_search  # noqa: E402 — p95 정의를 한 벌만 둔다(두 숫자가 나란히 읽힌다)
import quality_eval  # noqa: E402 — 동결 fixture 를 읽는 자리. 한 글자도 안 고친다

ACCURACY = 90     # % — 사양 기능 8. 경계는 통과 쪽이다("90% 이상")
BUDGET_MS = 500   # 사양 성능 5. `perf_search` 의 300ms 는 `/search` 예산이라 다른 숫자다
MIN_BLOCKS = 2    # 문서당 이보다 적으면 문단을 고른 것이 아니라 하나뿐인 것을 낸 것이다


def wrap(body):
    """본문을 문장 단위로 끊는다 — 마침표를 남기고 끊어 색인 본문을 안 바꾼다.

    `" ".join(wrap(body)) == body` 가 이 함수의 전부다. 이게 참이면 블록을 다시
    이어 붙인 것이 원문이라 `quality_eval` 과 **같은 것을 색인한 것**이 되고,
    채택률·정확도를 recall 숫자 옆에 놓을 수 있다. 거짓이면 두 도구가 다른 코퍼스를
    재고 있는 것이라 비교가 조용히 무의미해진다.
    """
    parts = body.split(". ")
    return [p + "." for p in parts[:-1]] + parts[-1:]


def build_index(db_path, corpus):
    """fixture 를 **문장 단위 `<p>`** 로 감싸 색인한다. (색인된 문서 수, 블록 수 목록).

    포장 말고는 `quality_eval.build_index` 와 같다 — 이스케이프도 같은 이유로 한다
    (코퍼스는 텍스트다. `a<b` 가 태그를 열면 매치 수와 순위가 조용히 달라진다).
    """
    store = Store(db_path)
    blocks = []
    for doc in corpus:
        sentences = wrap(doc["body"])
        if " ".join(sentences) != doc["body"]:
            # 파이썬 기본 종료 코드 1 로 죽게 두면 안 된다 — 1 은 "미달" 에 예약돼 있고
            # 여기는 잴 수 없다는 뜻이다 (`quality_eval` 이 fixture 오류를 2 로 내는 것과 같다)
            raise ValueError("G7 문장 끊기가 본문을 바꿨다 — quality_eval 과 다른 것을 "
                             "색인하게 되어 채택률을 recall 옆에 놓을 수 없다: %s" % doc["url"])
        page = ("<html><title>%s</title><body>%s</body></html>"
                % (html.escape(doc["title"]),
                   "".join("<p>%s</p>" % html.escape(s) for s in sentences)))
        store.upsert(doc["url"], page, 200)
        # 서버가 실제로 보게 될 경계로 센다 — 문장 수로 세면 파서가 못 끊어도 모른다
        blocks.append((doc["url"], len(extract.extract_blocks(page))))
    return indexer.index_pages(db_path), blocks


def needles(query):
    """사양 기능 8 의 술어 — 질의어와 그 2-gram.

    `indexer.passages` 가 문단을 **고를 때** 쓰는 재료와 같다. 그래서 정확도는
    구조적으로 100% 근처에서 나온다. 다른 술어를 지어내면 "무엇을 재는지"가 사양에서
    멀어질 뿐이라 같은 것을 쓰고, 대신 채택률과 가드로 이 도구의 이빨을 만든다.
    2-gram 정의는 `_bigrams` 를 부른다 — 다시 쓰면 색인과 갈릴 수 있다.
    """
    out = []
    for term in query.lower().translate(extract._CONTROL).split():
        out.append(term)
        out += indexer._bigrams(term).split()
    return out


def measure(base, queries, repeat):
    """질의마다 (질의, 문단 목록, 매치 문서 수)와 `/passages` 왕복 표본(ms)."""
    measured, samples = [], []
    for query in queries:
        url = base + "/passages?q=" + urllib.parse.quote(query["q"])
        for _ in range(repeat):
            start = time.perf_counter()
            with urllib.request.urlopen(url, timeout=30) as resp:  # 비2xx 는 HTTPError
                payload = json.loads(resp.read().decode())
            samples.append((time.perf_counter() - start) * 1000)
        # 분모는 같은 계약 위에서 가져온다 — 인프로세스로 세면 서버가 실제로 무엇을
        # 봤는지가 아니라 이 프로세스가 본 것을 세게 된다
        with urllib.request.urlopen(
                base + "/search?q=" + urllib.parse.quote(query["q"]), timeout=30) as resp:
            hits = json.loads(resp.read().decode())["results"]
        measured.append((query, payload["passages"], len(hits)))
    return measured, samples


def guard_defects(measured, blocks, bodies):
    """측정 자체가 성립하는가 — 비어 있으면 통과. 종료 2 로 가는 자리다."""
    defects = []
    thin = ["%s (블록 %d개)" % (url, n) for url, n in blocks if n < MIN_BLOCKS]
    if thin:
        defects.append("G4 문서당 블록이 %d개 미만이다 — 고를 문단이 없다: %s"
                       % (MIN_BLOCKS, ", ".join(thin[:3])))
    if not any(passages for _, passages, _ in measured):
        defects.append("G5 문단이 한 건도 안 나왔다 — 정확도 분모가 0이라 잴 것이 없다")
    # 문단이 본문 통째면 "근거 문단" 이 아니라 문서를 그대로 돌려준 것이다. 이때
    # 정확도는 자동으로 100% 가 되므로 숫자가 아니라 여기서 잡아야 한다.
    whole = ["%s (질의 [%s] %s)" % (p["url"], query["lang"], query["q"])
             for query, passages, _ in measured for p in passages
             if p["text"] == bodies.get(p["url"])]
    if whole:
        # 한 건이 나면 대개 전부 난다 — 앞 셋만 보인다(사유는 하나다)
        defects.append("G6 문단이 문서 본문과 통째로 같다 %d건: %s"
                       % (len(whole), ", ".join(whole[:3])))
    return defects


def report(measured, samples):
    """두 숫자를 출력하고 종료 코드(0·1)를 돌려준다."""
    judged = []
    for query, passages, _ in measured:
        found = needles(query["q"])  # 질의당 한 번만 만든다
        for p in passages:
            judged.append((query, p, any(n in p["text"].lower() for n in found)))
    hits = sum(n for _, _, n in measured)
    total = len(judged)
    matched = sum(1 for _, _, hit in judged if hit)
    accuracy = matched / total * 100
    p95 = perf_search.pct(samples, 0.95)

    print("문단 %d건 / 매치 문서 %d건 — 채택률 %.1f%% (기록만: 사양에 선이 없다)"
          % (total, hits, total / hits * 100))
    print("정확도 %.1f%% (%d/%d) — 질의어 또는 그 2-gram 을 담은 문단의 비율"
          % (accuracy, matched, total))
    print("지연 %d표본 — p50 %.2fms · p95 %.2fms (예산 %dms 의 %.1f%%)"
          % (len(samples), perf_search.pct(samples, 0.50), p95,
             BUDGET_MS, p95 / BUDGET_MS * 100))

    failed = ["  [%s] %s → %s" % (q["lang"], q["q"], p["text"][:60])
              for q, p, hit in judged if not hit]
    if accuracy < ACCURACY:
        print("정확도 %.1f%% 가 합격선 %d%% 미만이다 — 근거가 아닌 문단:"
              % (accuracy, ACCURACY), file=sys.stderr)
        for line in failed[:10]:
            print(line, file=sys.stderr)
        return 1
    if p95 > BUDGET_MS:
        print("p95 %.2fms 가 예산 %dms 를 넘었다 — 64문서에서 이 숫자는 규모 탓이 "
              "아니라 문단 경로가 망가진 것이다" % (p95, BUDGET_MS), file=sys.stderr)
        return 1
    print("통과 — 정확도 %.1f%% ≥ %d%% · p95 %.2fms ≤ %dms"
          % (accuracy, ACCURACY, p95, BUDGET_MS))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", default=os.path.join(quality_eval._QUALITY, "corpus.json"))
    parser.add_argument("--queries", default=os.path.join(quality_eval._QUALITY, "queries.json"))
    parser.add_argument("--repeat", type=int, default=5, help="질의당 반복 (기본 5 → 200표본)")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        # 트레이스백을 내며 rc 1 로 죽던 자리다 — 1 은 "미달" 에 예약돼 있고 이건
        # 사용법 오류라 잴 수 없다는 뜻이다 (G7 과 같은 이유로 2 로 낸다)
        print("--repeat 은 1 이상이어야 한다", file=sys.stderr)
        return 2
    try:
        corpus, queries = quality_eval._load(args.corpus), quality_eval._load(args.queries)
    except (OSError, ValueError) as exc:
        # 경로 오타·깨진 JSON 은 종료 2 다 — 1 은 "미달" 에 이미 예약돼 있다
        print("fixture 를 읽을 수 없다: %s" % exc, file=sys.stderr)
        return 2
    defects = quality_eval.fixture_defects(corpus, queries)
    if defects:
        for line in defects:
            print(line, file=sys.stderr)
        return 2
    # 분모가 성립하는 전제다 — 두 상수가 갈리면 `/search` 결과와 문단이 다른 문서집합이
    # 되고 채택률이 조용히 거짓말한다
    assert serve.PAGE_SIZE == serve.PASSAGE_LIMIT, (
        "PAGE_SIZE %d ≠ PASSAGE_LIMIT %d — 채택률의 분모가 분자와 다른 집합이다"
        % (serve.PAGE_SIZE, serve.PASSAGE_LIMIT))

    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "crawl.db")
        try:
            indexed, blocks = build_index(db_path, corpus)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        print("%d문서 색인 (블록 %d개) / 질의 %d개 × %d회"
              % (indexed, sum(n for _, n in blocks), len(queries), args.repeat))
        server = serve.make_server(db_path, port=0)
        threading.Thread(target=server.serve_forever,
                         kwargs={"poll_interval": 0.01}, daemon=True).start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            measure(base, queries[:1], 3)  # 워밍업 — 첫 요청의 임포트를 표본에서 뺀다
            measured, samples = measure(base, queries, args.repeat)
        finally:
            server.shutdown()
            server.server_close()

    bodies = {doc["url"]: " ".join(doc["body"].split()) for doc in corpus}
    problems = guard_defects(measured, blocks, bodies)
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        return 2
    return report(measured, samples)


if __name__ == "__main__":
    sys.exit(main())
