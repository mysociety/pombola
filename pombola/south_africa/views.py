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
from django import forms
from django.utils.translation import ugettext_lazy as _

import mapit
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from haystack.forms import SearchForm

from popit.models import Person as PopitPerson
from speeches.models import Section, Speech, Speaker, Tag
from speeches.views import NamespaceMixin

from pombola.core import models
from pombola.core.views import PlaceDetailView, PlaceDetailSub, \
    OrganisationDetailView, PersonDetail, PlaceDetailView, OrganisationDetailSub
from pombola.info.views import InfoPageView

from pombola.south_africa.models import ZAPlace

# In the short term, until we have a list of constituency offices and
# addresses from DA, let's bundle these together.
CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS = (
    'constituency-office',
    'constituency-area', # specific to DA party
)

class LocationSearchForm(SearchForm):
    q = forms.CharField(required=False, label=_('Search'), widget=forms.TextInput(attrs={'placeholder': 'Your location'}))

class LatLonDetailBaseView(PlaceDetailView):

    # Using 25km as the default, as that's what's used on MyReps.
    constituency_office_search_radius = 25

    # The codes used here should match the party slugs, and the names of the
    # icon files in .../static/images/party-map-icons/
    party_slugs_that_have_logos = set((
        'adcp', 'anc', 'apc', 'azapo', 'cope', 'da', 'ff', 'id', 'ifp', 'mf',
        'pac', 'sacp', 'ucdp', 'udm'
    ));

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
        context = super(LatLonDetailBaseView, self).get_context_data(**kwargs)
        context['location'] = self.location

        context['office_search_radius'] = self.constituency_office_search_radius

        context['nearest_offices'] = nearest_offices = (
            ZAPlace.objects
            .filter(kind__slug__in=CONSTITUENCY_OFFICE_PLACE_KIND_SLUGS)
            .distance(self.location)
            .filter(location__distance_lte=(self.location, D(km=self.constituency_office_search_radius)))
            .order_by('distance')
            )

        # FIXME - There must be a cleaner way/place to do this.
        for office in nearest_offices:
            try:
                cc_positions = office \
                    .organisation \
                    .position_set \
                    .filter(
                        person__position__title__slug='constituency-contact',
                    )

                constituency_contacts = models.Person.objects.filter(position__in=cc_positions)
                office_people_entries = []

                for constituency_contact in constituency_contacts:

                    # Find positions for this person that are relevant to the office.
                    positions = constituency_contact.position_set \
                        .filter(
                            organisation__slug__in = [
                                "national-assembly",
                                office.organisation.slug,
                            ]
                        )

                    office_people_entries.append({
                        'person': constituency_contact,
                        'positions': positions
                    })

                if len(office_people_entries):
                    office.office_people_entries = office_people_entries

            except models.Person.DoesNotExist:
                warnings.warn("{0} has no MPs".format(office.organisation))

            # Try to extract the political membership of this person and store
            # it next to the office. TODO - deal with several parties sharing
            # an office (should this happen?) and MPs with no party connection.
            if hasattr(office, 'office_people_entries'):
                for entry in office.office_people_entries:
                    try:
                        party_slug = entry['person'].position_set.filter(title__slug="member", organisation__kind__slug="party")[0].organisation.slug
                        if party_slug in self.party_slugs_that_have_logos:
                            office.party_slug_for_icon = party_slug
                    except IndexError:
                        warnings.warn("{0} has no party membership".format(entry['person']))

        context['form'] = LocationSearchForm()

        context['politicians'] = (self.object
            .all_related_current_politicians()
            .filter(position__organisation__slug='national-assembly')
        )

        return context


class LatLonDetailNationalView(LatLonDetailBaseView):
    template_name = 'south_africa/latlon_national_view.html'


class LatLonDetailLocalView(LatLonDetailBaseView):
    template_name = 'south_africa/latlon_local_view.html'



