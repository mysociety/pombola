import warnings
import re

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404
from django.db.models import Count
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import RedirectView, TemplateView
from django.shortcuts import get_object_or_404

import mapit
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

from popit.models import Person as PopitPerson
from speeches.models import Section, Speech, Speaker
from speeches.views import SpeakerView

from pombola.core import models
from pombola.core.views import PlaceDetailView, PlaceDetailSub, \
    OrganisationDetailView, PersonDetail, PlaceDetailView
from pombola.info.views import InfoPageView

from pombola.south_africa.models import ZAPlace

# In the short term, until we have a list of constituency offices and
# addresses from DA, let's bundle these together.
CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS = (
    'constituency-office',
    'constituency-area', # specific to DA party
)

class LatLonDetailView(PlaceDetailView):
    template_name = 'south_africa/latlon_detail_view.html'

    # Using 25km as the default, as that's what's used on MyReps.
    constituency_office_search_radius = 25

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

    def get_context_data(self, **kwargs):
        context = super(LatLonDetailView, self).get_context_data(**kwargs)
        context['location'] = self.location

        context['office_search_radius'] = self.constituency_office_search_radius

        context['nearest_offices'] = nearest_offices = (
            ZAPlace.objects
            .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
            .distance(self.location)
            .filter(location__distance_lte=(self.location, D(km=self.constituency_office_search_radius)))
            .order_by('distance')
            )

        return context


class SAPlaceDetailView(PlaceDetailView):

    def get_context_data(self, **kwargs):
        """
        Get back the people for this place in 3 separate lists so they can
        be displayed separatly on the place detail page.
        """
        context = super(SAPlaceDetailView, self).get_context_data(**kwargs)
        context['national_assembly_people_count'] = self.object.all_related_politicians().filter(position__organisation__slug='national-assembly').count()
        context['ncop_people_count'] = self.object.all_related_politicians().filter(position__organisation__slug='ncop').count()
        context['national_assembly_people'] = self.object.all_related_current_politicians().filter(position__organisation__slug='national-assembly')
        context['former_national_assembly_people'] = self.object.all_related_former_politicians().filter(position__organisation__slug='national-assembly')
        context['ncop_people'] = self.object.all_related_current_politicians().filter(position__organisation__slug='ncop')
        context['former_ncop_people'] = self.object.all_related_former_politicians().filter(position__organisation__slug='ncop')
        context['other_people'] = (models.Person.objects
            .filter(position__place=self.object)
            .exclude(id__in=context['national_assembly_people'])
            .exclude(id__in=context['former_national_assembly_people'])
            .exclude(id__in=context['ncop_people'])
            .exclude(id__in=context['former_ncop_people']))
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
                .filter(location__coveredby=self.object.mapit_area.polygons.collect())
                )

        return context


class SAOrganisationDetailView(OrganisationDetailView):

    def get_context_data(self, **kwargs):
        context = super(SAOrganisationDetailView, self).get_context_data(**kwargs)

        # Get all the parties represented in this house.
        people_in_house = models.Person.objects.filter(position__organisation=self.object)
        parties = models.Organisation.objects.filter(
            kind__slug='party',
            position__person__in=people_in_house,
        ).annotate(person_count=Count('position__person'))
        total_people = sum(map(lambda x: x.person_count, parties))

        # Calculate the % of the house each party occupies.
        for party in parties:
            party.percentage = round((float(party.person_count) / total_people) * 100, 2)

        context['parties'] = parties
        context['total_people'] =  total_people

        return context

    def get_template_names(self):
        if self.object.kind.slug == 'house':
            return [ 'south_africa/organisation_house.html' ]
        else:
            return super(SAOrganisationDetailView, self).get_template_names()


