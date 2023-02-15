import datetime
import json
import pathlib
import unittest

from ..libs.fetcher import parse_response


class TestFetcher(unittest.TestCase):
    _cpe_api_response_file_path: str

    def setUp(self) -> None:
        self._cpe_api_response_file_path = str(
            pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), "resources", "cpe_api_response.json"))

    def test_parse_empty(self):
        self.assertIsNone(parse_response({}, "", ""))

    def test_filters(self):
        with open(self._cpe_api_response_file_path) as f:
            self.assertListEqual([{"cpe_name": "cpe:2.3:o:apple:iphone_os:1.1.2:-:iphone:*:*:*:*:*",
                                   "title": "Apple iPhone OS 1.1.2 iPhone"},
                                  {"cpe_name": "cpe:2.3:o:apple:iphone_os:1.1.3:-:iphone:*:*:*:*:*",
                                   "title": "Apple iPhone OS 1.1.3 iPhone"},
                                  {"cpe_name": "cpe:2.3:o:apple:iphone_os:1.1.4:-:iphone:*:*:*:*:*",
                                   "title": "Apple iPhone OS 1.1.4 iPhone"}],
                                 parse_response(json.load(f), now=datetime.datetime.now().isoformat(),
                                                exclude_keywords=["ipodtouch"]))
