"""러너 `e2e/passage_shapes.py` 의 **표본 추출**(`--resample`) 계약을 고정한다.

설계는 `docs/design_history_092.md` 의 `## 못박는 수` 표다 — 시드 **117** ·
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

sys.path.insert(0, os.path.join(_ROOT, "e2e"))
import passage_shapes  # noqa: E402

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


FIXTURE = os.path.join(_ROOT, "e2e", "shapes", "sample.jsonl")


class FixtureCase(unittest.TestCase):
    """저장소에 동결된 표본 — 설계 `## 못박는 수` 의 상한·건수·형식을 문다.

    DB 없이 돈다. 픽스처는 URL 과 지문뿐이라 이 셋은 어느 기계에서나 잴 수 있다.
    """

    def test_fixture_is_within_the_byte_ceiling(self):
        self.assertLessEqual(os.path.getsize(FIXTURE), 150 * 1024)

    def test_fixture_has_exactly_the_sample_count(self):
        with open(FIXTURE, encoding="utf-8") as f:
            self.assertEqual(1000, sum(1 for l in f if l.strip()))

    def test_fixture_lines_are_url_and_sha_only(self):
        """본문이 한 바이트라도 실리면 설계의 결정(A)이 깨진다 — 키는 둘뿐이다."""
        with open(FIXTURE, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        urls = [r["url"] for r in rows]
        self.assertEqual(sorted(set(urls)), urls)          # 정렬 · 중복 없음
        for r in rows:
            self.assertEqual({"url", "sha"}, set(r))
            self.assertRegex(r["sha"], r"^[0-9a-f]{16}$")
            self.assertRegex(r["url"], r"^https?://[^/@]+/")  # userinfo 없음


class ShapeCountsCase(unittest.TestCase):
    """수 셋의 판정 규칙 — 설계 `## 측정하는 것`. DB 없이 HTML 문자열만 먹인다."""

    def test_ceiling_a_b_is_zero_because_the_cut_no_longer_survives(self):
        """천장 ⓐ-b 의 모양 그대로 — `extract.py` 주석의 예문이다. **계획 118 이 닫았다.**

        **이 자가 세는 것은 «살아남은» 끊김이다.** 계획 117 판은 「끊을 조건이 섰나」를
        셌고, 계획 118 이 끊김을 블록 끝으로 미루자 **같은 수 301 이 뜻만 뒤집힌 채**
        나왔다(피해 → 막은 피해). 조건이 아니라 **블록이 실제로 갈렸나**를 함께 보게
        고쳤다 — 아래 음성 대조가 그 이빨이다.
        """
        c = passage_shapes.shape_counts(
            ["<p><a>레시피</a><a>영상</a> 에서 김치찌개를 끓인다.</p>"])
        self.assertEqual((0, 0), (c["ab"], c["ab_docs"]))

    def test_restoring_the_pre_118_cut_makes_the_counter_bite(self):
        """음성 대조 — 계획 118 전 동작(끊는 자리에서 바로 `_flush`)을 되살리면 **1** 이다.

        없으면 이 자는 「언제나 0」 이 되어 아무것도 검증하지 않는다. 되살리는 변이를
        제품에 심는 대신 하위 클래스로 그 자리만 되돌려 잰다.
        """
        class PreOneEighteen(passage_shapes._BlockParser):
            def handle_starttag(self, tag, attrs):
                if tag == "a" and self._after_link and not self._prose:
                    self._flush()                  # 계획 118 이 표식으로 바꾼 그 줄
                    self._after_link = False
                    super(passage_shapes._BlockParser, self).handle_starttag(tag, attrs)
                    self._els.append((tag, bool(self._els and self._els[-1][1]), True))
                    return
                super().handle_starttag(tag, attrs)

        class Probe(passage_shapes._Probe, PreOneEighteen):
            pass

        p = Probe()
        p.feed("<p><a>레시피</a><a>영상</a> 에서 김치찌개를 끓인다.</p>")
        p.close()
        self.assertEqual(1, p.ab)
        self.assertEqual(["레시피", "영상 에서 김치찌개를 끓인다."],
                         [t for _, t in p.blocks])     # 옛 판의 피해 그대로

    def test_nav_and_separate_blocks_are_not_a_b(self):
        """인접 링크로 끊겨도 뒤에 산문이 없으면 내비다. 별개 `<div>` 둘이 소문자로
        이어지는 것(MediaWiki 「Tools」→「move to sidebar hide」)은 경계가 아니라
        원래 다른 블록이다 — 소문자 판정이 실물에서 이것을 1,652건 중 대부분으로 셌다."""
        c = passage_shapes.shape_counts([
            "<nav><a>홈</a><a>소개</a><a>문의</a></nav>"
            "<div>Tools</div><div>move to sidebar hide</div>"
            "<p>산문 <a>링크</a> 다음 글자.</p>"])
        self.assertEqual(0, c["ab"])

    def test_probe_does_not_change_the_blocks(self):
        """탐침은 세기만 한다 — 블록이 하나라도 다르면 제품과 다른 것을 잰 것이다."""
        h = "<p><a>가</a><a>나</a> 다</p><ul><li>x<li>y</ul><pre>z</pre>"
        self.assertEqual(passage_shapes.extract_blocks(h), passage_shapes._probe(h).blocks)

    def test_pre_share_and_blocks_per_doc(self):
        c = passage_shapes.shape_counts(
            ["<p>Run it.</p><pre>x = 1</pre>", "<p>One.</p><p>Two.</p><p>Three.</p>"])
        self.assertEqual((1, 5), (c["pre"], c["blocks"]))
        self.assertEqual([2, 3], c["per_doc"])


class MeasureCase(unittest.TestCase):
    """기본 실행(측정)의 종료 코드 — 0 통과 · 1 드리프트 · 2 측정 불능."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "crawl.db")
        s = Store(self.db)
        for i in range(20):
            s.upsert("https://ok.example/%d" % i, "<p><a>See</a><a>the</a> end %d.</p>" % i, 200)
        self.fix = os.path.join(self.tmp, "sample.jsonl")
        r = self.run_shapes("--resample", "--out", self.fix, "--count", "20")
        self.assertEqual(PASS, r.returncode, r.stdout)

    def run_shapes(self, *args, db=None):
        return subprocess.run(
            [sys.executable, RUNNER, "--db", db or self.db] + list(args),
            capture_output=True, text=True)

    def test_measure_prints_real_and_synthetic_side_by_side(self):
        r = self.run_shapes("--sample", self.fix)
        self.assertEqual(PASS, r.returncode, r.stdout + r.stderr)
        self.assertIn("실물", r.stdout)
        self.assertIn("합성", r.stdout)
        # 계획 118 이 ⓐ-b 를 닫았으므로 **살아남은 끊김은 0** 이다 — 20건 전부
        # 그 모양인데도 0.0% 다. 되돌리면 100.0% 로 돌아온다(위 음성 대조와 같은 축)
        self.assertIn("ⓐ-b 문서   0.0% (0)", r.stdout)

    def test_drift_over_five_percent_is_shortfall(self):
        s = Store(self.db)
        for i in range(2):                    # 20건 중 2건 = 10% > 5%
            s.upsert("https://ok.example/%d" % i, "<p>recrawled</p>", 200)
        r = self.run_shapes("--sample", self.fix)
        self.assertEqual(SHORTFALL, r.returncode, r.stdout)
        self.assertIn("드리프트", r.stdout)

    def test_broken_sample_line_is_unmeasurable_not_shortfall(self):
        """깨진 줄·빠진 키가 트레이스백으로 죽으면 rc 1 — «미달» 로 샌다 [리뷰 117 R1]."""
        for bad in ('{"url": "https://ok.example/0"\n', '{"url": "https://ok.example/0"}\n'):
            with open(self.fix, "w", encoding="utf-8") as f:
                f.write(bad)
            r = self.run_shapes("--sample", self.fix)
            self.assertEqual(UNMEASURABLE, r.returncode, r.stdout + r.stderr)
            self.assertIn("측정 불능", r.stdout)

    def test_missing_db_or_sample_is_unmeasurable(self):
        r = self.run_shapes("--sample", self.fix, db=os.path.join(self.tmp, "없다.db"))
        self.assertEqual(UNMEASURABLE, r.returncode, r.stdout)
        self.assertIn("측정 불능", r.stdout)
        r = self.run_shapes("--sample", os.path.join(self.tmp, "없다.jsonl"))
        self.assertEqual(UNMEASURABLE, r.returncode, r.stdout)
        self.assertIn("측정 불능", r.stdout)


if __name__ == "__main__":
    unittest.main()
