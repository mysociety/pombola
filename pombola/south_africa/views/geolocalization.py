import mapit
import requests

from .constants import API_REQUESTS_TIMEOUT

from django import forms
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.utils.http import urlquote

from haystack.forms import SearchForm

from pombola.core import models
from pombola.core.views import (
    BasePlaceDetailView, PlaceDetailView, PlaceDetailSub)
from pombola.search.views import GeocoderView

from pombola.south_africa.models import ZAPlace

# In the short term, until we have a list of constituency offices and
# addresses from DA, let's bundle these together.
CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS = (
    'constituency-office',
    'constituency-area',  # specific to DA party
)


class WardCouncillorAPIDown(Exception):
    pass


class SAGeocoderView(GeocoderView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        results = context.get('geocoder_results')
        if results is not None and len(results) == 1:
            result = results[0]
            redirect_url = reverse('latlon', kwargs={
                'lat': result['latitude'],
                'lon': result['longitude']})
            redirect_url += '?q=' + urlquote(request.GET['q'])
            return redirect(redirect_url)
        else:
            return self.render_to_response(context)


class LocationSearchForm(SearchForm):
    q = forms.CharField(
        required=False,
        label=('Search'),
        widget=forms.TextInput(attrs={'placeholder': 'Your address'}))


class LatLonDetailBaseView(BasePlaceDetailView):
    # Using 25km as the default, as that's what's used on MyReps.
    constituency_office_search_radius = 25

    # The codes used here should match the party slugs, and the names of the
    # icon files in .../static/images/party-map-icons/
    party_slugs_that_have_logos = set((
        'adcp', 'anc', 'apc', 'azapo', 'cope', 'da', 'ff', 'id', 'ifp', 'mf',
        'pac', 'sacp', 'ucdp', 'udm', 'agang', 'aic', 'eff'
    ))

    def get_object(self):
        # FIXME - handle bad args better.
        lat = float(self.kwargs['lat'])
        lon = float(self.kwargs['lon'])

        self.location = Point(lon, lat)

        areas = mapit.models.Area.objects.by_location(self.location)

        try:
            # FIXME - Handle getting more than one province.
            province = models.Place.objects.get(mapit_area__in=areas, kind__slug='province')
        except models.Place.DoesNotExist:
            raise Http404

        return province

    def get_ward_councillors(self, location):
        # Look up the ward on MapIt:
        url = 'http://mapit.code4sa.org/point/4326/{lon},{lat}?type=WD,MN'.format(
            lon=location.x, lat=location.y
        )

        try:
            r = requests.get(url, timeout=API_REQUESTS_TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise WardCouncillorAPIDown(u"MapIt request failed: {0}".format(e))

        mapit_json = r.json()
        if not mapit_json:
            return []
        ward = None
        muni = None
        for item in mapit_json.values():
            if item['type_name'] == 'Ward':
                ward = item
            elif item['type_name'] == 'Municipality':
                muni = item
        ward_id = ward['codes']['MDB']
        muni_id = muni['codes']['MDB']

        # Then find the ward councillor from that ward ID. There
        # should only be one at the moment, but make it a list in case
        # we support broader lookups in the future:
        url_fmt = 'http://nearby.code4sa.org/councillor/ward-{ward_id}.json'
        try:
            r = requests.get(
                url_fmt.format(ward_id=ward_id),
                timeout=API_REQUESTS_TIMEOUT)
            r.raise_for_status()
            ward_result = r.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            raise WardCouncillorAPIDown(unicode(e))
        councillor_data = ward_result['councillor']

        party = models.Organisation.objects.filter(
            name__icontains=councillor_data['PartyDetail']['Name'].lower(),
            kind__slug='party'
        ).first()
        has_party_logo = party and (party.slug in self.party_slugs_that_have_logos)

        return [
            {
                'name': councillor_data['Name'],
                'person': None,
                'email': councillor_data['custom_contact_details'].get('email', ''),
                'phone': councillor_data['custom_contact_details'].get('phone', ''),
                'postal_addresses': [],
                'party': party,
                'has_party_logo': has_party_logo,
                'ward_data': ward_result,
                'ward_mapit_area_id': mapit_json.values()[0]['id'],
                'positions': [
                    {
                        'title': {'name': 'Ward Councillor'}
                    }
                ],
                'element_id': 'ward-councillor-{ward_id}-0'.format(
                    ward_id=ward_id
                ),
                'muni_id': muni_id
            }
        ]

    def get_context_data(self, **kwargs):
        context = super(LatLonDetailBaseView, self).get_context_data(**kwargs)

        try:
            context['ward_data'] = self.get_ward_councillors(self.location)
        except WardCouncillorAPIDown as e:
            context['ward_data'] = []
            context['ward_data_not_available'] = u"The error was: {0}".format(e)

        context['location'] = self.location
        context['office_search_radius'] = self.constituency_office_search_radius

        nearest_office_places = (
            ZAPlace.objects
            .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
            .distance(self.location)
            .filter(location__distance_lte=(
                self.location, D(km=self.constituency_office_search_radius)))
            .order_by('distance')
            .select_related('organisation')
            .prefetch_related('organisation__org_rels_as_b')
            .prefetch_related('organisation__position_set')
        )

        context['mp_data'] = mp_data = []
        context['mpl_data'] = mpl_data = []

        for office_place in nearest_office_places:
            organisation = office_place.organisation
            if not organisation.is_ongoing():
                continue

            # Get the party and party logo:
            party = None
            has_party_logo = False
            for org_rel in organisation.org_rels_as_b.all():
                if org_rel.kind.name == 'has_office':
                    party = org_rel.organisation_a
                    if party.slug in self.party_slugs_that_have_logos:
                        has_party_logo = True

            # Find all the constituency contacts:
            for i, position in enumerate(organisation.position_set.filter(
                title__slug='constituency-contact'
            ).currently_active()):
                person = position.person
                element_id = 'constituency-contact-{office_id}-{i}'.format(
                    office_id=position.organisation.id, i=i
                )
                mp_positions = person.position_set \
                    .filter(
                        organisation__slug='national-assembly',
                        title__slug='member'
                    ) \
                    .currently_active()
                mpl_positions = person.position_set \
                    .filter(
                        organisation__kind__slug='provincial-legislature',
                        title__slug='member'
                    ) \
                    .currently_active()
                email, phone = None, None
                email_contact = person.contacts.filter(kind__slug='email').first()

                if email_contact:
                    email = email_contact.value
                phone_contact = person.contacts.filter(kind__slug='voice').first()

                if phone_contact:
                    phone = phone_contact.value
                person_data = {
                    'name': person.legal_name,
                    'person': person,
                    'email': email,
                    'phone': phone,
                    'postal_addresses': [
                        pa.value for pa in office_place.postal_addresses()
                    ],
                    'party': party,
                    'has_party_logo': has_party_logo,
                    'office_place': office_place,
                    'element_id': element_id,
                }

                if mp_positions:
                    person_data['positions'] = mp_positions
                    person_data['is_mp'] = True
                    mp_data.append(person_data)

                if mpl_positions:
                    person_data['positions'] = mpl_positions
                    person_data['is_mpl'] = True
                    mpl_data.append(person_data)

        context['form'] = LocationSearchForm(
            initial={'q': self.request.GET.get('q')}
        )
        return context


class LatLonDetailLocalView(LatLonDetailBaseView):
    template_name = 'south_africa/latlon_local_view.html'


class SAPlaceDetailView(PlaceDetailView):
    def get_context_data(self, **kwargs):
        """
        Get back the people for this place in separate lists so they can
        be displayed separately on the place detail page.
        """
        context = super(SAPlaceDetailView, self).get_context_data(**kwargs)

        for context_string, position_filter in (
            ('national_assembly_people',
                {'organisation__slug': 'national-assembly',
                    'title__slug': 'member'}),
            ('ncop_people',
                {'organisation__slug': 'ncop',
                    'title__slug': 'delegate'}),
            ('legislature_people',
                {'organisation__kind__slug': 'provincial-legislature',
                    'title__slug': 'member'}),
        ):
            all_member_positions = self.object.all_related_positions(). \
                filter(**position_filter).select_related('person')
            current_positions = all_member_positions.currently_active()
            current_people = models.Person.objects.filter(
                position__in=current_positions).distinct()
            former_positions = all_member_positions.currently_inactive()

            context[context_string + '_count'] = current_people.count()
            context[context_string] = current_people
            context['former_' + context_string] = models.Person.objects.filter(
                position__in=former_positions
            ).distinct()

        context['other_people'] = (
            models.Person.objects
            .filter(position__place=self.object)
            .exclude(id__in=context['national_assembly_people'])
            .exclude(id__in=context['former_national_assembly_people'])
            .exclude(id__in=context['ncop_people'])
            .exclude(id__in=context['former_ncop_people'])
            .exclude(id__in=context['legislature_people'])
            .exclude(id__in=context['former_legislature_people'])
        )
        return context


class SAPlaceDetailSub(PlaceDetailSub):
    child_place_template = "south_africa/constituency_office_list_item.html"
    child_place_list_template = "south_africa/constituency_office_list.html"

    def get_context_data(self, **kwargs):
        context = super(SAPlaceDetailSub, self).get_context_data(**kwargs)

        context['child_place_template'] = self.child_place_template
        context['child_place_list_template'] = self.child_place_list_template
        context['subcontent_title'] = 'Constituency Offices'

        if self.object.kind.slug == 'province':
            context['child_places'] = (
                ZAPlace.objects
                .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
                .filter(
                    location__coveredby=self.object.mapit_area.polygons.collect())
            )

        return context
