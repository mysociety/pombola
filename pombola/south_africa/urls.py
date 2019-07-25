import copy

from django.conf.urls import include, url
from django.views.generic.base import RedirectView, TemplateView

from pombola.south_africa import views
from pombola.south_africa.views import (SAHomeView, SAMembersView,
    LatLonDetailLocalView, SAPlaceDetailSub, SAOrganisationDetailView,
    SAPersonDetail, SASearchView, SANewsletterPage, SAPlaceDetailView,
    SAPersonAppearanceView,
    SAOrganisationDetailSubPeople, SAOrganisationDetailSubParty,
    SAGeocoderView,
    SAInfoBlogView,
    )
from pombola.core.urls import (
    organisation_patterns,
    organisation_patterns_path,
    person_patterns,
    person_patterns_path,
    place_patterns,
    place_patterns_path,
    )
from pombola.search.urls import urlpatterns as search_urlpatterns
from pombola.writeinpublic.views import WriteToRepresentativeMessages, WriteToCommitteeMessages

organisation_patterns = copy.copy(organisation_patterns)

new_organisation_people_url = url(
    r'^(?P<slug>[-\w]+)/people/',
    SAOrganisationDetailSubPeople.as_view(sub_page='people'),
    name='organisation_people',
    )
new_organisation_url = url(
    r'^(?P<slug>[-\w]+)/$',
    SAOrganisationDetailView.as_view(),
    name='organisation',
    )

for index, pattern in enumerate(organisation_patterns):
    if pattern.name == 'organisation_people':
        organisation_patterns[index] = new_organisation_people_url
    elif pattern.name == 'organisation':
        organisation_patterns[index] = new_organisation_url


# add organisation party sub-page
organisation_patterns.append(
    url(r'^(?P<slug>[-\w]+)/party/(?P<sub_page_identifier>[-\w]+)/$',
        SAOrganisationDetailSubParty.as_view(),
        name='organisation_party',
        )
    )

# Add view for people with names starting with a prefix
organisation_patterns.insert(
    0,
    url(r'^(?P<slug>[-\w]+)/people/(?P<person_prefix>[\w]+)$',
        SAOrganisationDetailSubPeople.as_view(sub_page='people'),
        name='organisation_people_prefix',
        )
    )

person_patterns = copy.copy(person_patterns)

new_person_url = url(
    r'^(?P<slug>[-\w]+)/$',
    SAPersonDetail.as_view(),
    name='person',
    )

new_person_appearances_url = url(
    r'(?P<slug>[-\w]+)/appearances/$',
    RedirectView.as_view(pattern_name='person', permanent=False),
    name='sa-person-appearances')

for index, pattern in enumerate(person_patterns):
    if pattern.name == 'person':
        person_patterns[index] = new_person_url
    elif pattern.name == 'person_appearances':
        person_patterns[index] = new_person_appearances_url


# Catch /person/{person_slug}/appearances/{speech_tag} urls and serve the
# appropriate content.
person_patterns.append((
    # FIXME - implement a redirect to /persons/joe-bloggs#appearances when #930
    # done
    # url(r'^person/(?P<person_slug>[-\w]+)/appearances/$', ........ ),
    url(r'(?P<person_slug>[-\w]+)/appearances/(?P<speech_tag>[-\w]+)$',
        SAPersonAppearanceView.as_view(),
        name='sa-person-appearance')
    ))

# Add View for person meetings attended
person_patterns.append((
    url(r'(?P<person_slug>[-\w]+)/attendances/$',
    views.SAPersonAttendanceView.as_view(),
    name='sa-person-attendance')
    ))

place_patterns = copy.copy(place_patterns)

new_place_url = url(
    r'^(?P<slug>[-\w]+)/$',
    SAPlaceDetailView.as_view(),
    name='place',
    )

new_subplace_url = url(
    r'^(?P<slug>[-\w]+)/places/',
    SAPlaceDetailSub.as_view(sub_page='places'),
    name='place_places',
    )

for index, pattern in enumerate(place_patterns):
    if pattern.name == 'place':
        place_patterns[index] = new_place_url
    elif pattern.name == 'place_places':
        place_patterns[index] = new_subplace_url

place_patterns.extend((
    url(r'^latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/$',
        LatLonDetailLocalView.as_view(),
        name='latlon'),
    ))

urlpatterns = [
    # Include the overriden person, organisation paths
    url(person_patterns_path, include(person_patterns)),
    url(place_patterns_path, include(place_patterns)),
    url(organisation_patterns_path, include(organisation_patterns)),

    # Override the home view:
    url(r'^$', SAHomeView.as_view(), name='home'),

    url(r'^position/member/parliament/?$',
        SAMembersView.as_view(),
        name='sa-members-view')
    ]

# This is for the Code4SA ward councillor widget lookup:
urlpatterns += (
    url(r'^ward-councillor-lookup/$',
        RedirectView.as_view(
            pattern_name='core_geocoder_search',
            permanent=True,
            ),
        name='ward-councillor-lookup'
    ),
)

# MP attendance overview
urlpatterns += (
    url(r'^mp-attendance/$',
        views.SAMpAttendanceView.as_view(),
        name='mp-attendance'
    ),
    url(r'^(mp|minister)-?attendance/?$',
        RedirectView.as_view(
            url='/mp-attendance/',
            permanent=False)
    ),
    url(r'^attendance/?$',
        RedirectView.as_view(
            url='/mp-attendance/',
            permanent=False)
    ),
)

