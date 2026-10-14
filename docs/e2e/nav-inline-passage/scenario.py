"""계획 115 e2e 시나리오 ①② — 한 배선으로 두 트리에서 돌려 비교한다.

인자: <src 경로>. 출력은 기계가 비교할 수 있게 `키<TAB>값` 한 줄씩.
코퍼스는 «실물 모양»(내비·목차가 앞 · 본문이 뒤)이고 **실물 크롤 DB 에서 뜬 두 장**을
함께 넣는다 — 합성만 재면 테스트 phase 가 YELLOW 를 낸 그 간극을 또 재게 된다.
"""
import hashlib, os, sqlite3, sys, tempfile

sys.path.insert(0, sys.argv[1])
from websearch import indexer, store           # noqa: E402
from websearch.store import Store              # noqa: E402

CRAWL = "/Users/t2025-m0191/work/websearch/data/crawl.db"
WIKI = """<!DOCTYPE html><html><head><title>김치찌개 - 위키백과</title></head><body>
<nav class="vector-menu"><a href="/wiki/대문">대문</a><a href="/wiki/김치찌개">김치찌개</a>
<a href="/wiki/된장찌개">된장찌개</a><a href="/wiki/김치찌개_만들기">김치찌개 만들기</a></nav>
<div id="toc"><a href="#재료">김치찌개 재료</a><a href="#순서">된장찌개 비교</a></div>
<article><p>김치찌개는 잘 익은 배추김치를 돼지고기나 참치와 함께 끓여 낸 된장찌개와
나란히 꼽히는 한국의 대표적인 찌개다.</p>
<p>재료는 김치와 돼지고기, 두부, 대파가 기본이다.</p></article>
<footer><a href="/privacy">개인정보</a><a href="/terms">약관</a></footer></body></html>"""

rows = [("http://wiki.test/kimchi", WIKI)]
cdb = sqlite3.connect("file:%s?mode=ro" % CRAWL, uri=True)
for pat in ("%Fundaci%n_Wikimedia%", "%lrzsz%"):
    r = cdb.execute("SELECT url, html FROM pages WHERE status=200 AND url LIKE ? LIMIT 1",
                    (pat,)).fetchone()
    if r:
        rows.append((r[0], store.page_html(r[1])))
cdb.close()
print("CORPUS\t%d" % len(rows))

path = os.path.join(tempfile.mkdtemp(), "idx.db")
s = Store(path)
for url, html in rows:
    s.upsert(url, html, 200)
indexer.index_pages(path)

# ② 색인 본문을 바이트로 뜬다 (재색인 유무의 자)
db = sqlite3.connect(path)
for url, body in db.execute("SELECT url, body FROM docs ORDER BY url"):
    print("BODY\t%s\t%s\t%d" % (url, hashlib.sha256(body.encode()).hexdigest()[:16], len(body)))

# ① 두 낱말 질의로 근거 문단을 받는다
for q in ("김치찌개 된장찌개", "wikimedia foundation", "lrzsz zmodem"):
    for url, _t, pos, text in indexer.passages(path, q):
        print("PASSAGE\t%s\t%s\t%d\t%s" % (q, url, pos, text[:90].replace("\t", " ")))
