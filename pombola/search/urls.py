from django.conf.urls import url
from django.conf import settings

from .views import (
    autocomplete,
    GeocoderView,
    SearchBaseView,
    )


urlpatterns = [
    # Haystack and other searches
    url(r'^autocomplete/', autocomplete, name="autocomplete"),

    url(r'^$',
        SearchBaseView.as_view(),
        name='core_search'),

    # Location search
    url(
        r'^location/$',
        GeocoderView.as_view(),
        name='core_geocoder_search'
    ),
]

# Hansard search - only loaded if hansard is enabled
if settings.ENABLED_FEATURES['hansard']:
    from .views import HansardSearchView
    urlpatterns.append(
        url(
            r'^hansard/$',
            HansardSearchView.as_view(),
            name='hansard_search',
            )
        )
