from django.conf.urls import patterns, include, url

from pombola.south_africa.views import LatLonDetailView, SAPlaceDetailSub, \
    SAOrganisationDetailView, SAPersonDetail, SANewsletterPage, SAHansardIndex
from pombola.core.urls import organisation_patterns, person_patterns

# Override the organisation url so we can vary it depending on the organisation type.
for index, pattern in enumerate(organisation_patterns):
    if pattern.name == 'organisation':
        organisation_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAOrganisationDetailView.as_view(), name='organisation')

# Override the person url so we can add some extra data
for index, pattern in enumerate(person_patterns):
    if pattern.name == 'person':
        person_patterns[index] = url(r'^(?P<slug>[-\w]+)/$', SAPersonDetail.as_view(), name='person')

urlpatterns = patterns('pombola.south_africa.views',
    url(r'^place/latlon/(?P<lat>[0-9\.-]+),(?P<lon>[0-9\.-]+)/', LatLonDetailView.as_view(), name='latlon'),
    url(r'^place/(?P<slug>[-\w]+)/places/', SAPlaceDetailSub.as_view(), {'sub_page': 'places'}, name='place_places'),

    # Catch the newsletter info page to change the template used so that the signup form is injected.
    # NOTE - you still need to create an InfoPage with the slug 'newsletter' for this not to 404.
    url(r'^info/newsletter', SANewsletterPage.as_view(), {'slug': 'newsletter'}, name='info_page_newsletter'),

    # Create a special Hansard index page that provides listing of the hansard sessions that contain speeches.
    url(r'^hansard/$', SAHansardIndex.as_view(), name='za_hansard_index'),
)
