import collections

from django.test import SimpleTestCase

from api.utils import SEARCH_PREDEFINED_LINKS, get_predefined_search_url


class SearchPredefinedLinksTestCase(SimpleTestCase):
    def test_no_duplicate_phrases_across_groups(self):
        """Each phrase must map to exactly one URL, otherwise the match is order-dependent"""
        owners = collections.defaultdict(set)
        for expressions, url in SEARCH_PREDEFINED_LINKS:
            for expression in expressions:
                owners[expression].add(url)

        conflicts = {phrase: urls for phrase, urls in owners.items() if len(urls) > 1}
        self.assertEqual(conflicts, {}, f"Phrases mapped to more than one URL: {conflicts}")

    def test_lookup_is_case_and_whitespace_insensitive(self):
        expressions, url = SEARCH_PREDEFINED_LINKS[0]
        phrase = next(iter(expressions))
        self.assertEqual(get_predefined_search_url(f"  {phrase.upper()}  "), url)

    def test_unknown_phrase_returns_none(self):
        self.assertIsNone(get_predefined_search_url("this phrase does not exist anywhere"))
