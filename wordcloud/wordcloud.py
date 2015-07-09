import os
from operator import itemgetter
import re

from haystack.query import SearchQuerySet
from pombola.hansard import models as hansard_models


BASEDIR = os.path.dirname(__file__)
# normal english stop words and hansard-centric words to ignore
with open(os.path.join(BASEDIR, 'stopwords.txt'), 'rU') as f:
    STOP_WORDS = set(f.read().splitlines())

def recent_entries(max_entries=20):
    return SearchQuerySet().models(hansard_models.Entry).order_by('-sitting_start_date')[:max_entries]


def popular_words(max_entries=20, max_words=25):
    sqs = recent_entries(max_entries)

    # Generate tag cloud from content of returned entries
    words = {}
    for entry in sqs:
        text = re.sub(ur'[^\w\s]', '', entry.object.content.lower())

        for x in text.split():
            if x not in STOP_WORDS:
                words[x] = 1 + words.get(x, 0)

    wordlist = []

    for word in words:
        wordlist.append(
            {
                "text": word,
                "weight": words.get(word),
                "link": "/search/hansard/?q=%s" % word,
                }
            )

    wordlist.sort(key=itemgetter('weight'), reverse=True)

    return wordlist[:max_words]
