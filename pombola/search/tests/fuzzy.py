# coding=utf-8

from django.test import TestCase

from haystack.inputs import Raw

from pombola.search.views import SearchBaseView


class FuzzyQueryStringTest(TestCase):

    def test_alphanumeric_string_fuzzed(self):

        query_string = 'foo bar baz'

        expected_string = 'foo~1 bar~1 baz~1'

        search = SearchBaseView()

        self.assertEqual(
            str(search.generate_fuzzy_query_object(query_string)),
            expected_string
        )

    def test_complex_string_unfuzzed(self):

        query_string = 'fü bár bâz'

        expected_string = 'fü bár bâz'

        search = SearchBaseView()

        self.assertEqual(
            str(search.generate_fuzzy_query_object(query_string)),
            expected_string
        )
