from django.conf.urls.defaults import patterns, include, url

from haystack.forms import ModelSearchForm, SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView

from mzalendo.core    import models as core_models
from mzalendo.hansard import models as hansard_models

urlpatterns = patterns('search.views',

    # Haystack and other searches
    url( r'^location/',    'location_search',        name="location_search"     ),
    url( r'^autocomplete/', 'autocomplete',           name="autocomplete"        ),

    # General search - just intended for the core app
    url(
        r'^$',
        SearchView(
            searchqueryset = SearchQuerySet().models(
                core_models.Person,
                core_models.Organisation,
                core_models.Place,
                core_models.PositionTitle
            ),
            form_class=SearchForm,            
        ),
        name='core_search'
    ),

    # Hansard search
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
