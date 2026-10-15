"""계획 116 e2e 시나리오 ② — 실물에서 «근거 문단이 어느 방향으로» 움직였나.

인자: `<src 경로> [문서 수]`. 출력은 기계가 비교할 수 있게 `키<TAB>값` 한 줄씩.
**한 스크립트를 두 트리에 먹인다** — 배선이 양쪽에서 같다는 것이 비교의 전제다
(계획 115 `scenario.py` 와 같은 관용구). 질의는 **제목에서 기계로 뽑아** 양쪽에서
같게 만든다. 코퍼스는 문서마다 새 색인이라 다른 문서의 매치가 섞이지 않는다.
"""
import os, random, re, sqlite3, sys, tempfile

sys.path.insert(0, sys.argv[1])
from websearch import extract, indexer, store      # noqa: E402
from websearch.store import Store                  # noqa: E402

CRAWL = "/Users/t2025-m0191/work/websearch/data/crawl.db"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 110
WORD = re.compile(r"[0-9A-Za-z가-힣]{3,}")

db = sqlite3.connect("file:%s?mode=ro" % CRAWL, uri=True)
rows = db.execute("SELECT url, html FROM pages WHERE status=200").fetchmany(4000)
db.close()
random.seed(116)                                   # 두 트리에서 같은 표본
sample = random.sample(rows, min(N * 3, len(rows)))

tmp = tempfile.mkdtemp()
seen = 0
for url, blob in sample:
    if seen >= N:
        break
    html = store.page_html(blob)
    if not html:
        continue
    title, _body = extract.extract_text(html)
    words = [w.lower() for w in WORD.findall(title)][:2]
    if len(words) < 2:                             # 질의를 못 만들면 건너뛴다
        continue
    seen += 1
    path = os.path.join(tmp, "idx%d.db" % seen)
    s = Store(path)
    s.upsert(url, html, 200)
    indexer.index_pages(path)
    q = " ".join(words)
    hits = indexer.passages(path, q)
    if not hits:
        print("NONE\t%s\t%s" % (url, q))
        continue
    _u, _t, pos, text = hits[0]
    print("TOP\t%s\t%s\t%d\t%d\t%s"
          % (url, q, pos, len(text), text[:60].replace("\t", " ")))
print("DOCS\t%d" % seen)