class SAPersonDetail(PersonDetail):

    important_organisations = ('ncop', 'national-assembly', 'national-executive')

    def get_sayit_speaker(self):
        # see also SASpeakerRedirectView for mapping in opposite direction

        pombola_person = self.object

        try:
            i = models.Identifier.objects.get(
                content_type = models.ContentType.objects.get_for_model(models.Person),
                object_id = pombola_person.id,
                scheme = 'org.mysociety.za'
            )
            speaker = Speaker.objects.get(person__popit_id = i.scheme + i.identifier)
            return speaker

        except ObjectDoesNotExist:
            return None

    def get_recent_speeches_for_section(self, section_title):
        pombola_person = self.object
        sayit_speaker = self.get_sayit_speaker()

        if not sayit_speaker:
            # Without a speaker we can't find any speeches
            return Speech.objects.none()

        try:
            # Add parent=None as the title is not unique, hopefully the top level will be.
            sayit_section = Section.objects.get(title=section_title, parent=None)
        except Section.DoesNotExist:
            # No match. Don't raise exception but do produce a warning and then return an empty queryset
            warnings.warn("Could not find top level sayit section '{0}'".format(section_title))
            return Speech.objects.none()

        speeches = (
            sayit_section.descendant_speeches()
                .filter(speaker=sayit_speaker)
                .order_by('-start_date', '-start_time'))

        return speeches


    def get_context_data(self, **kwargs):
        context = super(SAPersonDetail, self).get_context_data(**kwargs)
        context['twitter_contacts'] = self.object.contacts.filter(kind__slug='twitter')
        context['email_contacts'] = self.object.contacts.filter(kind__slug='email')
        context['phone_contacts'] = self.object.contacts.filter(kind__slug__in=('cell', 'voice'))
        context['fax_contacts'] = self.object.contacts.filter(kind__slug='fax')
        context['address_contacts'] = self.object.contacts.filter(kind__slug='address')
        context['positions'] = self.object.politician_positions().filter(organisation__slug__in=self.important_organisations)

        # FIXME - the titles used here will need to be checked and fixed.
        context['hansard']   = self.get_recent_speeches_for_section("Hansard")
        context['committee'] = self.get_recent_speeches_for_section("Committee Minutes")
        context['questions'] = self.get_recent_speeches_for_section("Questions")

        return context


search_models = (
    models.Place,
    models.PositionTitle,
)
if settings.ENABLED_FEATURES['speeches']:
    from speeches.models import Speech
    search_models += ( Speech, )


class SASearchView(SearchView):

    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = SearchQuerySet().models(*search_models).highlight()
        return super(SASearchView, self).__init__(*args, **kwargs)

    def extra_context(self):
        if not self.query:
            return {}
        query = SearchQuerySet().highlight()
        return {
            'person_results': query.models(models.Person).filter(content=AutoQuery(self.request.GET['q'])),
            'organisation_results': query.models(models.Organisation).filter(content=AutoQuery(self.request.GET['q'])),
        }


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'

class SASpeakerRedirectView(RedirectView):

    # see also SAPersonDetail for mapping in opposite direction
    def get_redirect_url(self, **kwargs):
        try:
            id = int( kwargs['pk'] )
            speaker = Speaker.objects.get( id=id )
            popit_id = speaker.person.popit_id
            [scheme, identifier] = re.match('(.*?)(/.*)$', popit_id).groups()
            i = models.Identifier.objects.get(
                content_type = models.ContentType.objects.get_for_model(models.Person),
                scheme = scheme,
                identifier = identifier,
            )
            person = models.Person.objects.get(id=i.object_id)
            return reverse('person', args=(person.slug,))
        except Exception as e:
            raise Http404

class SASpeechesIndex(TemplateView):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Hansard'
    sections_to_show = 25
    section_parent_field = 'section__parent__parent__parent__parent__parent'

    def get_context_data(self, **kwargs):
        context = super(SASpeechesIndex, self).get_context_data(**kwargs)

        # Get the top level section, or 404
        top_section = get_object_or_404(Section, title=self.top_section_name, parent=None)

        # As we know that the hansard section structure is
        # "Hansard" -> yyyy -> mm -> dd -> section -> subsection -> [speeches]
        # we can create a very specific query to drill up to the top level one
        # that we want.

        section_parent_filter = { self.section_parent_field : top_section }
        entries = Speech \
            .objects \
            .filter(**section_parent_filter) \
            .values('section_id', 'start_date') \
            .annotate(speech_count=Count('id')) \
            .order_by('-start_date')

        # loop through and add all the section objects. This is not efficient,
        # but makes the templates easier as we can (for example) use get_absolute_url.
        # Also lets us retrieve the last N parent sections which is what we need for the
        # display.
        parent_sections = set()
        display_entries = []
        for entry in entries:
            section = Section.objects.get(pk=entry['section_id'])
            parent_sections.add(section.parent.id)
            if len(parent_sections) > self.sections_to_show:
                break
            display_entries.append(entry)
            display_entries[-1]['section'] = section

        # PAGINATION NOTE - it would be possible to add pagination to this by simply
        # removing the `break` after self.sections_to_show has been reached and then
        # finding a more efficient way to inflate the sections (perhaps using an
        # embedded lambda, or a custom templatetag). However paginating this page may
        # not be as useful as creating an easy to use drill down based on date, or
        # indeed using search.

        context['entries'] = display_entries
        return context

class SAHansardIndex(SASpeechesIndex):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Hansard'
    section_parent_field = 'section__parent__parent__parent__parent__parent'
    sections_to_show = 25

class SACommitteeIndex(SASpeechesIndex):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Committee Minutes'
    section_parent_field = 'section__parent__parent__parent'
    sections_to_show = 25
