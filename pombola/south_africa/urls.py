from django.conf.urls import patterns, include, url

from pombola.south_africa.views import LatLonDetailNationalView, LatLonDetailLocalView, SAPlaceDetailSub, \
    SAOrganisationDetailView, SAPersonDetail, SASearchView, SANewsletterPage, \
    SAPlaceDetailView, SASpeakerRedirectView, SAHansardIndex, SACommitteeIndex, \
    SACommitteeSectionRedirectView, SACommitteeSpeechRedirectView, \
    SAPersonAppearanceView, SAQuestionIndex, SAOrganisationDetailSub
from speeches.views import SectionView, SpeechView, SectionList
from pombola.core.urls import organisation_patterns, person_patterns
from pombola.search.urls import urlpatterns as search_urlpatterns
from pombola.core.views import PlaceKindList

# Override the organisation url so we can vary it depending on the organisation type.
for index, pattern in enumerate(organisation_patterns):
    if pattern.name == 'organisation_people':
        organisation_patterns[index] = url(r'^(?P<slug>[-\w]+)/people/', SAOrganisationDetailSub.as_view(), {'sub_page': 'people'}, 'organisation_people')
    if pattern.name == 'organisation':
        organisation_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAOrganisationDetailView.as_view(), name='organisation')

#add organisation party sub-page
organisation_patterns += patterns(
    'pombola.south_africa.views',
    url(
        '^(?P<slug>[-\w]+)/party/(?P<sub_page_identifier>[-\w]+)/$',  #url regex
        SAOrganisationDetailSub.as_view(),                              #view function
        { 'sub_page': 'party' },                                      #pass in the 'sub_page' arg
        'organisation_party'                                          #url name
    )
)

# Override the person url so we can add some extra data
for index, pattern in enumerate(person_patterns):
    if pattern.name == 'person':
        person_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAPersonDetail.as_view(), name='person')

# Catch /person/{person_slug}/appearances/{speech_tag} urls and serve the
# appropriate content.
urlpatterns = patterns('',

    # FIXME - implement a redirect to /persons/joe-bloggs#appearances when #930
    # done
    # url(r'^person/(?P<person_slug>[-\w]+)/appearances/$', ........ ),

    url(
        r'^person/(?P<person_slug>[-\w]+)/appearances/(?P<speech_tag>[-\w]+)$',
        SAPersonAppearanceView.as_view(),
        name='sa-person-appearance'
    ),
)

for index, pattern in enumerate(search_urlpatterns):
    if pattern.name == 'core_search':
        search_urlpatterns[index] = url(r'^$', SASearchView(), name='core_search')

urlpatterns += patterns('pombola.south_africa.views',
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/national/$', LatLonDetailNationalView.as_view(), name='latlon-national'),
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/$', LatLonDetailLocalView.as_view(), name='latlon'),

    # because the following slug matches override this definition in the core
    # place_patterns, we reinstate it here
    url( r'^place/all/', PlaceKindList.as_view(), name='place_kind_all' ),

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

    # Fake endpoint to redirect
    url(r'^speaker/(?P<pk>\d+)$', SASpeakerRedirectView.as_view(), name='speaker-view'),
)

hansard_patterns = sayit_patterns + patterns('',
    # special Hansard index page that provides listing of the hansard sessions that contain speeches.
    url(r'^$', SAHansardIndex.as_view(), name='section-list'),
)

committee_patterns = patterns('',
    # Exposed endpoints
    url(r'^(?P<pk>\d+)$',        SACommitteeSectionRedirectView.as_view(), name='section-view'),
    url(r'^speech/(?P<pk>\d+)$', SACommitteeSpeechRedirectView.as_view(),  name='speech-view'),

    # Fake endpoint to redirect
    url(r'^speaker/(?P<pk>\d+)$', SASpeakerRedirectView.as_view(), name='speaker-view'),

    url(r'^$', SACommitteeIndex.as_view(), name='section-list'),
)

question_patterns = sayit_patterns + patterns('',
    # special Hansard index page that provides listing of the hansard sessions that contain speeches.
    url(r'^$', SAQuestionIndex.as_view(), name='section-list'),
)

urlpatterns += patterns('',
    url(r'^hansard/',   include(hansard_patterns,   namespace='hansard',   app_name='speeches')),
    url(r'^committee/', include(committee_patterns, namespace='committee', app_name='speeches')),
    url(r'^question/',  include(question_patterns,  namespace='question',  app_name='speeches')),
)
