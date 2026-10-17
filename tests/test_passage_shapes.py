"""러너 `e2e/passage_shapes.py` 의 **표본 추출**(`--resample`) 계약을 고정한다.

설계는 `docs/design_passage-real-sample.md` 의 `## 못박는 수` 표다 — 시드 **117** ·
모집단 `status=200` **및** `html` 이 비지 않은 행 · 한 줄 한 문서(JSONL).

**이 파일은 실물 `data/crawl.db` 를 안 본다.** 같은 스키마의 작은 DB 를 지어 먹인다 —
전수가 10GB 파일에 매달리면 그 기계에서만 도는 테스트가 되고(`project.md` 격리),
모집단 갈래를 비틀어 보려면 어차피 내가 지은 DB 라야 한다.

**「읽기 전용으로 열었나」는 직접 못 잰다.** 순수 `SELECT` 는 `mode=rw` 로 열어도
파일을 안 건드려서, 열기 방식을 밖에서 구별할 수가 없다. 그래서 여기서 재는 것은
**「쓰지 않았다」** — 실행 전후 DB 바이트가 같은지다. 그것이 실제로 지키려는 성질이고,
열기 방식은 그 성질을 **보장하는 수단**이라 러너 쪽 주석이 진다. 이것이 이 자의 천장이다.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(_ROOT, "e2e", "passage_shapes.py")

sys.path.insert(0, os.path.join(_ROOT, "src"))
from websearch.store import Store  # noqa: E402

PASS, SHORTFALL, UNMEASURABLE = 0, 1, 2


class ResampleCase(unittest.TestCase):
    """모집단과 시드가 계약대로인지. 표본 수는 작게 두고 `--count` 로 민다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "crawl.db")
        s = Store(self.db)
        for i in range(20):
            s.upsert("https://ok.example/%d" % i, "<p>본문 %d</p>" % i, 200)
        s.upsert("https://dead.example/404", "<p>없다</p>", 404)      # 모집단 밖
        s.upsert("https://empty.example/", None, 200)                 # 모집단 밖
        s.close() if hasattr(s, "close") else None

    def resample(self, out, count=5, seed=117, db=None):
        return subprocess.run(
            [sys.executable, RUNNER, "--resample", "--db", db or self.db,
             "--out", out, "--count", str(count), "--seed", str(seed)],
            capture_output=True, text=True)

    def lines(self, path):
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    def test_resample_writes_one_json_object_per_line(self):
        out = os.path.join(self.tmp, "sample.jsonl")
        r = self.resample(out)
        self.assertEqual(PASS, r.returncode, r.stderr)
        rows = self.lines(out)
        self.assertEqual(5, len(rows))
        for row in rows:
            self.assertEqual({"url", "sha"}, set(row))
            self.assertEqual(16, len(row["sha"]))

    def test_population_excludes_non_200_and_empty_html(self):
        """`status=200` 이 아니거나 `html` 이 비면 안 뽑힌다 — 오류 페이지의
        마크업을 세면 분포가 거짓이 된다 (설계 `## 못박는 수`)."""
        out = os.path.join(self.tmp, "sample.jsonl")
        self.assertEqual(PASS, self.resample(out, count=20).returncode)
        urls = {row["url"] for row in self.lines(out)}
        self.assertEqual(20, len(urls))          # 모집단이 정확히 20이다
        self.assertNotIn("https://dead.example/404", urls)
        self.assertNotIn("https://empty.example/", urls)

    def test_same_seed_gives_the_same_sample(self):
        """재추출이 같은 표본을 내야 옛 수와 새 수를 이을 수 있다."""
        a, b, c = (os.path.join(self.tmp, n) for n in ("a", "b", "c"))
        self.resample(a, count=5, seed=117)
        self.resample(b, count=5, seed=117)
        self.resample(c, count=5, seed=118)
        self.assertEqual(open(a).read(), open(b).read())
        self.assertNotEqual(open(a).read(), open(c).read())

    def test_sha_is_of_the_decompressed_html(self):
        """지문은 **원문**의 것이다 — 압축분을 해시하면 재크롤이 압축만 바꿔도
        드리프트로 잡힌다 (`store.page_html` 이 두 꼴을 받는 이유와 같은 자리)."""
        out = os.path.join(self.tmp, "sample.jsonl")
        self.resample(out, count=20)
        want = {"https://ok.example/%d" % i:
                hashlib.sha256(("<p>본문 %d</p>" % i).encode("utf-8")).hexdigest()[:16]
                for i in range(20)}
        for row in self.lines(out):
            self.assertEqual(want[row["url"]], row["sha"], row["url"])

    def test_resample_does_not_write_to_the_db(self):
        """이 자의 천장은 파일 docstring 에 적혀 있다 — 재는 것은 「쓰지 않았다」다."""
        before = hashlib.sha256(open(self.db, "rb").read()).hexdigest()
        r = self.resample(os.path.join(self.tmp, "sample.jsonl"), count=5)
        self.assertEqual(PASS, r.returncode, r.stderr)   # 안 돌고도 통과하는 것을 막는다
        self.assertEqual(before, hashlib.sha256(open(self.db, "rb").read()).hexdigest())

    def test_missing_db_is_unmeasurable_not_shortfall(self):
        """설정이 틀려 못 잰 것이 «미달» 로 보이면 사람이 엉뚱한 것을 고치러 간다
        (`test_passage_eval.py` 와 같은 갈림)."""
        r = self.resample(os.path.join(self.tmp, "sample.jsonl"),
                          db=os.path.join(self.tmp, "없다.db"))
        self.assertEqual(UNMEASURABLE, r.returncode, r.stdout)
        self.assertIn("측정 불능", r.stdout)   # 인터프리터가 낸 2 와 구별한다

    def test_count_larger_than_population_is_unmeasurable(self):
        """표본이 모집단보다 크면 수를 낸 것이 아니라 전수를 낸 것이다 — 조용히
        작은 표본을 내면 1,000건이라는 계약이 거짓말이 된다."""
        r = self.resample(os.path.join(self.tmp, "sample.jsonl"), count=21)
        self.assertEqual(UNMEASURABLE, r.returncode, r.stdout)
        self.assertIn("측정 불능", r.stdout)   # 인터프리터가 낸 2 와 구별한다


if __name__ == "__main__":
    unittest.main()
