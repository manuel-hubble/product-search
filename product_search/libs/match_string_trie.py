import difflib
import itertools
import re
from re import Pattern

import pygtrie
from mac_vendor_lookup import MacLookup


class MatchStringTrie:
    __match_string_data: dict[str, list[list[str]]]
    __mac_regex: Pattern

    __trie: pygtrie.StringTrie[str, set[str]] = None
    __prefix_term_set: set[str] = set()
    # TODO: this seems to be abandoned, perhaps we should be using macaddress.io instead.
    __mac_database: MacLookup

    def __init__(self, match_string_data: dict[str, list[list[str]]]):
        self.__match_string_data = match_string_data
        self.__mac_regex = re.compile(r"^([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})|([0-9a-fA-F]{12})$")

    def __load_match_string_data(self):
        """
        Builds the prefix term set, the trie, and downloads the MAC address database.
        """
        trie: pygtrie.StringTrie[str, set[str]] = pygtrie.StringTrie()

        for title, match_strings in self.__match_string_data.items():
            self.__prefix_term_set.update(set(filter(None, itertools.chain.from_iterable(match_strings))))
            for product in itertools.product(*match_strings):
                long_key: str = "/".join(list(filter(None, product))[:3])
                short_key: str = "/".join(list(filter(None, product))[:2])
                full_key: str = "/".join(filter(None, product))

                for key in [full_key, long_key, short_key]:
                    if not trie.get(key):
                        trie[key] = {title}
                    else:
                        value: set[str] = trie[key]
                        value.add(title)

        self.__mac_database = MacLookup()
        self.__mac_database.update_vendors()

        trie.enable_sorting(enable=True)
        self.__trie = trie

    def search(self, *terms: str, best_only=True, strict_equal_key_only=False) -> set[str]:
        """

        :param terms:
        :param best_only:
        :param strict_equal_key_only:
        :return:
        """
        if not terms:
            return set()

        if not self.__trie:
            # Lazy load.
            self.__load_match_string_data()

        # See if there's a MAC address available.
        mac_address: str = next(filter(lambda x: self.__mac_regex.match(x), terms), None)
        if mac_address:
            self.__mac_database.lookup(mac_address)

        # Normalise terms to lowercase.
        terms_lower: list[str] = [arg.lower() for arg in self.__mac_address_lookup(*terms)]

        # Exclude both duplicated terms, and those not in the trie.
        terms_filtered: list[str] = list(dict.fromkeys(filter(lambda x: x in self.__prefix_term_set, terms_lower)))

        results: dict = {}
        for permutation in itertools.permutations(terms_filtered):
            permutation_key: str = "/".join(permutation)
            if permutation_key in self.__trie:
                # Found a perfect match.
                if strict_equal_key_only:
                    return self.__trie[permutation_key].copy()

                if not results.get(99):
                    results[99] = self.__trie[permutation_key].copy()
                else:
                    results[99].update(self.__trie[permutation_key].copy())
            elif not strict_equal_key_only:
                if self.__trie.has_subtrie(permutation_key):
                    # First, let's get approximations based in this key subtries, i.e. any entry our permutation key
                    # is a prefix of.
                    divider_count: int = permutation_key.count("/")
                    for key in self.__trie.iterkeys(permutation_key):
                        pos: int = 99 - abs(key.count("/") - divider_count)
                        if not results.get(pos):
                            results[pos] = self.__trie[key].copy()
                        else:
                            results[pos].update(self.__trie[key].copy())
                elif nodes := list(self.__trie.prefixes(permutation_key)):
                    # Now, let's traverse all the possible prefixes.
                    divider_count: int = permutation_key.count("/")
                    for node in nodes:
                        prefix = node[0]
                        pos: int = 99 - abs(prefix.count("/") - divider_count)
                        if not results.get(pos):
                            results[pos] = self.__trie[prefix].copy()
                        else:
                            results[pos].update(self.__trie[prefix].copy())

        # Find best list and return.
        result_list: list = [] if not results else next(iter(sorted(results.items(), reverse=True)))[1]
        if result_list and best_only:
            # Keep only the best ratios.
            ratios: list = list(map(lambda x: difflib.SequenceMatcher(lambda y: y in "-", x,
                                                                      " ".join(terms_filtered)).ratio(), result_list))
            ratio_filter = list(map(lambda x: 1 if max(ratios) == x else 0, ratios))
            best_list: list = list(itertools.compress(result_list, ratio_filter))

            # Sort alphabetically.
            best_list.sort()

            # And sort by length.
            best_list.sort(key=len)

            return {best_list[0]}

        return set(result_list)

    def __mac_address_lookup(self, *terms) -> list[str]:
        """

        :param terms:
        :return:
        """
        modified_terms: list[str] = []
        for term in terms:
            if self.__mac_regex.match(term):
                modified_terms.extend(re.split(r"[_,:.)(\\]", self.__mac_database.lookup(term)))
            else:
                modified_terms.append(term)

        return modified_terms
