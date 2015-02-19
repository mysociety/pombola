from django.conf.urls import patterns, include, url
from django.conf import settings

from pombola.core    import models as core_models

from .views import SearchBaseView, GeocoderView, HansardSearchView

urlpatterns = patterns('pombola.search.views',

    # Haystack and other searches
    url( r'^autocomplete/', 'autocomplete',           name="autocomplete"        ),

    url(r'^$',
        SearchBaseView.as_view(),
        name='core_search'),

    # Location search
    url(
        r'^location/$',
        GeocoderView.as_view(),
        name='core_geocoder_search'
    ),

)

# Hansard search - only loaded if hansard is enabled
if settings.ENABLED_FEATURES['hansard']:
    from pombola.hansard import models as hansard_models
    urlpatterns += patterns('pombola.search.views',
        url(
            r'^hansard/$',
            HansardSearchView.as_view(),
            name='hansard_search',
        ),
    )
