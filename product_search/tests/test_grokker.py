import json
import pathlib
import unittest

from product_search.libs.grokker import grok_cpe_file, transform_cpe_name


class TestGrokCpeFile(unittest.TestCase):
    _cpe_match_string_file_path: str
    _os_synonyms_file_path: str
    _cpe_grokked_string_file_path: str

    def setUp(self) -> None:
        self.maxDiff = None
        self._cpe_match_string_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                     "operating_system-cpe-match-strings.json"))
        self._os_synonyms_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                "os_synonyms.json"))
        self._cpe_grokked_string_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                       "operating_system-cpe-grokked-strings.json"))

    def test_load_cpe_file(self):
        grokked_cpe_data: dict = grok_cpe_file(self._cpe_match_string_file_path,
                                               synonyms_file=self._os_synonyms_file_path)
        self.assertIsNotNone(grokked_cpe_data)
        self.assertIsInstance(grokked_cpe_data, dict)

        with open(self._cpe_grokked_string_file_path) as f:
            self.assertDictEqual(json.load(f), grokked_cpe_data)


class TestTransformCpeName(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_empty_cpe(self):
        self.assertEqual([], transform_cpe_name(""))

    def test_malformed_cpe(self):
        self.assertEqual([], transform_cpe_name("windows"))
        self.assertEqual([], transform_cpe_name("cpe:2.2:o:microsoft"))

    def test_good_cpe(self):
        self.assertEqual([["redhat", None], ["enterprise"], ["linux"], ["desktop"], ["6"], ["0"]],
                         transform_cpe_name("cpe:2.3:o:redhat:enterprise_linux_desktop:6.0:*:*:*:*:*:*:*"))
        self.assertEqual([["microsoft", None], ["windows"], ["10"], ["2019"], ["enterprise"], ["ltsc"]],
                         transform_cpe_name("cpe:2.3:o:microsoft:windows_10:2019:*:*:*:enterprise_ltsc:*:*:*"))
        self.assertEqual([["cisco", None], ["ios"], ["12"], ["0"], ["20"], ["st2"]],
                         transform_cpe_name("cpe:2.3:o:cisco:ios:12.0\\(20\\)st2:*:*:*:*:*:*:*"))
