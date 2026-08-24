import os
import tempfile
import unittest

from websearch.store import Store


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def test_upsert_then_has(self):
        self.assertFalse(self.store.has("http://a.com/"))
        self.store.upsert("http://a.com/", "<html/>", 200)
        self.assertTrue(self.store.has("http://a.com/"))

    def test_upsert_twice_updates_not_duplicates(self):
        self.store.upsert("http://a.com/", "v1", 200)
        self.store.upsert("http://a.com/", "v2", 200)
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.get_html("http://a.com/"), "v2")

    def test_creates_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            Store(os.path.join(tmp, "sub", "x.db")).upsert("http://a.com/", "h", 200)

    def test_failed_fetch_stored_without_html(self):
        self.store.upsert("http://a.com/gone", None, 404)
        self.assertTrue(self.store.has("http://a.com/gone"))
        self.assertIsNone(self.store.get_html("http://a.com/gone"))
