from haystack import indexes

from speeches.models import Speech

from pombola.search import search_indexes

class SAPlaceIndex(search_indexes.PlaceIndex):

    def index_queryset(self, **kwargs):
        return self.get_model().objects. \
            exclude(kind__slug__in=('constituency-office', 'wards'))

# We use our own index of speeches in SayIt since we want to add tags
# to it.  The SayIt one is excluded via EXCLUDED_INDEXES.  (For some
# reason if you subclass speeches.search_indexes.SpeechIndex,
# excluding the former via EXCLUDED_INDEXES doesn't work.)

class SASpeechIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='text')
    title = indexes.CharField() # use_template=True)
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    instance = indexes.CharField(model_attr='instance__label')
    speaker = indexes.IntegerField(model_attr='speaker__id', null=True)
    tags = indexes.CharField()

    def get_model(self):
        return Speech

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects # .filter(pub_date__lte=datetime.datetime.now())

    def get_updated_field(self):
        return 'modified'

    def prepare_tags(self, obj):
        return ' '.join(t.name for t in obj.tags.all())
