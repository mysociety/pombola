from django.conf.urls.defaults import patterns, include, url

from django.views.generic import DetailView, ListView
from django.views.generic.simple import direct_to_template

from core import models
from core.views import PlaceListView

person_patterns = patterns('core.views',
    url(r'^all/',
        ListView.as_view(model=models.Person),
        name='person_list'),
    url(r'^politicians/',
        ListView.as_view(queryset=models.Position.objects.all().current_mp_positions().order_by('place__slug')),
        name='politician_list'),
                           
    # featured person ajax load
    url(r'^featured/(?P<direction>(before|after))/(?P<current_slug>[-\w]+)',
        'featured_person', 
        name='featured_person'),
    
    url(r'^(?P<slug>[-\w]+)/',       'person',       name='person'),
  )

place_patterns = patterns('core.views',
    url(r'^all/',
        PlaceListView.as_view(queryset=models.Place.objects.all()),
        name='place_list'),
    url(r'^constituencies/',
        PlaceListView.as_view(queryset=models.Place.objects.all().constituencies(), context_object_name='constituencies'),
        name='constituency_list'),
    url(r'^counties/',
        PlaceListView.as_view(queryset=models.Place.objects.all().counties(), context_object_name='counties'),    
        name='county_list'),

    url(r'^is/(?P<slug>[-\w]+)/', 'place_kind', name='place_kind'),
    url(r'^(?P<slug>[-\w]+)/$',   'place',      name='place'),

    # Tab content
    url(
        r'^(?P<slug>[-\w]+)/related_person_tab', 
        DetailView.as_view(
            model=models.Place,
            template_name_suffix='_related_person_tab',
        ),
        name="place_related_person_tab",        
    ),
    url(
        r'^(?P<slug>[-\w]+)/related_organisation_tab', 
        DetailView.as_view(
            model=models.Place,
            template_name_suffix='_related_organisation_tab',
        ),
        name="place_related_organisation_tab",        
    ),
                          )

organisation_patterns = patterns('core.views',
    url(r'^all/', 'organisation_list', name='organisation_list'),

    # Tab content
    url(
        r'^(?P<slug>[-\w]+)/related_person_tab', 
        DetailView.as_view(
            model=models.Organisation,
            template_name_suffix='_related_person_tab',
        ),
        name="organisation_related_person_tab",        
    ),

    url(r'^is/(?P<slug>[-\w]+)/', 'organisation_kind', name='organisation_kind'),
    url(r'^(?P<slug>[-\w]+)/$',   'organisation',      name='organisation'),
    
                                 )

urlpatterns = patterns('core.views',
    # Homepage
    url(r'^$', 'home', name='home'),

    (r'^person/', include(person_patterns)),
    (r'^place/', include(place_patterns)),
    (r'^organisation/', include(organisation_patterns)),

    url(r'^position/(?P<slug>[-\w]+)/',     'position',     name='position'),

    # specials
    url(r'^parties', 'parties', name='parties'),

    # Ajax select
    url(r'^ajax_select/', include('ajax_select.urls')),
)

urlpatterns += patterns('core.views',
    url(r'^external_feeds/twitter/', 'twitter_feed',     name='twitter_feed'),
    url(r'^status/memcached/',       'memcached_status', name='memcached_status'),
)

urlpatterns += patterns('',
    url(r'^status/down/', direct_to_template, {'template': 'down.html'} ),
)

