from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('search.views',

    # Haystack and other searches
    url( r'^location/',    'location_search',        name="location_search"     ),
    url( r'^autocomplete', 'autocomplete',           name="autocomplete"        ),
    url( r'^',             include('haystack.urls'), name="default_search_page" ),

)