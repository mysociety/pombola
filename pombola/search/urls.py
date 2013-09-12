from django.conf.urls import patterns, include, url
from django.conf import settings

from haystack.forms import ModelSearchForm, SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView

from pombola.core    import models as core_models
from pombola.hansard import models as hansard_models

from .views import SearchViewWithGeocoder

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
    # url( r'^location/',    'location_search',        name="location_search"     ),
    url( r'^autocomplete/', 'autocomplete',           name="autocomplete"        ),

    # General search - just intended for the core app
    url(
        r'^$',
        SearchViewWithGeocoder(
            searchqueryset = SearchQuerySet().models( *search_models ).highlight(),
            form_class=SearchForm,
        ),
        name='core_search'
    ),

    # Person search
    url(
        r'^person/$',
        SearchView(
            searchqueryset = SearchQuerySet().models(
                core_models.Person
            ),
            form_class=SearchForm,
        ),
        name='core_person_search'
    ),

    # Place search
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
