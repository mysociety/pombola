import os
from operator import itemgetter

from haystack.query import SearchQuerySet
from pombola.hansard import models as hansard_models


BASEDIR = os.path.dirname(__file__)
# normal english stop words and hansard-centric words to ignore
STOP_WORDS = open(os.path.join(BASEDIR, 'stopwords.txt'), 'rU').read().splitlines()


def popular_words(max_entries=20):
    sqs = SearchQuerySet().models(hansard_models.Entry).order_by('-sitting_start_date')

    cloudlist = []

    try:
        # Generate tag cloud from content of returned entries
        words = {}
        for entry in sqs[:max_entries]:
            text = entry.object.content

            for x in text.lower().split():
                cleanx = x.replace(',', '').replace('.', '').replace('"', '').strip()
                if cleanx not in STOP_WORDS:  # and not cleanx in hansard_words:
                    words[cleanx] = 1 + words.get(cleanx, 0)

        for word in words:
            cloudlist.append(
                {
                    "text": word,
                    "weight": words.get(word),
                    "link": "/search/hansard/?q=%s" % word,
                    }
                )

        sortedlist = sorted(cloudlist, key=itemgetter('weight'), reverse=True)[:25]
    except:
        sortedlist = []

    return sortedlist
