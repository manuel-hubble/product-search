import json
import pathlib
import unittest

from product_search.libs.match_string_trie import MatchStringTrie


class BaseTestCases:
    class AbstractTestMatchStringTrie(unittest.TestCase):
        _trie: MatchStringTrie

        def test_empty_values(self):
            trie = MatchStringTrie({})
            self.assertEqual(set(), trie.search("one", "two", "three"))

            self.assertEqual(set(), self._trie.search())

        def test_exact_match(self):
            self.assertEqual({"Canonical Ubuntu Linux 14.04.1"},
                             self._trie.search("canonical", "ubuntu", "linux", "14", "04", "1"))
            self.assertEqual({"Canonical Ubuntu Linux 14.04.1"},
                             self._trie.search("linux", "ubuntu", "14", "04", "1"))
            self.assertEqual({"Canonical Ubuntu Linux 14.04.1"},
                             self._trie.search("ubuntu", "linux", "14", "04", "1"))
            self.assertEqual({"Microsoft Windows Vista"},
                             self._trie.search("microsoft", "windows", "vista", strict_equal_key_only=True))
            self.assertEqual({"Apple iPad OS 16.1.2"}, self._trie.search("ipados", "16", "1", "2"))
            self.assertEqual({"Apple iPad OS -"}, self._trie.search("ipados"))
            self.assertEqual({"Apple macOS 13.1"}, self._trie.search("macos", "13", "1"))
            self.assertEqual({"Apple macOS 13.0.1"}, self._trie.search("macos", "13", "0", "1"))
            self.assertEqual({"Apple iPhone OS 5.0.1 iPod touch"},
                             self._trie.search("iphone", "os", "5", "0", "1", "ipodtouch"))

        def test_approximate_match(self):
            # From `uname -a` on a System76 laptop:
            # Linux pop-os 5.3.0-22-generic #24+system76~1573659475~19.04~26b2022-Ubuntu SMP Wed Nov 13 20:0 x86_64
            # x86_64 x86_64 GNU/Linux
            self.assertEqual({"Canonical Ubuntu Linux 19.04"},
                             self._trie.search("Linux" "pop-os" "5", "3", "0", "22", "generic", "#24", "system76",
                                               "1573659475", "19", "04", "26b2022", "Ubuntu", "SMP",
                                               "x86_64" "GNU/Linux"))


operating_systems: dict = {
    "Canonical Ubuntu Linux 14.04.1": [["canonical", None], ["ubuntu linux", "ubuntu"], ["14"], ["04"],
                                       ["1"]],
    "Canonical Ubuntu Linux 19.04": [["canonical", None], ["ubuntu linux", "ubuntu"], ["19"], ["04"]],
    "Microsoft Windows Vista": [["microsoft", None], ["windows"], ["vista"]],
    "Microsoft Windows Server 2012 R2": [["microsoft", None], ["windows"], ["server"], ["2012"], ["r2"]],
    "Microsoft Windows Server 2012 R2 Service Pack 1 on X64": [["microsoft", None], ["windows"], ["server"], ["2012"],
                                                               ["r2"], ["sp1"], ["x64"]],
    "Microsoft Windows 10 1507 64-bit": [["microsoft", None], ["windows"], ["10"], ["1507"], ["x64"]],
    "Microsoft Windows 10 1507 32-bit": [["microsoft", None], ["windows"], ["10"], ["1507"], ["x86"]],
    "Cisco IOS 11.1": [["cisco", None], ["ios"], ["11"], ["1"]],
    "Cisco IOS 11.1.13 IA": [["cisco", None], ["ios"], ["11"], ["1"], ["13"]],
    "Apple iPhone OS 5.0.1": [["apple", None], ["iphone", "ios"], ["os", None], ["5"], ["0"], ["1"]],
    "Apple iPhone OS 5.0.1 iPad": [["apple", None], ["iphone", "ios"], ["os", None], ["5"], ["0"], ["1"], ["ipad"]],
    "Apple iPhone OS 5.0.1 iPhone": [["apple", None], ["iphone", "ios"], ["os", None], ["5"], ["0"], ["1"], ["iphone"]],
    "Apple iPhone OS 5.0.1 iPod touch": [["apple", None], ["iphone", "ios"], ["os", None], ["5"], ["0"], ["1"],
                                         ["ipodtouch"]],
    "Apple iPhone OS 11.1.13": [["apple", None], ["iphone", "ios"], ["os", None], ["11"], ["1"], ["13"]],
    "Apple iPad OS 16.1": [["apple", None], ["ipados"], ["16"], ["1"]],
    "Apple iPad OS 16.1.2": [["apple", None], ["ipados"], ["16"], ["1"], ["2"]],
    "Apple iPad OS 16.1.4": [["apple", None], ["ipados"], ["16"], ["1"], ["4"]],
    "Apple iPad OS -": [["apple", None], ["ipados"]],
    "Apple macOS 13.0": [["apple", None], ["macos"], ["13"], ["0"]],
    "Apple macOS 13.0.1": [["apple", None], ["macos"], ["13"], ["0"], ["1"]],
    "Apple macOS 13.1": [["apple", None], ["macos"], ["13"], ["1"]],
    "Red Hat Enterprise Linux 8.6 Server Edition": [["redhat", None], ["enterprise"], ["linux"], ["8"], ["6"]]}


