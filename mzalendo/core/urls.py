from django.conf.urls.defaults import patterns, include, url

from django.views.generic import DetailView, ListView
from django.views.generic.simple import direct_to_template, redirect_to

from core import models
from core.views import PlaceDetailView

person_patterns = patterns('core.views',
    url(r'^all/',
        ListView.as_view(model=models.Person),
        name='person_list'),

    url(
        r'^politicians/',
        redirect_to,
        {
            # This is what I'd like to have - but as the 'position' path does
            # not exist yet it gets confused. Hardcode instead - this end point
            # should be removed at some point - legacy from the MzKe site.
            # 'url': reverse('position', kwargs={'slug':'mp'}),
            'url': '/position/mp',
            'permanent': True,
        }
    ),
                           
    # featured person ajax load
    url(r'^featured/((?P<direction>(before|after))/)?(?P<current_slug>[-\w]+)',
        'featured_person', 
        name='featured_person'),
    
    url(r'^(?P<slug>[-\w]+)/',       'person',       name='person'),
  )

place_patterns = patterns('core.views',

    url( r'^all/',                 'place_kind', name='place_kind_all' ),
    url( r'^is/(?P<slug>[-\w]+)/', 'place_kind', name='place_kind'     ),
    url( r'^mapit_area/(?P<mapit_id>\d+)/', 'place_mapit_area', name='place_mapit_area' ),

    url(r'^(?P<slug>[-\w]+)/$',
        PlaceDetailView.as_view(),      
        name='place'),
                          
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

