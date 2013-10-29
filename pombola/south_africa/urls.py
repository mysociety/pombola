from django.conf.urls import patterns, include, url

from pombola.south_africa.views import LatLonDetailView, SAPlaceDetailSub, \
    SAOrganisationDetailView, SAPersonDetail, SASearchView, SANewsletterPage, \
    SAPlaceDetailView, SASpeakerRedirectView, SAHansardIndex
from speeches.views import SectionView, SpeechView, SectionList
from pombola.core.urls import organisation_patterns, person_patterns
from pombola.search.urls import urlpatterns as search_urlpatterns

# Override the organisation url so we can vary it depending on the organisation type.
for index, pattern in enumerate(organisation_patterns):
    if pattern.name == 'organisation':
        organisation_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAOrganisationDetailView.as_view(), name='organisation')

# Override the person url so we can add some extra data
for index, pattern in enumerate(person_patterns):
    if pattern.name == 'person':
        person_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAPersonDetail.as_view(), name='person')

for index, pattern in enumerate(search_urlpatterns):
    if pattern.name == 'core_search':
        search_urlpatterns[index] = url(r'^$', SASearchView(), name='core_search')

urlpatterns = patterns('pombola.south_africa.views',
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', LatLonDetailView.as_view(), name='latlon'),
    url(r'^place/(?P<slug>[-\w]+)/$', SAPlaceDetailView.as_view(), name='place'),

    url(r'^place/(?P<slug>[-\w]+)/places/', SAPlaceDetailSub.as_view(), {'sub_page': 'places'}, name='place_places'),

    # Catch the newsletter info page to change the template used so that the signup form is injected.
    # NOTE - you still need to create an InfoPage with the slug 'newsletter' for this not to 404.
    url(r'^info/newsletter', SANewsletterPage.as_view(), {'slug': 'newsletter'}, name='info_page_newsletter'),
)

sayit_patterns = patterns('',

    # Exposed endpoints
    url(r'^(?P<pk>\d+)$',        SectionView.as_view(), name='section-view'),
    url(r'^speech/(?P<pk>\d+)$', SpeechView.as_view(),  name='speech-view'),

    # special Hansard index page that provides listing of the hansard sessions that contain speeches.
    url(r'^$', SAHansardIndex.as_view(), name='section-list'),

    # Fake endpoint to redirect
    url(r'^speaker/(?P<pk>\d+)$', SASpeakerRedirectView.as_view(), name='speaker-view'),
)
urlpatterns += patterns('',
    url(r'^hansard/', include(sayit_patterns, namespace='hansard', app_name='speeches')),
)