class TestSmallMatchStringTrie(BaseTestCases.AbstractTestMatchStringTrie):
    def setUp(self) -> None:
        self.maxDiff = None
        self._trie = MatchStringTrie(operating_systems)

    def test_small_exact_match(self):
        self.assertEqual({"Apple iPhone OS 11.1.13"},
                         self._trie.search("iphone", "os", "11", "1", "13", strict_equal_key_only=True))

    def test_small_approximate_match(self):
        self.assertEqual({"Apple iPad OS 16.1"}, self._trie.search("ipados", "16"))
        self.assertEqual(
            {"Cisco IOS 11.1.13 IA", "Cisco IOS 11.1", "Apple iPhone OS 11.1.13"},
            self._trie.search("ios", "11", best_only=False))
        self.assertEqual({"Microsoft Windows 10 1507 64-bit", "Microsoft Windows 10 1507 32-bit"},
                         self._trie.search("Windows", "10", "Pro", "10", "0", "19042", best_only=False))
        self.assertEqual({"Microsoft Windows Server 2012 R2"}, self._trie.search("Windows", "Server", "2016"))
        self.assertEqual({"Red Hat Enterprise Linux 8.6 Server Edition"},
                         self._trie.search("Red", "Hat", "Enterprise", "Linux", "6", "0"))
        self.assertEqual({"Microsoft Windows 10 1507 32-bit",
                          "Microsoft Windows 10 1507 64-bit",
                          "Microsoft Windows Server 2012 R2",
                          "Microsoft Windows Server 2012 R2 Service Pack 1 on X64",
                          "Microsoft Windows Vista"},
                         self._trie.search("microsoft", "windows", best_only=False))
        self.assertEqual({"Cisco IOS 11.1.13 IA", "Apple iPhone OS 11.1.13"},
                         self._trie.search("ios", "11", "1", "13", best_only=False, strict_equal_key_only=True))


class TestLargeMatchStringTrie(BaseTestCases.AbstractTestMatchStringTrie):
    def setUp(self) -> None:
        self.maxDiff = None
        self._cpe_grokked_string_file_path = str(pathlib.Path.joinpath(pathlib.Path().parent.resolve(), "resources",
                                                                       "operating_system-cpe-grokked-strings.json"))
        with open(self._cpe_grokked_string_file_path) as f:
            self._trie = MatchStringTrie(json.load(f))

    def test_large_exact_match(self):
        self.assertEqual({"Red Hat Enterprise Linux 6.0"},
                         self._trie.search("Red", "Hat", "Enterprise", "Linux", "6", "0"))

    def test_large_approximate_match(self):
        self.assertEqual({"Apple iPad OS 16.0"}, self._trie.search("ipados", "16"))
        self.assertEqual({"Cisco IOS 11.0"}, self._trie.search("ios", "11", best_only=True))
        self.assertEqual({'Microsoft Windows 10 1903'},
                         self._trie.search("Windows", "10", "Pro", "10", "0", "19042", best_only=True))
        self.assertEqual({"Microsoft Windows Server 2016"}, self._trie.search("Windows", "Server", "2016"))