# Routing for election pages
urlpatterns += (
    # Overview pages
    url(r'^election/$',
        RedirectView.as_view(
            pattern_name='sa-election-overview-year',
            permanent=False
        ),
        { 'election_year': 2019 }, name='sa-election-overview'
    ),
    url(
        r'^election/(?P<election_year>[0-9]{4})/$',
        views.SAElectionOverviewView.as_view(),
        name='sa-election-overview-year'
    ),
    url(
        r'^election/(?P<election_year>[0-9]{4})/statistics/$',
        views.SAElectionStatisticsView.as_view(),
        name='sa-election-statistics-year'
    ),
    url(
        r'^election/(?P<election_year>[0-9]{4})/national/$',
        views.SAElectionNationalView.as_view(),
        name='sa-election-overview-national'
    ),
    url(
        r'^election/(?P<election_year>[0-9]{4})/provincial/$',
        views.SAElectionProvincialView.as_view(),
        name='sa-election-overview-provincial'
    ),
    url(
        r'^election/(?P<election_year>[0-9]{4})/national/(party|province)/$',
        RedirectView.as_view(pattern_name='sa-election-overview-national', permanent=True),
    ),

    # National election, party list
    url(
        r'^election/(?P<election_year>[-\w]+)/national/party/(?P<party_name>[-\w]+)/$',
        views.SAElectionPartyCandidatesView.as_view(election_type='national'),
        name='sa-election-candidates-national-party',
    ),

    # National election, provincial list
    url(
        r'^election/(?P<election_year>[-\w]+)/national/province/(?P<province_name>[-\w]+)/$',
        views.SAElectionProvinceCandidatesView.as_view(election_type='national'),
        name='sa-election-candidates-national-province',
    ),

    # National election, party list for a province
    url(
        r'^election/(?P<election_year>[-\w]+)/national/(?P<province_name>[-\w]+)/(?P<party_name>[-\w]+)/$',
        views.SAElectionPartyCandidatesView.as_view(election_type='national'),
        name='sa-election-candidates-national-province-party',
    ),

    # Provincial election, provincial list (ie all candidates in province)
    url(
        r'^election/(?P<election_year>[-\w]+)/provincial/(?P<province_name>[-\w]+)/$',
        views.SAElectionProvinceCandidatesView.as_view(election_type='provincial'),
        name='sa-election-candidates-provincial',
    ),
    # Provincial election, party list
    url(
        r'^election/(?P<election_year>[-\w]+)/provincial/(?P<province_name>[-\w]+)/(?P<party_name>[-\w]+)/$',
        views.SAElectionPartyCandidatesView.as_view(election_type='provincial'),
        name='sa-election-candidates-provincial-party',
    ),
)

for index, pattern in enumerate(search_urlpatterns):
    if pattern.name == 'core_search':
        search_urlpatterns[index] = url(r'^$', SASearchView.as_view(), name='core_search')

urlpatterns += (
    # We want to override the location search view, so that we can
    # redirect straight to the results page if there's a unique result
    # returned.
    url(r'^search/location/$', SAGeocoderView.as_view(), name='core_geocoder_search'),

    # Catch the newsletter info page to change the template used so that the signup form is injected.
    # NOTE - you still need to create an InfoPage with the slug 'newsletter' for this not to 404.
    url(r'^info/newsletter', SANewsletterPage.as_view(), {'slug': 'newsletter'}, name='info_page_newsletter'),
    url(r'^blog/(?P<slug>[\w\-]+)$', SAInfoBlogView.as_view(), name='info_blog'),
)


# Members' interests browser
urlpatterns += (
    url(
        r'^interests/$',
        views.SAMembersInterestsIndex.as_view(),
        name='sa-interests-index'
    ),
    url(
        r'^interests/source/$',
        views.SAMembersInterestsSource.as_view(),
        name='sa-interests-source'
    ),
)

# WriteInPublic
urlpatterns += (
    url(
        r'^committees/$',
        views.SACommitteesView.as_view(),
        name='sa-committees-list'
    ),
    url(
        r'^person/(?P<person_slug>[-\w]+)/messages/$',
        WriteToRepresentativeMessages.as_view(),
        kwargs={'configuration_slug': 'south-africa-assembly'},
        name='sa-person-write-all'
    ),
    url(r'^organisation/(?P<slug>[-\w]+)/messages/$',
        WriteToCommitteeMessages.as_view(),
        kwargs={'configuration_slug': 'south-africa-committees'},
        name='organisation_messages',
    ),
    url(r'^write-committees/', include('pombola.writeinpublic.urls', namespace='writeinpublic-committees', app_name='writeinpublic'), kwargs={'configuration_slug': 'south-africa-committees', 'app_name': 'Write to a committee'}),
    url(r'^write/', include('pombola.writeinpublic.urls', namespace='writeinpublic-mps', app_name='writeinpublic'), kwargs={'configuration_slug': 'south-africa-assembly', 'app_name': 'Write to my MP'}),
)

urlpatterns += (
    url(
        r'^api/committees/popolo.json$',
        views.CommitteesPopoloJson.as_view(),
        name='sa-committees-popolo-json'
    ),
    url(
        r'^api/national-assembly/popolo.json$',
        views.NAMembersPopoloJson.as_view(),
        name='sa-national-assembly-popolo-json'
    ),
)
