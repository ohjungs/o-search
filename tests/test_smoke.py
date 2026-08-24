import unittest

import websearch


class TestSmoke(unittest.TestCase):
    def test_package_has_version(self):
        self.assertEqual(websearch.__version__, "0.1")
