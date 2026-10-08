from unittest.mock import patch

from django.test import SimpleTestCase

from api.utils import (
    SEARCH_PREDEFINED_LINKS,
    get_country_specific_search_urls,
    get_predefined_search_urls,
)


class SearchPredefinedLinksTestCase(SimpleTestCase):
    def test_lookup_is_case_and_whitespace_insensitive(self):
        expressions, url, name = SEARCH_PREDEFINED_LINKS[0]
        phrase = next(iter(expressions))
        # A phrase may legitimately match more than one group, so just assert this group's entry is among the results.
        self.assertIn({"url": url, "name": name}, get_predefined_search_urls(f"  {phrase.upper()}  "))

    def test_unknown_phrase_returns_empty_list(self):
        self.assertEqual(get_predefined_search_urls("this phrase does not exist anywhere"), [])

    def test_phrase_matching_multiple_groups_returns_all_their_urls(self):
        phrase = "some-test-only-phrase-xyz"
        extra_links = SEARCH_PREDEFINED_LINKS + [({phrase}, "/first", "First"), ({phrase}, "/second", "Second")]
        matches = [{"url": url, "name": name} for expressions, url, name in extra_links if phrase in expressions]
        self.assertEqual(matches, [{"url": "/first", "name": "First"}, {"url": "/second", "name": "Second"}])


class CountrySpecificSearchLinksTestCase(SimpleTestCase):
    def setUp(self):
        patcher = patch("api.utils._get_country_name_to_id_map", return_value={"angola": 18, "niger": 1, "nigeria": 2})
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_country_prefix_matches_category(self):
        self.assertEqual(
            get_country_specific_search_urls("Angola emergencies"),
            [{"url": "/countries/18/ongoing-activities/emergencies", "name": "Ongoing Emergencies"}],
        )

    def test_country_suffix_matches_category(self):
        self.assertEqual(
            get_country_specific_search_urls("movement partners Angola"),
            [{"url": "/countries/18/ns-overview/partners", "name": "Partners"}],
        )

    def test_longer_country_name_is_not_shadowed_by_shorter_one(self):
        self.assertEqual(
            get_country_specific_search_urls("Nigeria profile"),
            [{"url": "/countries/2/profile/overview", "name": "Country Profile"}],
        )
        self.assertEqual(
            get_country_specific_search_urls("Niger profile"),
            [{"url": "/countries/1/profile/overview", "name": "Country Profile"}],
        )

    def test_unknown_category_returns_empty_list(self):
        self.assertEqual(get_country_specific_search_urls("Angola xyz"), [])

    def test_unknown_country_returns_empty_list(self):
        self.assertEqual(get_country_specific_search_urls("Wakanda emergencies"), [])
