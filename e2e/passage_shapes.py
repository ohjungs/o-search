"""실물 마크업 분포에서 근거 문단 축을 잰다 — 오늘은 **표본 추출**까지다.

설계는 `docs/design_history_092.md`. 요지 하나만 여기 다시 적는다:
**실물 HTML 은 저장소에 한 바이트도 안 들어간다.** 픽스처가 담는 것은 URL 과 내용
지문(`sha256` 앞 16자)뿐이고, 본문은 실행 시점에 `data/crawl.db` 에서 읽는다. 남의
저작물과 아무도 안 본 꼬리 4,213 도메인의 내용을 커밋 이력에 영구히 싣지 않기 위해서다.

**DB 는 `mode=ro` 로 연다.** 테스트가 밖에서 잴 수 있는 것은 「쓰지 않았다」까지라
(순수 `SELECT` 는 `rw` 로 열어도 파일을 안 건드린다) 그 성질을 보장하는 몫은 이 줄이
진다 — `tests/test_passage_shapes.py` 의 docstring 이 그 천장을 적어 뒀다.

기본 실행은 **측정**이다 — 표본을 DB 에서 읽어 지문을 대조하고, `extract_blocks()`
출력에서 수 셋(설계 `## 측정하는 것`)을 내어 합성 64건의 같은 수와 나란히 찍는다.
`--resample` 은 표본을 다시 뜬다.

**천장 ⓐ-b 는 블록 출력으로는 못 센다** — 첫 판은 「앞 블록이 종결부호 없이 끝나고 다음
블록이 소문자로 시작」을 셌는데, 실물 1,652건이 거의 MediaWiki 메뉴(「Tools」→「move to
sidebar hide」, 원래 다른 `<div>` 둘)였다. 그래서 `_Probe` 가 파서 안에서 **인접 링크
경계가 끊은 자리**를 직접 보고, 그 뒤 블록에 **링크 밖 글자(산문)** 가 쌓였을 때만 센다.
**2026-10-18 계획 118 이 ⓐ-b 를 닫으면서 이 자를 한 번 고쳤다** — 「끊을 조건이 섰나」만
보던 판은 끊김이 블록 끝으로 미뤄진 뒤에도 **같은 수를 뜻만 뒤집어** 냈다(피해 → 막은
피해). 지금은 **블록이 실제로 갈렸는지**를 함께 본다(`_Probe` docstring).
ponytail: 탐침은 `_BlockParser` 의 사설 이름(`_after_link`·`_prose`·`text_parts`)에 기댄다
— 파서가 바뀌면 `tests/test_passage_shapes.py` 의 예문 단언이 먼저 빨개진다.

종료 코드: **0** 통과 · **1** 미달(드리프트) · **2** 측정 불능(DB·픽스처·사용법)
  — `passage_eval.py` 와 같은 갈림이다. 설정이 틀려 못 잰 것이 «미달» 로 보이면
  사람이 엉뚱한 것을 고치러 간다.

실행: PYTHONPATH=src python3 e2e/passage_shapes.py [--resample]
"""
import argparse
import hashlib
import json
import os
import random
import sqlite3
import statistics
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import store  # noqa: E402
from websearch.extract import _BlockParser, extract_blocks  # noqa: E402
import passage_eval  # noqa: E402 — 합성 쪽 포장(`wrap`)을 한 벌만 둔다
import quality_eval  # noqa: E402 — 동결 코퍼스를 읽는 자리

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "crawl.db")
OUT = os.path.join(ROOT, "e2e", "shapes", "sample.jsonl")
COUNT = 1_000   # 설계 `## 못박는 수` — 110 건은 0 건을 봐도 95% 상한이 2.7% 라 못 닫는다
SEED = 117      # 계획 번호. 재추출이 같은 표본을 내야 옛 수와 새 수를 이을 수 있다
SHA_LEN = 16
DRIFT = 5       # % — 넘으면 재크롤이 표본을 갈았다. 옛 수와 새 수가 안 이어진다

PASS, SHORTFALL, UNMEASURABLE = 0, 1, 2


def unmeasurable(msg):
    print("측정 불능 — %s" % msg)
    return UNMEASURABLE


def resample(db_path, out_path, count, seed):
    """모집단에서 `count` 건을 뽑아 `{"url", "sha"}` 를 한 줄씩 쓴다.

    모집단은 `status=200` **이고** `html` 이 비지 않은 행이다 — 오류 페이지의
    마크업을 세면 분포가 거짓이 된다. 층화하지 않는다(설계 `## 못박는 수`).
    """
    if not os.path.exists(db_path):
        return unmeasurable("DB 가 없다: %s" % db_path)
    db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        urls = [u for (u,) in db.execute(
            "SELECT url FROM pages WHERE status=200 AND html IS NOT NULL")]
        if count > len(urls):
            return unmeasurable("표본 %d > 모집단 %d — 전수를 표본이라 부르게 된다"
                                % (count, len(urls)))
        random.seed(seed)
        rows = []
        for url in sorted(random.sample(urls, count)):
            blob = db.execute(
                "SELECT html FROM pages WHERE url=?", (url,)).fetchone()[0]
            html = store.page_html(blob)
            if not html:                       # 압축분이 빈 문자열인 행 — 세지 않는다
                return unmeasurable("본문이 빈 행이 표본에 들었다: %s" % url)
            rows.append({"url": url, "sha": _sha(html)})
    finally:
        db.close()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("표본 %d 건 → %s (모집단 %d · 시드 %d)"
          % (len(rows), out_path, len(urls), seed))
    return PASS


