"""숨김/스킵 속 인접 링크가 «보이는» 문단을 끊는가 — 제품 경로와 같은 배선으로 센다.

**이 도구가 재던 축은 닫혔다 — 2026-10-15 리뷰 116 [R116-5].** 계획 115 의 숨김 경계
수정이 `main` 에 들어가 `Base`(제품)와 `Guarded`(제품+가드)가 **같아졌고**, 그래서 아래
배선 검사 ① 이 이제 `배선 FAIL` 을 낸다 — 도구가 고장난 것이 아니라 **isolate 하던 차이가
사라진 것**이다. 그보다 먼저 계획 116 이 `_els` 를 세 칸으로 넓혀 **이 사본이 `IndexError`
로 죽어 있었다**(전수 880 OK 인 채로 · 이 파일을 돌리는 테스트가 0개다). 죽는 쪽은 고쳤다.
**은퇴시킬지는 사람 몫이다** — 야간 모드는 파일을 지우지 않는다. 측정 결과는
`docs/e2e/nav-inline-passage/result.md` 에 남아 있고, 이 축을 지키는 자는 이제
`tests/test_extract.py` 의 `test_links_hidden_from_people_do_not_cut_the_visible_paragraph` 다.

배선 검사 3단: ① 합성 모양 ② 압축 해제가 실제로 HTML 을 내는가
③ 제품과 같은 캡·클립을 타는가. 셋 다 찍은 뒤에만 실물을 센다.
"""
import sqlite3, sys
sys.path.insert(0, "/Users/t2025-m0191/work/websearch/src")
from websearch import extract, indexer, store

Base = extract._BlockParser


class Guarded(Base):
    def handle_starttag(self, tag, attrs):
        # 제품의 산문 판정(`_prose`)을 **함께 들고 간다** — 안 들면 이 사본이 재는
        # 축이 「숨김 경계」가 아니라 「숨김 경계 + 계획 116」이 된다
        if (tag == "a" and self._after_link and not self._prose
                and not self._blind()):
            self._flush()
        self._after_link = False
        super(Base, self).handle_starttag(tag, attrs)
        while self._els and tag in extract._IMPLIED_END.get(self._els[-1][0], ()):
            if self._open and self._open[-1] == self._els[-1][0]:
                self._open.pop()
            self._els.pop()
        if tag not in extract._VOID_TAGS:
            # 세 칸이다 — 계획 116 이 `_els` 에 「링크 안인가」를 더했다. 두 칸으로
            # 두면 제품의 `handle_data` 가 `[2]` 를 읽다 **IndexError** 로 터진다
            # (리뷰 116 [R116-5] 가 실제로 밟았다 — 전수 880 OK 인 채로 이 도구만
            # 죽어 있었다). **이 메서드는 제품 사본이라 제품이 바뀌면 함께 고친다**
            self._els.append((tag, (self._els and self._els[-1][1])
                              or extract._is_hidden(tag, attrs),
                              tag == 'a' or bool(self._els and self._els[-1][2])))
        if self._in_title or tag in extract._INLINE_TAGS or tag in extract._NON_BLOCK_TAGS:
            return
        self._open.append(tag)

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if self._after_link and self._blind():
            self._after_link = False

    def _blind(self):
        return bool(self._skip_depth) or bool(self._els and self._els[-1][1])


def blocks_with(cls, html):
    old = extract._BlockParser
    extract._BlockParser = cls
    try:
        return extract.extract_blocks(html)
    finally:
        extract._BlockParser = old


