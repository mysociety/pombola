from django.conf.urls import patterns, include, url
from django.conf import settings

from haystack.forms import ModelSearchForm, SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView

from pombola.core    import models as core_models

from .views import (SearchGlobalView, SearchSectionView,
   GeocoderView)

search_models = (
    core_models.Person,
    core_models.Organisation,
    core_models.Place,
    core_models.PositionTitle
)
if settings.ENABLED_FEATURES['speeches']:
    from speeches.models import Speech
    search_models += ( Speech, )

urlpatterns = patterns('pombola.search.views',

    # Haystack and other searches
    url( r'^autocomplete/', 'autocomplete',           name="autocomplete"        ),

    url(r'^$',
        SearchGlobalView.as_view(form_class=SearchForm),
        name='core_search'),
    url(r'^section/$',
        SearchSectionView.as_view(form_class=SearchForm),
        name='core_search_section'),

    # Location search
    url(
        r'^location/$',
        GeocoderView.as_view(),
        name='core_geocoder_search'
    ),

    # Person search - this is only used in the Kenyan 2013
    # election-themed homepage
    url(
        r'^person/$',
        SearchView(
            searchqueryset = SearchQuerySet().models(
                core_models.Person
            ).exclude(hidden=True),
            form_class=SearchForm,
        ),
        name='core_person_search'
    ),

    # Place search - this is only used in the Kenyan 2013
    # election-themed homepage
    url(
        r'^place/$',
        SearchView(
            searchqueryset = SearchQuerySet().models(
                core_models.Place,
            ),
            form_class=SearchForm,
        ),
        name='core_place_search'
    ),
)


# Hansard search - only loaded if hansard is enabled
if settings.ENABLED_FEATURES['hansard']:
    from pombola.hansard import models as hansard_models
    urlpatterns += patterns('pombola.search.views',
        url(
            r'^hansard/$',
            SearchView(
                searchqueryset = SearchQuerySet().models(
                    hansard_models.Entry,
                ),
                form_class=SearchForm,
                template="search/hansard.html",
            ),
            name='hansard_search',
        ),
    )
