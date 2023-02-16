import difflib
import itertools

import pygtrie


class MatchStringTrie:
    __match_string_data: dict[str, list[list[str]]]
    __trie: pygtrie.StringTrie[str, set[str]] = None
    __prefix_term_set: set[str] = set()

    def __init__(self, match_string_data: dict[str, list[list[str]]]):
        self.__match_string_data = match_string_data

    def __load_match_string_data(self):
        """
        Builds both the prefix term set, and the trie.
        """
        trie: pygtrie.StringTrie[str, set[str]] = pygtrie.StringTrie()

        for title, match_strings in self.__match_string_data.items():
            self.__prefix_term_set.update(set(filter(None, itertools.chain.from_iterable(match_strings))))
            for product in itertools.product(*match_strings):
                partial_key: str = "/".join(list(filter(None, product))[:2])
                full_key: str = "/".join(filter(None, product))

                for key in [full_key, partial_key]:
                    if not trie.get(key):
                        trie[key] = {title}
                    else:
                        value: set[str] = trie[key]
                        value.add(title)

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

        # Normalise terms to lowercase.
        terms_lower: list[str] = [arg.lower() for arg in terms]

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
                    for key in self.__trie.iterkeys(permutation_key):
                        pos: int = key.count("/") + 1
                        if not results.get(pos):
                            results[pos] = self.__trie[key].copy()
                        else:
                            results[pos].update(self.__trie[key].copy())
                elif nodes := list(self.__trie.prefixes(permutation_key)):
                    # Now, let's traverse all the possible prefixes.
                    for node in nodes:
                        prefix = node[0]
                        pos: int = prefix.count("/") + 1
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