# ── ① 합성 배선 ────────────────────────────────────────────────────────
WIRING = [
    ('<p>김치찌개는<span style="display:none"><a>광고</a><a>제휴</a></span> 배추를 절인 찌개다.</p>',
     [("p", "김치찌개는"), ("p", "배추를 절인 찌개다.")],
     [("p", "김치찌개는 배추를 절인 찌개다.")]),
    ("<nav><a>김치찌개</a><a>된장찌개</a></nav>",
     [("nav", "김치찌개"), ("nav", "된장찌개")],
     [("nav", "김치찌개"), ("nav", "된장찌개")]),
    ("<p>보이는<span hidden><a>가</a>숨<a>나</a></span>뒤</p>",
     [("p", "보이는"), ("p", "뒤")], [("p", "보이는뒤")]),
    ("<p>앞<noscript><a>가</a><a>나</a></noscript> 뒤 문장이다.</p>",
     [("p", "앞"), ("p", "뒤 문장이다.")], [("p", "앞 뒤 문장이다.")]),
]
for html, want_now, want_guard in WIRING:
    got = (blocks_with(Base, html), blocks_with(Guarded, html))
    if got != (want_now, want_guard):
        sys.exit("배선 FAIL %r\n  now=%r\n  grd=%r" % (html, got[0], got[1]))
print("① 합성 배선 OK (4모양)")

db = sqlite3.connect("file:/Users/t2025-m0191/work/websearch/data/crawl.db?mode=ro", uri=True)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
rows = db.execute("SELECT url, html FROM pages WHERE status=200 AND html IS NOT NULL "
                  "ORDER BY random() LIMIT ?", (n,)).fetchall()

# ── ② 압축 해제가 실제로 HTML 을 내는가 ────────────────────────────────
sample = store.page_html(rows[0][1])
assert isinstance(sample, str) and "<" in sample, "압축 해제가 HTML 을 안 낸다"
tagged = sum(1 for _u, b in rows[:40] if "<" in store.page_html(b).lower())
print("② 압축 해제 OK — 앞 40건 중 %d건이 태그를 가졌다 (%r…)" % (tagged, sample[:40]))

# ── ③ 제품과 같은 캡·클립 ──────────────────────────────────────────────
def product_html(blob):
    return indexer._clip_by_tags(store.page_html(blob)[:indexer.MAX_PASSAGE_HTML])

print("③ 캡=%d · 클립=%s" % (indexer.MAX_PASSAGE_HTML, indexer._clip_by_tags.__name__))

# ── 실물 census ────────────────────────────────────────────────────────
diff_docs, short_frag, examples, blind_seen = 0, 0, [], 0
for url, blob in rows:
    html = product_html(blob)
    low = html.lower()
    if "noscript" in low or "hidden" in low or "display:none" in low or "display: none" in low:
        blind_seen += 1
    a, b = blocks_with(Base, html), blocks_with(Guarded, html)
    if a == b:
        continue
    diff_docs += 1
    extra = [t for (_g, t) in a if (_g, t) not in b]
    if any(len(t) < 30 for t in extra):
        short_frag += 1
    if len(examples) < 8:
        examples.append((url, len(a), len(b), [t[:50] for t in extra[:3]]))

print("\n표본 %d문서 · 숨김 마크업을 가진 문서 %d건 · "
      "**숨김 경계가 블록을 바꾸는 문서 %d건(%.1f%%)** · 30자 미만 조각 %d건"
      % (len(rows), blind_seen, diff_docs, 100.0 * diff_docs / len(rows), short_frag))
for url, na, nb, extra in examples:
    print("  - %s  %d→%d  %r" % (url[:64], na, nb, extra))

# ── 방아쇠 자체를 센다 — 「없다」와 「있는데 무해하다」를 가른다 ──────────
class Counting(Base):
    hits = 0
    def handle_starttag(self, tag, attrs):
        if (tag == "a" and self._after_link
                and (self._skip_depth or (self._els and self._els[-1][1]))):
            Counting.hits += 1
        return super().handle_starttag(tag, attrs)

trig_docs, trig_hits = 0, 0
for url, blob in rows:
    Counting.hits = 0
    blocks_with(Counting, product_html(blob))
    if Counting.hits:
        trig_docs += 1
        trig_hits += Counting.hits
print("방아쇠(숨김 안에서 인접 링크 경계가 선 자리): 문서 %d건 · 총 %d회"
      % (trig_docs, trig_hits))
