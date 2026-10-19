"""실물에서 근거 문단 «소비» 축을 잰다 — 모양 블록이 근거로 나가 본문을 이기나.

설계는 `docs/design_passage-consume-census.md`. 요지 넷만 여기 다시 적는다.

**① 공급이 아니라 소비다.** `e2e/passage_shapes.py` 는 모양이 **몇 개 있나**를 세고
`e2e/passage_eval.py` 는 합성 64건에서 **정확도**를 잰다. 그 사이가 비어 있었다 —
「그 모양 블록이 질의에 대해 **근거로 선택되어** 본문을 이기나」를 아무도 안 셌고,
그래서 `digest` 후보 `[4]`·`[5]`·`[6]` 의 ⓑ 가 전부 「소비 측정이 나오는 날」에 묶여
못 열렸다.

**② 이 수는 «상한» 이다.** 질의를 **모양 블록 자신의 글자**에서 뽑는다 — 그 블록에
가장 유리한 질의다. 그래서 **분자가 0 이면 「가장 유리하게 줘도 안 이긴다」** 가 되어
후보가 닫힌다. 반대로 1 이상이면 후보가 열리고 그때 고치는 것은 **다음 계획**이다.

**③ 분자와 분모를 합치지 않는다.** 모양 문서가 질의로 **상위에 못 들면** 근거가 될
기회 자체가 없다 — 그 0 은 「안 이긴다」가 아니라 「안 만났다」다(설계 가정 3 이 실물에서
그것을 밟았다: `gnustatus-2011-10` 은 `Health` 로는 상위 10 에 안 들고
`Fontutils Gama Gawk` 로는 든다). 그래서 **분모(hit 수)를 함께 찍고, 분모가 0 이면
`rc=2`(재지 못했다)** 다.

**④ 고르는 규칙은 제품에게 묻는다.** `indexer.passages()` 를 **그대로** 부른다 —
베끼지도 않고 제품에서 빼내지도 않는다. 사본을 든 도구가 조용히 죽는 것은 이 저장소가
이미 한 번 밟은 사고다(`digest` 후보 `[6]`). **제품 `src/` 0줄이다.**

**DB 는 `mode=ro` 로 연다** — 단 `passages()` 안의 연결은 제품 것이라 못 고른다.
순수 `SELECT` 라 파일을 안 건드리는 것은 설계 가정 2 가 mtime·size 로 확인했다.

종료 코드: **0** 쟀다 · **1** 분자가 0 이 아니다(후보가 열린다) · **2** 재지 못했다
(DB·픽스처 부재 · 분모 0 · 정렬 깨짐). **2 는 판정이 아니다.**

    PYTHONPATH=src python3 e2e/passage_consume.py [--census]
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from websearch import extract, indexer, store          # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import passage_shapes                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "crawl.db")
FIX = os.path.join(ROOT, "e2e", "shapes", "consume.jsonl")
# census 창 — `baselines.md` 계획 119 가 6문서를 집은 그 창이다. 바꾸면 수가 안 이어진다
CENSUS_LIMIT, CENSUS_OFFSET = 20_000, 40_000
TERMS = 3        # 질의어 수. 설계 가정 3 의 `Fontutils Gama Gawk` 가 이 모양이다
HITS = 10        # `passages()` 의 limit — 제품 기본값이다. 넓히면 상한이 아니라 다른 것을 잰다
MIN_WORD = 3     # 한두 글자는 2-gram 색인에서 아무 문서나 맞춘다
MEASURED, SHAPE_WINS, UNMEASURABLE = 0, 1, 2

_WORD = re.compile(r"[^\W_]{%d,}" % MIN_WORD, re.UNICODE)


def unmeasurable(msg):
    print("측정 불능 — %s" % msg)
    return UNMEASURABLE


def query_terms(text, limit=TERMS):
    """블록 글자에서 질의어를 뽑는다 — **긴 것부터**, 같은 길이면 등장 순서.

    ponytail: 긴 단어가 드물다는 **감**이다 — 코퍼스 빈도를 보면 더 유리한 질의를
    고를 수 있지만, 이 자가 재는 것은 **상한**이라 질의가 더 유리해질수록 수가 커질
    뿐이고 0 이 나왔을 때의 결론(「유리하게 줘도 안 이긴다」)은 그대로다. 수가 1 이상
    나와 「얼마나 자주 이기나」를 묻게 되는 날 빈도로 올린다.
    """
    seen, words = set(), []
    for w in _WORD.findall(text):
        if w not in seen:
            seen.add(w)
            words.append(w)
    return sorted(words, key=lambda w: -len(w))[:limit]


def shape_positions(html, _ref=None):
    """제품 블록 중 **중첩 `<a>` 때문에 브라우저보다 덜 끊긴** 블록의 position 목록.

    `position` 은 **제품** 블록 순번이다 — `passages()` 가 그 번호를 내므로 그것과
    같아야 비교가 성립한다. 브라우저 답은 `passage_shapes._NestedRef` 가 들고 있고
    **그 답 자체는 그쪽 테스트가 따로 못박는다** — 여기서 다시 적으면 사본이 된다.

    **정렬이 깨지면 `[]` 가 아니라 `None` 이다.** 이 모양에서 제품은 브라우저 블록을
    «합치기만» 하므로 붙여 보면 글자가 맞아야 한다. 안 맞으면 내가 모르는 모양이고,
    그때 0 을 내면 「안 이긴다」로 읽혀 **죽은 측정기의 0** 이 된다.
    """
    prod = [b for _tag, b in extract.extract_blocks(html)]
    ref = (_ref(html) if _ref else
           [b for _tag, b in passage_shapes._nested_ref(html).blocks])
    out, j = [], 0
    for i, text in enumerate(prod):
        acc, taken = "", 0
        while j < len(ref) and len(acc) < len(text):
            acc += ref[j]
            j, taken = j + 1, taken + 1
        if acc != text:
            return None
        if taken > 1:
            out.append(i)
    return out if j == len(ref) else None


def _rows(fixture):
    with open(fixture, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _html_of(db, url):
    got = db.execute("SELECT html FROM pages WHERE url=?", (url,)).fetchone()
    return store.page_html(got[0]) if got and got[0] else None


def _clipped(html):
    """`passages()` 가 보는 것과 **같은** 바이트를 본다 — 안 자르면 position 이 밀린다."""
    return indexer._clip_by_tags(html[:indexer.MAX_PASSAGE_HTML])


def census(db_path, out_path):
    """census 창을 훑어 **중첩 `<a>` 로 덜 끊긴** 문서의 `{url, sha}` 를 동결한다.

    본문은 한 바이트도 안 쓴다 — `e2e/shapes/sample.jsonl` 과 같은 이유다
    (남의 저작물을 커밋 이력에 영구히 싣지 않는다).
    """
    if not os.path.exists(db_path):
        return unmeasurable("DB 가 없다: %s" % db_path)
    db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    rows, seen, desync = [], 0, 0
    try:
        for url, blob in db.execute(
                "SELECT url, html FROM pages WHERE status=200 AND html IS NOT NULL "
                "AND length(html)>0 LIMIT ? OFFSET ?",
                (CENSUS_LIMIT, CENSUS_OFFSET)):
            seen += 1
            html = store.page_html(blob)
            if not html:
                continue
            clipped = _clipped(html)
            pos = shape_positions(clipped)
            # **정렬 깨짐을 센다.** 첫 판은 `if pos:` 로 `None` 까지 먹어 **조용히**
            # 건너뛰었고, 그래서 계획 119 가 센 6문서 중 3문서를 못 보면서도 초록이었다.
            # 모르는 모양을 못 세면 모집단이 작아진 것을 모집단이 작다고 읽게 된다.
            if pos is None:
                desync += 1
            elif pos:
                rows.append({"url": url, "sha": passage_shapes._sha(html),
                             "positions": pos})
    finally:
        db.close()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in sorted(rows, key=lambda r: r["url"]):
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("census %d문서 훑어 모양 문서 %d건 · 정렬 깨짐 %d건 → %s (창 LIMIT %d OFFSET %d)"
          % (seen, len(rows), desync, out_path, CENSUS_LIMIT, CENSUS_OFFSET))
    if desync:
        print("정렬이 깨진 문서가 있다 — 제품이 브라우저 블록을 «합치기만» 한다는 전제가 "
              "그 문서에서 거짓이다. 모집단에서 빠졌으니 상한이 그만큼 넓다")
    return MEASURED


def measure(db_path, fixture, hits=HITS):
    if not os.path.exists(fixture):
        return unmeasurable("픽스처가 없다: %s — `--census` 로 한 번 뜬다" % fixture)
    if not os.path.exists(db_path):
        return unmeasurable("DB 가 없다: %s — 이 자는 그 DB 가 있는 기계에서만 돈다"
                            % db_path)
    try:
        rows = _rows(fixture)
    except ValueError as exc:
        return unmeasurable("픽스처를 못 읽는다: %r" % (exc,))
    if not rows:
        return unmeasurable("픽스처가 비었다: %s" % fixture)

    db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        docs, drifted, desync = [], 0, 0
        for row in rows:
            html = _html_of(db, row["url"])
            if not html or passage_shapes._sha(html) != row["sha"]:
                drifted += 1
                continue
            clipped = _clipped(html)
            pos = shape_positions(clipped)
            if pos is None:
                desync += 1
                continue
            docs.append((row["url"], clipped, pos))
    finally:
        db.close()

    blocks = denom = numer = asked = 0
    for url, clipped, pos in docs:
        texts = [b for _tag, b in extract.extract_blocks(clipped)]
        for p in pos:
            blocks += 1
            q = " ".join(query_terms(texts[p]))
            if not q:
                continue       # 질의어가 안 나오는 블록 — 분모에도 안 넣는다
            asked += 1
            got = [pp for u, _t, pp, _x in indexer.passages(db_path, q, limit=hits)
                   if u == url]
            if not got:
                continue       # 상위 %d 에 못 들었다 — 근거가 될 기회가 없다
            denom += 1
            numer += got[0] == p

    print("모양 문서 %d/%d (드리프트 %d · 정렬 깨짐 %d) · 모양 블록 %d · 질의 %d"
          % (len(docs), len(rows), drifted, desync, blocks, asked))
    print("분모(상위 %d 에 든 쌍) %d · **분자(모양 블록이 근거로 나간 쌍) %d**"
          % (hits, denom, numer))
    if desync:
        return unmeasurable("정렬이 깨진 문서가 %d건 있다 — 모르는 모양이다" % desync)
    if not denom:
        return unmeasurable("분모가 0 이다 — 모양 문서가 상위 %d 에 한 번도 못 들었다. "
                            "이 0 은 「안 이긴다」가 아니라 「안 만났다」다" % hits)
    print("상한 %.1f%% (%d/%d)" % (100.0 * numer / denom, numer, denom))
    if numer:
        print("후보가 열린다 — 모양 블록이 본문을 이긴 쌍이 %d 건이다" % numer)
        return SHAPE_WINS
    print("분자 0 — 질의를 모양 블록에 가장 유리하게 줘도 본문이 이긴다")
    return MEASURED


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--census", action="store_true",
                   help="모집단을 다시 뜬다 (약 8분 30초)")
    p.add_argument("--db", default=DB)
    p.add_argument("--fixture", default=FIX)
    p.add_argument("--hits", type=int, default=HITS)
    a = p.parse_args(argv)
    if a.census:
        return census(a.db, a.fixture)
    return measure(a.db, a.fixture, a.hits)


if __name__ == "__main__":
    sys.exit(main())
