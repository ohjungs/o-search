"""실물 마크업 분포에서 근거 문단 축을 잰다 — 오늘은 **표본 추출**까지다.

설계는 `docs/design_passage-real-sample.md`. 요지 하나만 여기 다시 적는다:
**실물 HTML 은 저장소에 한 바이트도 안 들어간다.** 픽스처가 담는 것은 URL 과 내용
지문(`sha256` 앞 16자)뿐이고, 본문은 실행 시점에 `data/crawl.db` 에서 읽는다. 남의
저작물과 아무도 안 본 꼬리 4,213 도메인의 내용을 커밋 이력에 영구히 싣지 않기 위해서다.

**DB 는 `mode=ro` 로 연다.** 테스트가 밖에서 잴 수 있는 것은 「쓰지 않았다」까지라
(순수 `SELECT` 는 `rw` 로 열어도 파일을 안 건드린다) 그 성질을 보장하는 몫은 이 줄이
진다 — `tests/test_passage_shapes.py` 의 docstring 이 그 천장을 적어 뒀다.

오늘 아는 모드는 `--resample` 하나다. 측정은 계획 117 스텝 4 에서 이 파일에 붙는다.

종료 코드: **0** 통과 · **1** 미달(드리프트) · **2** 측정 불능(DB·픽스처·사용법)
  — `passage_eval.py` 와 같은 갈림이다. 설정이 틀려 못 잰 것이 «미달» 로 보이면
  사람이 엉뚱한 것을 고치러 간다.

실행: PYTHONPATH=src python3 e2e/passage_shapes.py --resample
"""
import argparse
import hashlib
import json
import os
import sqlite3
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from websearch import store  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "crawl.db")
OUT = os.path.join(ROOT, "e2e", "shapes", "sample.jsonl")
COUNT = 1_000   # 설계 `## 못박는 수` — 110 건은 0 건을 봐도 95% 상한이 2.7% 라 못 닫는다
SEED = 117      # 계획 번호. 재추출이 같은 표본을 내야 옛 수와 새 수를 이을 수 있다
SHA_LEN = 16

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
            rows.append({"url": url,
                         "sha": hashlib.sha256(
                             html.encode("utf-8")).hexdigest()[:SHA_LEN]})
    finally:
        db.close()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print("표본 %d 건 → %s (모집단 %d · 시드 %d)"
          % (len(rows), out_path, len(urls), seed))
    return PASS


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--resample", action="store_true", required=True,
                   help="표본을 다시 뜬다 — 오늘 아는 유일한 모드다")
    p.add_argument("--db", default=DB)
    p.add_argument("--out", default=OUT)
    p.add_argument("--count", type=int, default=COUNT)
    p.add_argument("--seed", type=int, default=SEED)
    a = p.parse_args(argv)
    return resample(a.db, a.out, a.count, a.seed)


if __name__ == "__main__":
    sys.exit(main())
