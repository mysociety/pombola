# coding=UTF-8
from mock import patch, Mock

from django.test import TestCase

from wordcloud.wordcloud import popular_words


def debug_print():
    print 'DEBUGGING'


@patch('wordcloud.wordcloud.recent_entries')
class TestPopularWords(TestCase):
    def make_entries(self, recent_entries, text_entries):
        recent_entries.return_value = [
            Mock(**{'object.content': x}) for x in text_entries
            ]

    def test_popular_words_punctuation(self, recent_entries):
        text_entries = [
            'Testing! Testing!',
            'Testing again.',
            ]

        self.make_entries(recent_entries, text_entries)

        self.assertEqual(
            [{'text': 'testing', 'link': '/search/hansard/?q=testing', 'weight': 3}],
            popular_words(),
            )

    def test_popular_words(self, recent_entries):
        text_entries = [
            'As well as issuing 107 formal notices to underperforming academies, '
            'we have intervened and changed the sponsor in 75 cases of particular '
            'concern. The results of such intervention are evident.',
            'I am interested in what the right hon. Lady has to say about failing '
            'academies because, as she will know, the regional schools commissioner '
            'is involved in one academy in my constituency that Ofsted judges to '
            'be inadequate.',
            ]

        self.make_entries(recent_entries, text_entries)

        words = popular_words()

        expected = [
            {'text': 'academies', 'link': '/search/hansard/?q=academies', 'weight': 2},
            {'text': 'changed', 'link': '/search/hansard/?q=changed', 'weight': 1},
            {'text': 'underperforming', 'link': '/search/hansard/?q=underperforming', 'weight': 1},
            {'text': 'inadequate', 'link': '/search/hansard/?q=inadequate', 'weight': 1},
            {'text': 'sponsor', 'link': '/search/hansard/?q=sponsor', 'weight': 1},
            {'text': 'intervention', 'link': '/search/hansard/?q=intervention', 'weight': 1},
            {'text': 'judges', 'link': '/search/hansard/?q=judges', 'weight': 1},
            {'text': 'ofsted', 'link': '/search/hansard/?q=ofsted', 'weight': 1},
            {'text': '107', 'link': '/search/hansard/?q=107', 'weight': 1},
            {'text': 'interested', 'link': '/search/hansard/?q=interested', 'weight': 1},
            {'text': 'notices', 'link': '/search/hansard/?q=notices', 'weight': 1},
            {'text': 'concern', 'link': '/search/hansard/?q=concern', 'weight': 1},
            {'text': 'commissioner', 'link': '/search/hansard/?q=commissioner', 'weight': 1},
            {'text': 'intervened', 'link': '/search/hansard/?q=intervened', 'weight': 1},
            {'text': 'academy', 'link': '/search/hansard/?q=academy', 'weight': 1},
            {'text': 'regional', 'link': '/search/hansard/?q=regional', 'weight': 1},
            {'text': '75', 'link': '/search/hansard/?q=75', 'weight': 1},
            {'text': 'schools', 'link': '/search/hansard/?q=schools', 'weight': 1},
            {'text': 'cases', 'link': '/search/hansard/?q=cases', 'weight': 1},
            {'text': 'lady', 'link': '/search/hansard/?q=lady', 'weight': 1},
            {'text': 'issuing', 'link': '/search/hansard/?q=issuing', 'weight': 1},
            {'text': 'formal', 'link': '/search/hansard/?q=formal', 'weight': 1},
            {'text': 'evident', 'link': '/search/hansard/?q=evident', 'weight': 1},
            {'text': 'involved', 'link': '/search/hansard/?q=involved', 'weight': 1},
            {'text': 'failing', 'link': '/search/hansard/?q=failing', 'weight': 1},
            ]

        # I guess this is slightly fragile and relies on the ordering being preserved.
        self.assertEqual(words, expected)
