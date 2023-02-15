import pathlib
import unittest


class TestIntegration(unittest.TestCase):
    _cpe_match_string_file_path: str
    _cpe_grokked_string_file_path: str

    def setUp(self) -> None:
        self.maxDiff = None

        self._cpe_match_string_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                     "operating_system-cpe-match-strings.json"))
        self._cpe_grokked_string_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                       "operating_system-cpe-grokked-strings.json"))

    def test_grokker_to_trie(self):
        pass
