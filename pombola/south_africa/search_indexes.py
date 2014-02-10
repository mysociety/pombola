from pombola.search import search_indexes

class SAPlaceIndex(search_indexes.PlaceIndex):

    def index_queryset(self, **kwargs):
        return self.get_model().objects. \
            exclude(kind__slug__in=('constituency-office', 'wards'))
