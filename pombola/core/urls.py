from django.conf import settings
from django.conf.urls import include, url

from django.views.generic import TemplateView, ListView, RedirectView

from pombola.core import models
from pombola.core.views import (HomeView, PlaceDetailView,
    OrganisationList, OrganisationKindList, PlaceKindList, PersonDetail,
    PersonDetailSub, PlaceDetailSub, OrganisationDetailSub,
    SessionListView,
    OrganisationDetailView, HelpApiView,
    featured_person,
    parties,
    memcached_status,
    position_pt,
    position_pt_ok,
    position_pt_ok_o,
    robots,
    VersionView,
    )


person_patterns = [
    url(r'^all/',
        ListView.as_view(model=models.Person),
        name='person_list'),

    url(
        r'^politicians/',
        # This is what I'd like to have - but as the 'position' path does
        # not exist yet it gets confused. Hardcode instead - this end point
        # should be removed at some point - legacy from the MzKe site.
        # 'url': reverse('position', kwargs={'slug':'mp'}),
        RedirectView.as_view(url='/position/mp', permanent=True),
    ),

    # featured person ajax load
    url(r'^featured/((?P<direction>(before|after))/)?(?P<current_slug>[-\w]+)',
        featured_person,
        name='featured_person'),

    url(r'^(?P<slug>[-\w]+)/$', PersonDetail.as_view(), name='person'),
]

for sub_page in ['scorecard', 'comments', 'experience', 'appearances', 'contact_details']:
    person_patterns += (
        url(
            '^(?P<slug>[-\w]+)/%s/$' % sub_page,
            PersonDetailSub.as_view(sub_page=sub_page),
            name='person_%s' % sub_page,
        ),
    )

if settings.ENABLED_FEATURES['bills']:
    person_patterns += (
        url(
            '^(?P<slug>[-\w]+)/bills/',
            PersonDetailSub.as_view(sub_page='bills'),
            name='person_bills',
        ),
    )


place_patterns = [
    url( r'^all/', PlaceKindList.as_view(), name='place_kind_all' ),
    url( r'^is/(?P<slug>[-\w]+)/$', PlaceKindList.as_view(), name='place_kind'     ),
    url( r'^is/(?P<slug>[-\w]+)/(?P<session_slug>[-\w]+)/?', PlaceKindList.as_view(), name='place_kind'     ),

    url(r'^(?P<slug>[-\w]+)/$',
        PlaceDetailView.as_view(),
        name='place'),

    # redirect .../candidates to .../aspirants so that the URL wording matches
    # that on the site. This is to fix originally using the word 'candidates'
    # and can probably be removed at some point when there are no more hits on
    # this path - after July 2013 feels about right.
    url(
        r'^(?P<slug>[-\w]+)/candidates/$',
        RedirectView.as_view(url='/place/%(slug)s/aspirants', permanent=True),
    ),
]

for sub_page in ['aspirants', 'election', 'scorecard', 'comments', 'people', 'places', 'organisations', 'data', 'projects', 'budgets']:
    place_patterns += (
        url(
            '^(?P<slug>[-\w]+)/%s/' % sub_page,
            PlaceDetailSub.as_view(sub_page=sub_page),
            name='place_%s' % sub_page,
        ),
    )


organisation_patterns = [
    url(r'^all/', OrganisationList.as_view(), name='organisation_list'),
    url(r'^is/(?P<slug>[-\w]+)/', OrganisationKindList.as_view(), name='organisation_kind'),
    url(r'^(?P<slug>[-\w]+)/$', OrganisationDetailView.as_view(), name='organisation'),
]

for sub_page in ['comments', 'contact_details', 'people']:
    organisation_patterns += (
        url(
            '^(?P<slug>[-\w]+)/%s/' % sub_page,
            OrganisationDetailSub.as_view(sub_page=sub_page),
            name='organisation_%s' % sub_page,
        ),
    )

organisation_patterns_path = r'^organisation/'
person_patterns_path = r'^person/'
place_patterns_path = r'^place/'

urlpatterns = [
    # Homepage
    url(r'^$', HomeView.as_view(), name='home'),

    url(person_patterns_path, include(person_patterns)),
    url(place_patterns_path, include(place_patterns)),
    url(organisation_patterns_path, include(organisation_patterns)),

    url(r'^position/(?P<pt_slug>[-\w]+)/$', position_pt, name='position_pt'),
    url(r'^position/(?P<pt_slug>[-\w]+)/(?P<ok_slug>[-\w]+)/$', position_pt_ok, name='position_pt_ok'),
    url(r'^position/(?P<pt_slug>[-\w]+)/(?P<ok_slug>[-\w]+)/(?P<o_slug>[-\w]+)/$', position_pt_ok_o, name='position_pt_ok_o'),

    url(r'^sessions$', SessionListView.as_view(), name='sessions'),

    # specials
    url(r'^parties', parties, name='parties'),

    # Ajax select
    url(r'^ajax_select/', include('ajax_select.urls')),
]

urlpatterns += (
    url(r'^status/memcached/', memcached_status, name='memcached_status'),
)

if settings.POPIT_API_URL:
    # Add the dynamically generated API help page
    urlpatterns.append(
        url(r'^help/api', HelpApiView.as_view(), name='help-api')
    )

# Make it easy to see the various error pages without having to fiddle with the
# STAGING settings.
urlpatterns += (
    url(r'^status/down/', TemplateView.as_view(template_name='down.html') ),
    url(r'^status/404/',  TemplateView.as_view(template_name='404.html') ),
    url(r'^status/500/',  TemplateView.as_view(template_name='500.html') ),
)


# We handle the robots here rather than as a static file so that we can send
# different content on a staging server. We don't use direct_to_template as we
# want to set some caching headers too.
urlpatterns += (
    url(r'robots.txt', robots),
)

# A URL for testing jQuery UI components:
urlpatterns += (
    url(r'^ui-test', TemplateView.as_view(template_name='ui-test.html')),
)

urlpatterns += (
    url(r'version.json', VersionView.as_view(), name='version'),
    url(r'template-for-blog.html', TemplateView.as_view(template_name='template-for-blog.html')),
)
