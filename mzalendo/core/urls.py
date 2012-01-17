from django.conf.urls.defaults import patterns, include, url

from django.views.generic import DetailView

from core import models

urlpatterns = patterns('core.views',
    # Homepage
    url(r'^$', 'home', name='home'),

    # Lists
    url(r'^person/all/',       'person_list',       name='person_list'),
    url(r'^place/all/',        'place_list',        name='place_list'),
    url(r'^organisation/all/', 'organisation_list', name='organisation_list'),
    
    # Objects
    url(r'^person/(?P<slug>[-\w]+)/',       'person',       name='person'),
    url(r'^position/(?P<slug>[-\w]+)/',     'position',     name='position'),

    url(r'^place/is/(?P<slug>[-\w]+)/', 'place_kind', name='place_kind'),
    url(r'^place/(?P<slug>[-\w]+)/$',   'place',      name='place'),

    url(r'^organisation/is/(?P<slug>[-\w]+)/', 'organisation_kind', name='organisation_kind'),
    url(r'^organisation/(?P<slug>[-\w]+)/', 'organisation', name='organisation'),

    # Tab content
    url(
        r'^place/(?P<slug>[-\w]+)/related_person_tab', 
        DetailView.as_view(
            model=models.Place,
            template_name_suffix='_related_person_tab',
        ),
        name="place_related_person_tab",        
    ),
    url(
        r'^place/(?P<slug>[-\w]+)/related_organisation_tab', 
        DetailView.as_view(
            model=models.Place,
            template_name_suffix='_related_organisation_tab',
        ),
        name="place_related_organisation_tab",        
    ),

    # specials
    url(r'^parties', 'parties', name='parties'),

    # Ajax select
    url(r'^ajax_select/', include('ajax_select.urls')),
)