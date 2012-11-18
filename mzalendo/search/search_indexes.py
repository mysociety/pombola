from django.conf import settings

from haystack import indexes
from haystack import site
from haystack.exceptions import AlreadyRegistered

from core    import models as core_models


# TODO - currently I'm using the realtime search index - which is possibly a bad
# idea if we get heavy load. Switch to a queue as suggested in the docs:
#
#   http://docs.haystacksearch.org/dev/best_practices.html#use-of-a-queue-for-a-better-user-experience

# TODO - all the search result html could be cached to save db access when
# displaying results: Not done initially as the templates will keep changing
# until the design is stable.
#
#   http://docs.haystacksearch.org/dev/best_practices.html#avoid-hitting-the-database


# Note - these indexes could be specified in the individual apps, which might
# well be cleaner. They are all in one place as I believe there is a good chance
# that they'll be heavily edited when moving to Haystack 2, or some other search
# index abstraction.


class BaseIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)


class PersonIndex(BaseIndex):
    name_auto = indexes.EdgeNgramField(model_attr='name')

class PlaceIndex(BaseIndex):
    name_auto = indexes.EdgeNgramField(model_attr='name')

class OrganisationIndex(BaseIndex):
    name_auto = indexes.EdgeNgramField(model_attr='name')

class PositionTitleIndex(BaseIndex):
    name_auto = indexes.EdgeNgramField(model_attr='name')


try:
    site.register( core_models.Person,        PersonIndex        )
    site.register( core_models.Place,         PlaceIndex         )
    site.register( core_models.Organisation,  OrganisationIndex  )
    site.register( core_models.PositionTitle, PositionTitleIndex )
except AlreadyRegistered:
    # Ignore this error
    pass



if settings.ENABLED_FEATURES['hansard']:
    from hansard import models as hansard_models

    class HansardEntryIndex(BaseIndex):
        sitting_date = indexes.DateTimeField(model_attr='sitting__start_date')

    site.register( hansard_models.Entry, HansardEntryIndex )