def _sha(html):
    return hashlib.sha256(html.encode("utf-8")).hexdigest()[:SHA_LEN]


class _Probe(_BlockParser):
    """블록은 그대로 내고, 인접 링크 경계가 **실제로 끊은 뒤** 산문이 이어진 블록 수(`ab`)만 센다.

    **「조건이 섰나」가 아니라 「블록이 갈렸나」를 센다 — 계획 118 이 그 차이를 실물에서
    한 번 보여 줬다.** 계획 117 판은 끊을 조건만 봤고, 계획 118 이 끊김을 블록 끝으로
    미루자 **같은 수 301 이 뜻만 뒤집힌 채**(피해 → 막은 피해) 그대로 나왔다 — 이 파일
    docstring 이 「파서가 바뀌면 단언이 먼저 빨개진다」고 적어 뒀는데 **안 빨개졌다.**
    그래서 `super()` 호출이 블록을 **늘렸는지**를 함께 본다. `<a>` 는 인라인이라 그
    호출에서 블록이 느는 길은 끊김뿐이다. 음성 대조는
    `tests/test_passage_shapes.py` 의 `test_restoring_the_pre_118_cut_makes_the_counter_bite`.
    """

    def __init__(self):
        self.ab, self._cut = 0, False
        super().__init__()

    def handle_starttag(self, tag, attrs):
        cut = tag == "a" and self._after_link and not self._prose and bool(self.text_parts)
        before = len(self.blocks)
        super().handle_starttag(tag, attrs)     # 제품이 여기서 끊으면 블록이 늘어난다
        self._cut = self._cut or (cut and len(self.blocks) > before)

    def _flush(self):
        if self._cut and self._prose:
            self.ab += 1
        self._cut = False
        super()._flush()


def _probe(html):
    p = _Probe()
    p.feed(html)
    p.close()
    return p


def shape_counts(htmls):
    """HTML 묶음에서 수 셋의 재료를 센다 — 색인도 질의도 안 한다."""
    c = {"ab": 0, "ab_docs": 0, "pre": 0, "blocks": 0, "per_doc": []}
    for html in htmls:
        p = _probe(html)
        c["per_doc"].append(len(p.blocks))
        c["blocks"] += len(p.blocks)
        c["pre"] += sum(tag == "pre" for tag, _ in p.blocks)
        c["ab"] += p.ab
        c["ab_docs"] += p.ab > 0
    return c


def _row(name, c):
    pct = lambda a, b: "%.1f%%" % (100.0 * a / b) if b else "—"
    d = c["per_doc"]
    return ("%-4s %5d문서 | ⓐ-b 문서 %6s (%d) · 블록 %6s (%d) | pre %6s (%d/%d) | "
            "블록/문서 최소 %d · 중앙 %g · 최대 %d"
            % (name, len(d), pct(c["ab_docs"], len(d)), c["ab_docs"],
               pct(c["ab"], c["blocks"]), c["ab"],
               pct(c["pre"], c["blocks"]), c["pre"], c["blocks"],
               min(d), statistics.median(d), max(d)))


def measure(db_path, sample_path):
    if not os.path.exists(sample_path):
        return unmeasurable("표본이 없다: %s" % sample_path)
    if not os.path.exists(db_path):
        return unmeasurable("DB 가 없다: %s — 이 자는 그 DB 가 있는 기계에서만 돈다"
                            % db_path)
    try:
        with open(sample_path, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        rows = [{"url": r["url"], "sha": r["sha"]} for r in rows]
        # 코퍼스도 여기서 읽는다 — 트레이스백의 rc 1 은 «미달» 로 샌다
        corpus = quality_eval._load(os.path.join(quality_eval._QUALITY, "corpus.json"))
    except (ValueError, KeyError, TypeError) as exc:
        return unmeasurable("표본·코퍼스를 못 읽는다: %r" % (exc,))
    if not rows:
        return unmeasurable("표본이 비었다: %s" % sample_path)
    db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        htmls, drifted = [], 0
        for row in rows:
            got = db.execute("SELECT html FROM pages WHERE url=?",
                             (row["url"],)).fetchone()
            html = store.page_html(got[0]) if got else None
            if not html or _sha(html) != row["sha"]:
                drifted += 1
                continue
            htmls.append(html)
    finally:
        db.close()
    synth = ["".join("<p>%s</p>" % passage_eval.html.escape(s)
                     for s in passage_eval.wrap(doc["body"])) for doc in corpus]
    print(_row("실물", shape_counts(htmls)) if htmls else "실물 0문서")
    print(_row("합성", shape_counts(synth)))
    print("드리프트 %d/%d (상한 %d%%)" % (drifted, len(rows), DRIFT))
    if drifted * 100 > DRIFT * len(rows):
        print("미달 — 드리프트가 상한을 넘었다. 재크롤이 표본을 갈았으니 --resample 로 "
              "다시 뜨고 기준선을 새로 잇는다")
        return SHORTFALL
    return PASS


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--resample", action="store_true", help="표본을 다시 뜬다")
    p.add_argument("--sample", default=OUT, help="측정할 표본")
    p.add_argument("--db", default=DB)
    p.add_argument("--out", default=OUT)
    p.add_argument("--count", type=int, default=COUNT)
    p.add_argument("--seed", type=int, default=SEED)
    a = p.parse_args(argv)
    if a.resample:
        return resample(a.db, a.out, a.count, a.seed)
    return measure(a.db, a.sample)


if __name__ == "__main__":
    sys.exit(main())
