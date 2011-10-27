import datetime
from haystack import indexes
from haystack import site
from core import models


# TODO - currently I'm using the realtime search index - which is possibly a bad
# idea if we get heavy load. Switch to a queue as suggested in the docs:
#
#   http://docs.haystacksearch.org/dev/best_practices.html#use-of-a-queue-for-a-better-user-experience

# TODO - all the search result html could be cached to save db access when
# displaying results: Not done initially as the templates will keep changing
# until the design is stable.
#
#   http://docs.haystacksearch.org/dev/best_practices.html#avoid-hitting-the-database


class PersonIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

class PlaceIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

class OrganisationIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

class PositionTitleIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)


site.register( models.Person,        PersonIndex        )
site.register( models.Place,         PlaceIndex         )
site.register( models.Organisation,  OrganisationIndex  )
site.register( models.PositionTitle, PositionTitleIndex )