class SAPlaceDetailView(PlaceDetailView):

    def get_context_data(self, **kwargs):
        """
        Get back the people for this place in separate lists so they can
        be displayed separately on the place detail page.
        """
        context = super(SAPlaceDetailView, self).get_context_data(**kwargs)

        context['national_assembly_people_count']  = self.object.all_related_politicians().filter(position__organisation__slug='national-assembly').count()
        context['national_assembly_people']        = self.object.all_related_current_politicians().filter(position__organisation__slug='national-assembly')
        context['former_national_assembly_people'] = self.object.all_related_former_politicians().filter(position__organisation__slug='national-assembly')

        context['ncop_people_count']  = self.object.all_related_politicians().filter(position__organisation__slug='ncop').count()
        context['ncop_people']        = self.object.all_related_current_politicians().filter(position__organisation__slug='ncop')
        context['former_ncop_people'] = self.object.all_related_former_politicians().filter(position__organisation__slug='ncop')

        context['legislature_people_count']  = self.object.all_related_politicians().filter(position__organisation__kind__slug='provincial-legislature').count()
        context['legislature_people']        = self.object.all_related_current_politicians().filter(position__organisation__kind__slug='provincial-legislature')
        context['former_legislature_people'] = self.object.all_related_former_politicians().filter(position__organisation__kind__slug='provincial-legislature')

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
                .filter(location__coveredby=self.object.mapit_area.polygons.collect())
                )

        return context


class SAOrganisationDetailView(OrganisationDetailView):

    def get_context_data(self, **kwargs):
        context = super(SAOrganisationDetailView, self).get_context_data(**kwargs)

        if self.object.kind.slug == 'parliament':
            self.add_parliament_counts_to_context_data(context)

        # Sort the list of positions in an organisation by an approximation
        # of their holder's last name.
        context['positions'] = sorted(
            context['positions'],
            key=lambda position: position.person.legal_name.split()[-1]
            )

        return context

    def add_parliament_counts_to_context_data(self, context):
        # Get all the parties represented in this house.
        people_in_house = models.Person.objects.filter(position__organisation=self.object)
        parties = models.Organisation.objects.filter(
            kind__slug='party',
            position__person__in=people_in_house,
        ).annotate(person_count=Count('position__person'))
        total_people = sum(map(lambda x: x.person_count, parties))

        # Calculate the % of the house each party occupies.
        for party in parties:
            party.percentage = float(party.person_count) / total_people * 100

        context['parties'] = parties
        context['total_people'] =  total_people

        context['all_members'] = self.object.position_set.filter(title__slug='member')
        context['office_bearers'] = self.object.position_set.exclude(title__slug='member')

    def get_template_names(self):
        if self.object.kind.slug == 'parliament':
            return [ 'south_africa/organisation_house.html' ]
        else:
            return super(SAOrganisationDetailView, self).get_template_names()


class SAOrganisationDetailSub(OrganisationDetailSub):
    def get_context_data(self, *args, **kwargs):
        context = super(SAOrganisationDetailSub, self).get_context_data(*args, **kwargs)

        if self.kwargs['sub_page'] == 'people':
            all_positions = context['all_positions'] = self.object.position_set.all()
            if self.request.GET.get('member'):
                context['sorted_positions'] = all_positions.filter(title__slug='member')
            elif self.request.GET.get('delegates'):
                context['sorted_positions'] = all_positions.filter(title__slug='delegate')
            elif self.request.GET.get('office'):
                context['sorted_positions'] = all_positions.exclude(title__slug='member')

            if self.request.GET.get('order') == 'place':
                context['sorted_positions'] = context['sorted_positions'].order_by_place()
            else:
                context['sorted_positions'] = context['sorted_positions'].order_by_person_name()

        return context


class PersonSpeakerMappings(object):
    def pombola_person_to_sayit_speaker(self, person):
        try:
            i = models.Identifier.objects.get(
                content_type = models.ContentType.objects.get_for_model(models.Person),
                object_id = person.id,
                scheme = 'org.mysociety.za'
            )
            speaker = Speaker.objects.get(person__popit_id = i.scheme + i.identifier)
            return speaker

        except ObjectDoesNotExist:
            return None


class SAPersonDetail(PersonDetail):

    important_organisations = ('ncop', 'national-assembly', 'national-executive')

    def get_recent_speeches_for_section(self, section_title, limit=5):
        pombola_person = self.object
        sayit_speaker = PersonSpeakerMappings().pombola_person_to_sayit_speaker(pombola_person)

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

        if limit:
            speeches = speeches[:limit]

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
        context['question']  = self.get_recent_speeches_for_section("Questions")

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
        # We can't just order by -start_date, since that will put any
        # Place and PositionTitle results (where there is no
        # start_date in the index) at the very end, after potentially
        # thousands of Speech results.  We can get around this by
        # ordering on django_ct first, since places and positiontitles
        # have content types that just happen to come earlier in the
        # alphabet than that of speeches.
        kwargs['searchqueryset'] = SearchQuerySet().models(*search_models). \
            order_by('django_ct', '-start_date'). \
            highlight()
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

class SASpeechesIndex(NamespaceMixin, TemplateView):
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

