from django.conf import settings

from haystack import indexes

from pombola.core import models as core_models

# TODO - currently this uses the realtime search index - which is possibly a bad
# idea if the site gets heavy load. Switch to a queue as suggested in the docs:
#   http://docs.haystacksearch.org/dev/best_practices.html#use-of-a-queue-for-a-better-user-experience

# TODO - all the search result html could be cached to save db access when
# displaying results: Not done initially as the templates will keep changing
# until the design is stable.
#   http://docs.haystacksearch.org/dev/best_practices.html#avoid-hitting-the-database

# Note - these indexes could be specified in the individual apps, which might
# well be cleaner.

class BaseIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)

class PersonIndex(BaseIndex, indexes.Indexable):
    name_auto = indexes.EdgeNgramField(model_attr='name')
    hidden = indexes.BooleanField(model_attr='hidden')

    def get_model(self):
        return core_models.Person

class PlaceIndex(BaseIndex, indexes.Indexable):
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return core_models.Place

class OrganisationIndex(BaseIndex, indexes.Indexable):
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return core_models.Organisation

class PositionTitleIndex(BaseIndex, indexes.Indexable):
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return core_models.PositionTitle

if settings.ENABLED_FEATURES['hansard']:
    from pombola.hansard import models as hansard_models

    class HansardEntryIndex(BaseIndex, indexes.Indexable):
        start_date = indexes.DateTimeField(null=True)

        def get_model(self):
            return hansard_models.Entry

        def index_queryset(self, using=None):
            """Used when the entire index for model is updated."""
            return self.get_model().objects.select_related('sitting')

        def prepare_start_date(self, obj):
            return obj.sitting.start_date

if 'pombola.info' in settings.INSTALLED_APPS:
    from pombola.info.models import InfoPage

    class InfoPageIndex(BaseIndex, indexes.Indexable):
        kind = indexes.CharField(model_attr='kind')

        def get_model(self):
            return InfoPage
