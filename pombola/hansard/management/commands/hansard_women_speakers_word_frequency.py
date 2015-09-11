from collections import defaultdict
from datetime import date
import json
import math
from os.path import dirname, join
import re
from urllib import quote

from django.core.management import BaseCommand

from pombola.hansard.models import Entry

MAX_WORDS = 50

start_date = date(2015, 3, 4)
end_date = date(2015, 6, 30)

WORD_RE = re.compile(r'[\w\']{3,}')
JUST_NUMBERS_RE = re.compile(r'^\d+')

def extract_words(text):
    words_including_numbers = WORD_RE.findall(text)
    return [
        w for w in words_including_numbers if not JUST_NUMBERS_RE.search(w)
    ]


class Command(BaseCommand):

    def handle(self, *args, **options):
        all_words = list()
        word_counts = defaultdict(int)
        for entry in Entry.objects.filter(
                speaker__gender__iexact='female',
                sitting__start_date__gte=start_date,
                sitting__end_date__lte=end_date,
        ):
            for word in extract_words(entry.content):
                word = word.lower()
                if word not in words_to_exclude:
                    word_counts[word] += 1
                all_words.append(word)
        sorted_words = sorted(
            word_counts.items(),
            key=lambda t: t[1],
            reverse=True,
        )
        words_for_json = [
            {
                'text': w,
                'link': '/search/hansard/?q={0}'.format(quote(w)),
                'weight': math.log(c),
            }
            for w, c in sorted_words
        ]
        json_output_filename = join(
            dirname(__file__), '..', '..', '..',
            'kenya', 'static', 'js', 'women-hansard-words.js'
        )
        with open(json_output_filename, 'w') as f:
            f.write('var womenHansardWords = ')
            json.dump(words_for_json[:MAX_WORDS], f, indent=4, sort_keys=True)
        for word, count in sorted_words[:MAX_WORDS*4]:
            print count, word


words_to_exclude = set([
    "the",
    "to",
    "of",
    "with",
    "were",
    "has",
    "that",
    "and",
    "is",
    "i",
    "we",
    "a",
    "in",
    "this",
    "are",
    "it",
    "have",
    "for",
    "not",
    "be",
    "on",
    "you",
    "will",
    "they",
    "from",
    "so",
    "can",
    "was",
    "do",
    "there",
    "who",
    "because",
    "at",
    "our",
    "want",
    "been",
    "very",
    "what",
    "if",
    "also",
    "when",
    "he",
    "would",
    "or",
    "but",
    "which",
    "us",
    "should",
    "all",
    "one",
    "am",
    "their",
    "them",
    "an",
    "about",
    "those",
    "my",
    "like",
    "know",
    "other",
    "need",
    "even",
    "these",
    "where",
    "no",
    "only",
    "me",
    "had",
    "just",
    "up",
    "some",
    "many",
    "out",
    "now",
    "must",
    "any",
    "come",
    "therefore",
    "then",
    "more",
    "get",
    "take",
    "look",
    "how",
    "could",
    "cannot",
    "why",
    "here",
    "way",
    "na",
    "your",
    "make",
    "before",
    "into",
    "two",
    "through",
    "see",
    "his",
    "done",
    "let",
    "lot",
    "however",
    "whether",
    "under",
    "put",
    "may",
    "did",
    "new",
    "kwa",
    "same",
    "ya",
    "first",
    "really",
    "after",
    "does",
    "much",
    "doing",
    "years",
    "such",
    "him",
    "she",
    "well",
    "its",
    "shall",
    "most",
    "within",
    "than",
    "every",
    "per",
    "over",
    "back",
    "made",
    "already",
    "purposesonly",
    "still",
    "sure",
    "next",
    "find",
    "three",
    "use",
    "something",
    "day",
    "without",
    "another",
    "used",
    "few",
    "tell",
    "long",
    "own",
    "since",
    "her",
    "asked",
    "further",
    "during",
    "yet",
    "yes",
    "against",
    "each",
    "start",
    "coming",
    "enough",
    "while",
    "whole",
    "once",
    "between",
    "indeed",
    "sub",
    "down",
    "high",
    "hii",
    "sector",
    "never",
    "came",
    "comes",
    "both",
    "until",
    "five",
    "went",
    "sometimes",
    "forward",
    "call",
    "left",
    "various",
    "better",
    "upon",
    "called",
    "always",
    "ourselves",
    "four",
    "become",
    "away",
    "somebody",
    "ones",
    "too",
    "themselves",
    "got",
    "things",
])
