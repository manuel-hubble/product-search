import unittest

from httpx import Response

from ..libs.fetcher import parse_response


class TestFetcher(unittest.TestCase):
    def test_parse_empty(self):
        self.assertIsNone(parse_response({}, "", ""))
