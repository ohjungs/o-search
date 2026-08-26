"""품질 평가 fixture(코퍼스·질의 셋)가 계약을 지키는지 본다.

형식은 `docs/design_history_006.md` `## 계약`, 개수·구조는 같은 문서 `## 구조`,
색인 검사는 `docs/plan_history_006.md` 스텝 1·2 완료 기준이다.

fixture 는 **동결**이라 여기서 깨지면 이후 모든 품질 숫자의 기준선이 흔들린다.
"""

import collections
import json
import os
import tempfile
import unittest

from websearch.indexer import index_pages, search
from websearch.store import Store

_QUALITY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "e2e", "quality"
)
CORPUS = os.path.join(_QUALITY, "corpus.json")
QUERIES = os.path.join(_QUALITY, "queries.json")

FIELDS = {"url", "lang", "title", "body"}
QUERY_FIELDS = {"q", "lang", "answer"}

# URL 두 번째 조각(토픽) → 그 토픽 16문서가 **전부 공유**하는 어휘.
# 이 어휘로 질의했을 때 16건이 다 걸려야 러너 가드 G2(매치 ≤ 10 = 측정 불능)에 여유가 생긴다.
TOPIC_TERMS = {
    "kimchi": "김치찌개",
    "jeju": "제주도",
    "sourdough": "sourdough",
    "python": "python",
}


def _load(path=CORPUS):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestQualityCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = _load()

    def test_64_docs_half_per_language(self):
        self.assertEqual(len(self.docs), 64)
        self.assertEqual(
            collections.Counter(d["lang"] for d in self.docs),
            {"ko": 32, "en": 32},
        )

    def test_fields_are_exactly_the_contract(self):
        for doc in self.docs:
            self.assertEqual(set(doc), FIELDS, doc.get("url"))
            for key in FIELDS:
                self.assertIsInstance(doc[key], str, (doc.get("url"), key))
                self.assertTrue(doc[key].strip(), (doc.get("url"), key))
            self.assertIn(doc["lang"], ("ko", "en"), doc["url"])
            # 러너가 감싸는 HTML 을 깨뜨리는 문서는 색인 내용이 조용히 달라진다
            self.assertNotIn("<", doc["title"] + doc["body"], doc["url"])

    def test_urls_are_unique(self):
        urls = [d["url"] for d in self.docs]
        self.assertEqual(len(set(urls)), len(urls))

    def test_four_topics_of_16(self):
        topics = collections.Counter()
        for doc in self.docs:
            _, _, _, lang, topic, _ = doc["url"].split("/")
            self.assertEqual(lang, doc["lang"], doc["url"])
            topics[topic] += 1
        self.assertEqual(topics, dict.fromkeys(TOPIC_TERMS, 16))

    def test_indexes_whole_corpus_and_shares_topic_vocabulary(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db_path = os.path.join(tmp.name, "crawl.db")
        store = Store(db_path)
        for doc in self.docs:
            store.upsert(
                doc["url"],
                "<html><title>%s</title><body><p>%s</p></body></html>"
                % (doc["title"], doc["body"]),
                200,
            )
        # is_noindex 로 조용히 빠지는 문서가 있으면 여기서 64 밑으로 떨어진다
        self.assertEqual(index_pages(db_path), 64)
        for topic, term in TOPIC_TERMS.items():
            self.assertGreaterEqual(len(search(db_path, term, limit=100)), 16, topic)


class TestQualityQueries(unittest.TestCase):
    """`plan_history_006.md` 스텝 2 완료 기준 — 20/20 이고 정답 URL 이 실제로 있다."""

    @classmethod
    def setUpClass(cls):
        cls.queries = _load(QUERIES)
        cls.by_url = {d["url"]: d for d in _load()}

    def test_40_queries_20_per_language(self):
        self.assertEqual(len(self.queries), 40)
        self.assertEqual(
            collections.Counter(q["lang"] for q in self.queries),
            {"ko": 20, "en": 20},
        )

    def test_fields_are_exactly_the_contract(self):
        for query in self.queries:
            self.assertEqual(set(query), QUERY_FIELDS, query.get("q"))
            for key in QUERY_FIELDS:
                self.assertIsInstance(query[key], str, (query.get("q"), key))
                self.assertTrue(query[key].strip(), (query.get("q"), key))
            self.assertIn(query["lang"], ("ko", "en"), query["q"])

    def test_queries_are_single_token(self):
        # 다어절은 AND 라 매치 수가 10 밑으로 떨어져 러너 가드 G2 에 걸린다
        # (`design_history_006.md` `## 착수 전 탐침`)
        for query in self.queries:
            self.assertNotIn(" ", query["q"])

    def test_answers_exist_in_corpus_and_are_distinct(self):
        # 오타 난 정답은 조용히 불합격으로 보인다 — 러너 가드 G1 과 같은 검사
        answers = [q["answer"] for q in self.queries]
        self.assertEqual(len(set(answers)), 40)
        self.assertEqual(len(set(q["q"] for q in self.queries)), 40)
        for query in self.queries:
            doc = self.by_url.get(query["answer"])
            self.assertIsNotNone(doc, query["answer"])
            self.assertEqual(doc["lang"], query["lang"], query["q"])

    def test_answers_are_the_first_ten_of_each_topic(self):
        # 11~16 은 정답이 없는 순수 방해 문서다 (`design_history_006.md` `## 구조`)
        for query in self.queries:
            self.assertLessEqual(int(query["answer"].rsplit("/", 1)[1]), 10, query["q"])


if __name__ == "__main__":
    unittest.main()
