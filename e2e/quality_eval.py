"""검색 품질 — 상위 10건 안에 정답이 든 질의의 비율(recall@10)을 잰다.

`docs/specs/concept.md:22-23` 기능 2 의 합격선은 **한국어 20질의·영어 20질의에서
각각 80% 이상**이다. 이 스크립트가 그 숫자를 내는 유일한 수단이고,
계약은 `docs/design_quality-eval.md` `## 계약` 이다.

**가드가 이 도구의 핵심이다.** `limit=10` 이라 매치가 10건 이하인 질의는 정답이
구조적으로 항상 상위 10 안에 들어온다 — 포함률 1 이 나오지만 아무것도 잰 것이 아니다.
그래서 방해 문서가 실제로 방해하고 있는지를 사람 눈이 아니라 **매 실행 검사**한다.

  종료 코드 0  두 언어 모두 ≥80%
             1  미달 (품질 문제)
             2  코퍼스·질의 셋 결함(G1·G2·G3) 또는 사용법 — **미달과 구분한다**

네트워크도 크롤 루프도 타지 않는다. `e2e/perf_search.py` 와 같이 fixture 를 곧장
`pages` 에 넣고 색인한다.

실행: PYTHONPATH=src python3 e2e/quality_eval.py [--corpus PATH] [--queries PATH]
"""
import argparse
import collections
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch.indexer import index_pages, search  # noqa: E402
from websearch.store import Store  # noqa: E402

TOP_N = 10        # `concept.md:22` "상위 10건"
THRESHOLD = 80    # % — 같은 줄의 합격선. 경계는 통과 쪽이다("80% 이상")
PER_LANG = 20     # 언어별 질의 수. 다르면 분모가 달라져 숫자를 비교할 수 없다
LANG_NAMES = {"ko": "한국어", "en": "영어"}

_QUALITY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quality")


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        # 깨진 JSON 의 원 메시지에는 파일 이름이 없다 — 두 파일 중 어느 쪽인지 붙인다
        raise ValueError("%s — %s" % (path, exc)) from None


def fixture_defects(corpus, queries):
    """색인 전에 잡히는 결함(G1·G3) 목록. 비어 있으면 통과."""
    defects = []
    counts = collections.Counter(q["lang"] for q in queries)
    for lang in LANG_NAMES:
        if counts[lang] != PER_LANG:
            defects.append("G3 %s 질의가 %d개다 — %d개여야 한다"
                           % (LANG_NAMES[lang], counts[lang], PER_LANG))
    urls = {doc["url"] for doc in corpus}
    for query in queries:
        # 오타 난 정답은 조용히 불합격으로 보인다 — 품질이 아니라 fixture 문제다
        if query["answer"] not in urls:
            defects.append("G1 정답 URL 이 코퍼스에 없다: %s (질의 [%s] %s)"
                           % (query["answer"], query["lang"], query["q"]))
    return defects


def build_index(db_path, corpus):
    """fixture 를 최소 HTML 로 감싸 `pages` 에 넣고 색인한다. 색인된 문서 수."""
    store = Store(db_path)
    for doc in corpus:
        store.upsert(
            doc["url"],
            "<html><title>%s</title><body><p>%s</p></body></html>"
            % (doc["title"], doc["body"]),
            200,
        )
    return index_pages(db_path)


def measure(db_path, queries):
    """질의마다 (질의, 매치 수, 정답 순위 또는 None).

    `limit=100` 한 번으로 낸다 — 앞 10건이 곧 `limit=10` 결과이고
    (`ORDER BY bm25, rowid` 로 결정적), 같은 목록에서 매치 수와 순위를 함께 얻는다.
    """
    measured = []
    for query in queries:
        urls = [row[0] for row in search(db_path, query["q"], limit=100)]
        rank = urls.index(query["answer"]) + 1 if query["answer"] in urls else None
        measured.append((query, len(urls), rank))
    return measured


def report(measured):
    """포함률을 출력하고 종료 코드(0·1·2)를 돌려준다."""
    unmeasurable = ["G2 매치가 %d건뿐이다(≤%d) — 측정 불능: [%s] %s"
                    % (matches, TOP_N, query["lang"], query["q"])
                    for query, matches, _ in measured if matches <= TOP_N]
    if unmeasurable:
        # 못 잰 것을 미달로 보고하면 코퍼스 결함이 품질 숫자로 둔갑한다
        for line in unmeasurable:
            print(line, file=sys.stderr)
        print("가드 위반 %d건 — 포함률을 보고하지 않는다" % len(unmeasurable),
              file=sys.stderr)
        return 2

    hits, total = collections.Counter(), collections.Counter()
    misses = []
    for query, matches, rank in measured:
        total[query["lang"]] += 1
        if rank is not None and rank <= TOP_N:
            hits[query["lang"]] += 1
        else:
            misses.append("[%s] %s → %s (매치 %d건, 순위 %s)"
                          % (query["lang"], query["q"], query["answer"], matches,
                             rank if rank is not None else "밖"))

    code = 0
    for lang, name in LANG_NAMES.items():
        percent = hits[lang] * 100 // total[lang]
        print("%s %d/%d (%d%%)" % (name, hits[lang], total[lang], percent))
        if percent < THRESHOLD:
            code = 1
    for line in misses:
        print(line)
    print("합격선 %d%% — %s" % (THRESHOLD, "통과" if code == 0 else "미달"))
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", default=os.path.join(_QUALITY, "corpus.json"))
    parser.add_argument("--queries", default=os.path.join(_QUALITY, "queries.json"))
    args = parser.parse_args(argv)

    try:
        corpus, queries = _load(args.corpus), _load(args.queries)
    except (OSError, ValueError) as exc:
        # 경로 오타·깨진 JSON 도 종료 코드 2 다. 트레이스백은 파이썬 기본값 1 로
        # 나가는데 그 1 은 "품질 미달" 로 이미 예약돼 있다 (`## 계약`)
        print("fixture 를 읽을 수 없다: %s" % exc, file=sys.stderr)
        return 2
    defects = fixture_defects(corpus, queries)
    if defects:
        for line in defects:
            print(line, file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "crawl.db")
        print("%d문서 색인 / 질의 %d개" % (build_index(db_path, corpus), len(queries)))
        return report(measure(db_path, queries))


if __name__ == "__main__":
    sys.exit(main())