def questions_section_sort_key(section):
    """This function helps to sort question sections

    The intention is to have questions for the President first, then
    Deputy President, then offices associated with the presidency,
    then questions to ministers sorted by the name of the ministry,
    and finally anything else sorted just on the title.

    >>> questions_section_sort_key(Section(title="for the President"))
    'AAAfor the President'
    >>> questions_section_sort_key(Section(title="ask the deputy president"))
    'BBBask the deputy president'
    >>> questions_section_sort_key(Section(title="about the Presidency"))
    'CCCabout the Presidency'
    >>> questions_section_sort_key(Section(title="Questions asked to Minister for Foo"))
    'DDDFoo'
    >>> questions_section_sort_key(Section(title="Questions asked to the Minister for Bar"))
    'DDDBar'
    >>> questions_section_sort_key(Section(title="Questions asked to Minister of Baz"))
    'DDDBaz'
    >>> questions_section_sort_key(Section(title="Minister of Quux"))
    'DDDQuux'
    >>> questions_section_sort_key(Section(title="Random"))
    'MMMRandom'
    """
    title = section.title
    if re.search(r'(?i)Deputy\s+President', title):
        return "BBB" + title
    if re.search(r'(?i)President', title):
        return "AAA" + title
    if re.search(r'(?i)Presidency', title):
        return "CCC" + title
    stripped_title = title
    for regexp in (r'^(?i)Questions\s+asked\s+to\s+(the\s+)?Minister\s+(of|for(\s+the)?)\s+',
                   r'^(?i)Minister\s+(of|for(\s+the)?)\s+'):
        stripped_title = re.sub(regexp, '', stripped_title)
    if stripped_title == title:
        # i.e. it wasn't questions for a minister
        return "MMM" + title
    return "DDD" + stripped_title

class SAQuestionIndex(SASpeechesIndex):
    template_name = 'south_africa/question_index.html'
    top_section_name='Questions'

    def get_context_data(self, **kwargs):
        context = super(SASpeechesIndex, self).get_context_data(**kwargs)

        # Get the top level section, or 404
        top_section = get_object_or_404(Section, title=self.top_section_name, parent=None)

        # the question section structure is
        # "Questions" -> "Questions asked to Minister for X" -> "Date" ...

        sections = Section \
            .objects \
            .filter(parent=top_section) \
            .annotate(speech_count=Count('children__speech__id'))

        context['entries'] = sorted(sections,
                                    key=questions_section_sort_key)
        return context

class SACommitteeSpeechRedirectView(RedirectView):

    def get_redirect_url(self, **kwargs):
        try:
            id = int( kwargs['pk'] )
            speech = Speech.objects.get( id=id )
            source_url = speech.source_url
            if source_url:
                return source_url
        except Exception as e:
            raise Http404

        raise Http404("No source URL for this content")

class SACommitteeSectionRedirectView(RedirectView):

    def get_redirect_url(self, **kwargs):
        try:
            id = int( kwargs['pk'] )
            section = Section.objects.get( id=id )
            for speech in section.speech_set.all():
                source_url = speech.source_url
                if source_url:
                    return source_url
        except Exception as e:
            raise Http404

        raise Http404("No source URL for this content")


class SAPersonAppearanceView(TemplateView):

    template_name = 'south_africa/person_appearances.html'

    def get_context_data(self, **kwargs):
        context = super(SAPersonAppearanceView, self).get_context_data(**kwargs)

        # Extract slug and tag provided on url
        person_slug = self.kwargs['person_slug']
        speech_tag  = self.kwargs['speech_tag']

        # Find (or 404) matching objects
        person = get_object_or_404(models.Person, slug=person_slug)
        tag    = get_object_or_404(Tag, name=speech_tag)

        # SayIt speaker is different to core.Person, Load the speaker
        speaker = PersonSpeakerMappings().pombola_person_to_sayit_speaker(person)

        # Load the speeches. Pagination is done in the template
        speeches = Speech.objects \
            .filter(tags=tag, speaker=speaker) \
            .order_by('-start_date', '-start_time')

        # Store person as 'object' for the person_base.html template
        context['object']  = person
        context['speeches'] = speeches

        # Add a hardcoded section-view url name to use for the speeches. Would
        # rather this was not hardcoded here but seems hard to avoid.
        if (speech_tag in ['hansard', 'committee', 'question']):
            context['section_url'] = '%s:section-view' % speech_tag
        else:
            # speech_tag not know. Use 'None' for template default instead
            context['section_url'] = None

        return context
