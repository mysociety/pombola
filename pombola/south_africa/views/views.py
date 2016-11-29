from __future__ import division
from .constants import API_REQUESTS_TIMEOUT

import datetime
import dateutil
import json
import re
import warnings

import requests

from django.http import Http404
from django.db.models import Count, Min, Max
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import RedirectView, TemplateView
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from haystack.query import RelatedSearchQuerySet, SQ
from haystack.inputs import AutoQuery

from info.views import InfoBlogView

from speeches.models import Section, Speech, Speaker, Tag
from speeches.views import NamespaceMixin, SpeechView, SectionView

from info.views import InfoPageView

from slug_helpers.views import SlugRedirect

from pombola.core import models
from pombola.core.views import (
    CommentArchiveMixin, PersonSpeakerMappingsMixin)
from pombola.search.views import SearchBaseView

from pombola.interests_register.models import Release, Category, Entry
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_date_extensions.fields import ApproximateDate


class SASearchView(SearchBaseView):

    def __init__(self, *args, **kwargs):
        super(SASearchView, self).__init__(*args, **kwargs)
        del self.search_sections['speeches']
        self.search_sections['questions'] = {
            'model': Speech,
            'title': 'Questions and Answers',
            'filter': {
                'args': [SQ(tags='question') | SQ(tags='answer')],
            }
        }
        self.search_sections['committee'] = {
            'model': Speech,
            'title': 'Committee Appearance',
            'filter': {
                'kwargs': {
                    'tags': 'committee'
                }
            }
        }
        self.search_sections['hansard'] = {
            'model': Speech,
            'title': 'Hansard',
            'filter': {
                'kwargs': {
                    'tags': 'hansard'
                }
            }
        }
        self.section_ordering.remove('speeches')
        self.section_ordering += [
            'questions', 'committee', 'hansard'
        ]


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'

class SASpeakerRedirectView(RedirectView):

    permanent = False

    # see also SAPersonDetail for mapping in opposite direction
    def get_redirect_url(self, *args, **kwargs):
        try:
            speaker = Speaker.objects.get(pk=kwargs['pk'])
            return reverse(
                'person',
                args=(speaker.pombola_link.pombola_person.slug,)
            )
        except ObjectDoesNotExist:
            raise Http404

class SASpeechesIndex(NamespaceMixin, TemplateView):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Hansard'
    sections_to_show = 25
    section_parent_field = 'parent__parent__parent__parent'

    def get_context_data(self, **kwargs):
        context = super(SASpeechesIndex, self).get_context_data(**kwargs)
        self.page = self.request.GET.get('page')

        # Get the top level section, or 404
        top_section = get_object_or_404(Section, heading=self.top_section_name, parent=None)
        context['show_lateness_warning'] = (self.top_section_name == 'Hansard')

        # As we know that the hansard section structure is
        # "Hansard" -> yyyy -> mm -> dd -> section -> subsection -> [speeches]
        # we can create very specific queries to fetch the sections
        # then the subsections containing the speeches themselves.
        #
        # The parent_sections form the headings which are expanded by javascript
        # to reveal the debate_sections
        #
        # FIXME ideally we'd have start_date for sections rather than
        # having to get MAX('start_date') from the speeches table

        # exclude sections without subsections and
        # with subsections that have no speeches
        section_filter = {
            self.section_parent_field : top_section,
            'children__speech__id__isnull' : False,
            'children__id__isnull' : False
        }

        # get a list of all the section headings
        all_parent_section_headings = Section \
              .objects \
              .filter(**section_filter) \
              .values('heading') \
              .distinct() \
              .annotate(latest_start_date=Max('children__speech__start_date')) \
              .order_by('-latest_start_date')

        # use Paginator to cut this down to the sections for the current page
        paginator = Paginator(all_parent_section_headings, self.sections_to_show)
        try:
            parent_section_headings = paginator.page(self.page)
        except PageNotAnInteger:
            parent_section_headings = paginator.page(1)
        except EmptyPage:
            parent_section_headings = paginator.page(paginator.num_pages)

        # get the sections for the current page in date order
        headings = list(section['heading'] for section in parent_section_headings)
        section_filter['heading__in'] = headings
        parent_sections = Section \
              .objects \
              .values('id', 'heading') \
              .filter(**section_filter) \
              .annotate(latest_start_date=Max('children__speech__start_date')) \
              .order_by('-latest_start_date', 'heading')

        # get the subsections based on the relevant section ids
        # exclude those with blank headings as we have no way of linking to them
        parent_ids = list(section['id'] for section in parent_sections)
        debate_sections = Section \
            .objects \
            .filter(parent_id__in=parent_ids, speech__id__isnull=False) \
            .annotate(start_order=Min('speech__id'), speech_start_date=Max('speech__start_date'), speech_count=Count('speech__id')) \
            .exclude(heading='') \
            .order_by('-speech_start_date', 'parent__heading', 'start_order')

        context['entries'] = debate_sections
        context['page_obj'] = parent_section_headings
        return context

class SAHansardIndex(SASpeechesIndex):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Hansard'
    section_parent_field = 'parent__parent__parent__parent'
    sections_to_show = 15

class SACommitteeIndex(SASpeechesIndex):
    template_name = 'south_africa/hansard_index.html'
    top_section_name='Committee Minutes'
    section_parent_field = 'parent__parent'
    sections_to_show = 25

def questions_section_sort_key(section):
    """This function helps to sort question sections

    The intention is to have questions for the President first, then
    Deputy President, then offices associated with the presidency,
    then questions to ministers sorted by the name of the ministry,
    and finally anything else sorted just on the heading.

    >>> questions_section_sort_key(Section(heading="for the President"))
    'AAAfor the President'
    >>> questions_section_sort_key(Section(heading="ask the deputy president"))
    'BBBask the deputy president'
    >>> questions_section_sort_key(Section(heading="about the Presidency"))
    'CCCabout the Presidency'
    >>> questions_section_sort_key(Section(heading="Questions asked to Minister for Foo"))
    'DDDFoo'
    >>> questions_section_sort_key(Section(heading="Questions asked to the Minister for Bar"))
    'DDDBar'
    >>> questions_section_sort_key(Section(heading="Questions asked to Minister of Baz"))
    'DDDBaz'
    >>> questions_section_sort_key(Section(heading="Minister of Quux"))
    'DDDQuux'
    >>> questions_section_sort_key(Section(heading="Random"))
    'MMMRandom'
    """
    heading = section.heading
    if re.search(r'(?i)Deputy\s+President', heading):
        return "BBB" + heading
    if re.search(r'(?i)President', heading):
        return "AAA" + heading
    if re.search(r'(?i)Presidency', heading):
        return "CCC" + heading
    stripped_heading = heading
    for regexp in (r'^(?i)Questions\s+asked\s+to\s+(the\s+)?Minister\s+(of|for(\s+the)?)\s+',
                   r'^(?i)Minister\s+(of|for(\s+the)?)\s+'):
        stripped_heading = re.sub(regexp, '', stripped_heading)
    if stripped_heading == heading:
        # i.e. it wasn't questions for a minister
        return "MMM" + heading
    return "DDD" + stripped_heading

class SAQuestionIndex(TemplateView):
    template_name = 'south_africa/question_index.html'

    def get_context_data(self, **kwargs):
        context = super(SAQuestionIndex, self).get_context_data(**kwargs)

        context['ministers'] = []
        ministers = Section.objects.filter(parent__heading='Questions')
        ministers = sorted(ministers, key=questions_section_sort_key)
        for minister in ministers:
            context['ministers'].append({
                'title': minister.title.replace('Questions asked to the ',''),
                'slug': minister.slug
                })

        context['orderby'] = 'recentanswers'
        context['minister'] = 'all'
        context['q'] = ''

        #set filter values
        for key in ('orderby', 'minister', 'q'):
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        if not context['orderby'] in ['recentquestions', 'recentanswers']:
            context['orderby'] = 'recentquestions'

        search_result_sections = []

        if context['q'] != '':
            #using a RelatedSearchQuerySet seems to result in fewer
            #queries, although the same results can be achieved with a
            #SearchQuerySet
            query = RelatedSearchQuerySet().models(Speech)
            query = query.filter(
                tags__name__in = ['question', 'answer'],
                content=AutoQuery(context['q']),
                ).load_all()

            all_speeches = Speech.objects.all().filter(
                tags__name__in = ['question', 'answer'])

            if context['minister'] != 'all':
                all_speeches = all_speeches.filter(
                    section__parent__slug=context['minister']
                    )

            query = query.load_all_queryset(Speech, all_speeches)

            for result in query:
                search_result_sections.append(result.object.section.id)

        sections = Section \
            .objects \
            .filter(
                parent__parent__heading='Questions'
            ) \
            .select_related('parent__heading') \
            .prefetch_related('speech_set') \
            .annotate(
                earliest_date=Min('speech__start_date'),
                smallest_id=Min('speech__id'),
                number_speeches=Count('speech'),
                latest_date=Max('speech__start_date'),
            )

        if context['minister'] != 'all':
            sections = sections.filter(parent__slug=context['minister'])

        if len(search_result_sections)>0:
            sections = sections.filter(id__in=search_result_sections)

        if context['orderby'] == 'recentanswers':
            sections = sections.filter(number_speeches__gt=1).order_by(
                '-latest_date',
                '-smallest_id'
            )
        else:
            sections = sections.order_by(
                '-earliest_date',
                '-smallest_id'
            )

        paginator = Paginator(sections, 10)
        page = self.request.GET.get('page')

        try:
            sections = paginator.page(page)
        except PageNotAnInteger:
            sections = paginator.page(1)
        except EmptyPage:
            sections = paginator.page(paginator.num_pages)

        context['paginator'] = sections

        #format questions and answers for the template
        questions = []
        for section in sections:
            question = section.speech_set.all()[0]
            question.questionto = section.parent.heading.replace('Questions asked to the ','')
            question.questionto_slug = section.parent.slug

            #assume if there is more than one speech that the question is answered
            if len(section.speech_set.all())>1:
                question.answer = section \
                    .speech_set \
                    .all()[len(section.speech_set.all())-1]

                #extract the actual reply from the reply text (replies
                #often include the original question and other text,
                #such as a letterhead)
                text = question.answer.text.split('REPLY')
                if len(text)>1:
                    question.answer.text = text[len(text)-1]
                    if question.answer.text[0]==':':
                        question.answer.text = question.answer.text[1:]

            questions.append(question)

        context['speeches'] = questions

        return context


class OldSpeechRedirect(RedirectView):

    """Redirects from an old speech URL to the current one"""

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        try:
            speech_id = int(kwargs['pk'])
            speech = Speech.objects.get(pk=speech_id)
            return reverse(
                'speeches:speech-view',
                args=[speech_id])
        except (ValueError, Speech.DoesNotExist):
            raise Http404


class OldSectionRedirect(RedirectView):

    """Redirects from an old section URL to the current one"""

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        try:
            section_id = int(kwargs['pk'])
            section = Section.objects.get(pk=section_id)
            return reverse(
                'speeches:section-view',
                args=[section.get_path])
        except (ValueError, Section.DoesNotExist):
            raise Http404


class SAPersonAppearanceView(PersonSpeakerMappingsMixin, TemplateView):

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
        speaker = self.pombola_person_to_sayit_speaker(person)

        # Load the speeches. Pagination is done in the template
        speeches = Speech.objects \
            .filter(tags=tag, speaker=speaker) \
            .order_by('-start_date', '-start_time')

        # Store person as 'object' for the person_base.html template
        context['object']  = person
        context['speeches'] = speeches

        # Add a hardcoded section-view url name to use for the speeches. Would
        # rather this was not hardcoded here but seems hard to avoid.
        # speech_tag not known. Use 'None' for template default instead
        context['section_url'] = None

        return context


def should_redirect_to_source(section):
    # If this committee is descended from the Committee Minutes
    # section, redirect to the source transcript on the PMG website:
    root_section = section.get_ancestors[0]
    return root_section.slug == 'committee-minutes'


class SASpeechView(SpeechView):

    def get(self, request, *args, **kwargs):
        speech = self.object = self.get_object()
        try_redirect = should_redirect_to_source(speech.section)
        if try_redirect and speech.source_url:
            return redirect(speech.source_url)
        context = self.get_context_data(object=speech)
        return self.render_to_response(context)

    def get_queryset(self):
        return Speech.objects.all()

class SASectionView(SectionView):

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            #if not found check if any sections have been redirected by
            #considering the deepest section first
            full_slug = self.kwargs.get('full_slug', None)
            slugs = full_slug.split('/')
            for i in range(len(slugs), 0, -1):
                try:
                    check_slug = '/'.join(slugs[:i])
                    sr = SlugRedirect.objects.get(
                        content_type=ContentType.objects.get_for_model(Section),
                        old_object_slug=check_slug
                    )
                    new_url = '/' + full_slug.replace(
                        check_slug,
                        sr.new_object.get_path,
                        1)
                    break
                except SlugRedirect.DoesNotExist:
                    pass

            try:
                return redirect(new_url)
            except NameError:
                raise Http404

        if should_redirect_to_source(self.object):
            # Find a URL to redirect to; try to get any speech in the
            # section with a non-blank source URL. FIXME: after
            # switching to Django 1.6, .first() will make this simpler.
            speeches = self.object.speech_set.exclude(source_url='')[:1]
            if speeches:
                speech = speeches[0]
                redirect_url = speech.source_url
                if redirect_url:
                    return redirect(redirect_url)

        if self.object.get_ancestors[0].slug == 'questions':
            self.template_name = 'south_africa/question_section_detail.html'

            if len(self.object.get_ancestors) == 2:
                #level two question sections are displayed on the
                #landing page
                redirect_url = '/question/?minister=%s&orderby=recentquestions' % \
                    (self.object.slug)
                return redirect(redirect_url)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class SAElectionOverviewMixin(TemplateView):
    election_type = ''

    def get_context_data(self, **kwargs):
        context = super(SAElectionOverviewMixin, self).get_context_data(**kwargs)

        # XXX Does this need to only be parties standing in the election?
        party_kind = models.OrganisationKind.objects.get(slug='party')
        context['party_list'] = models.Organisation.objects.filter(
            kind=party_kind).order_by('name')

        province_kind = models.PlaceKind.objects.get(slug='province')
        context['province_list'] = models.Place.objects.filter(
            kind=province_kind).order_by('name')

        election_year = self.kwargs['election_year']

        # All lists of candidates share this kind
        election_list = models.OrganisationKind.objects.get(slug='election-list')

        context['election_year'] = election_year

        # Build the right election list names
        election_list_suffix = '-national-election-list-' + election_year

        # All the running parties live in this list
        running_parties = []

        # Find the slugs of all parties taking part in the national election
        national_running_party_lists = models.Organisation.objects.filter(
            kind=election_list,
            slug__endswith=election_list_suffix
        ).order_by('name')

        # Loop through national sets and extract slugs
        for l in national_running_party_lists:
            party_slug = l.slug.replace(election_list_suffix, '')
            if not party_slug in running_parties:
                running_parties.append(party_slug)

        # I am so sorry for this.
        context['running_party_list'] = []
        for running_party in running_parties:
            context['running_party_list'].append(models.Organisation.objects.get(slug=running_party))

        return context

class SAElectionOverviewView(SAElectionOverviewMixin):
    template_name = 'south_africa/election/overview.html'

class SAElectionStatisticsView(SAElectionOverviewMixin):
    template_name = 'south_africa/election/statistics.html'
    election_type = 'statistics'

    def get_context_data(self, **kwargs):
        context = super(SAElectionStatisticsView, self).get_context_data(**kwargs)

        context['current_mps'] = {'all': {}, 'byparty': []}

        election_2014_query = (
            Q(person__position__organisation__slug__contains='national-election-list-2014') |
            (Q(person__position__organisation__slug__contains='election-list-2014') &
             Q(person__position__organisation__slug__contains='regional'))
            )

        current_na_positions = (
            models.Organisation.objects
            .get(slug='national-assembly')
            .position_set.all()
            .currently_active()
            )

        context['current_mps']['all']['current'] = (
            current_na_positions
            .order_by('person__id')
            .distinct('person__id')
            .count()
            )
        context['current_mps']['all']['rerunning'] = (
            current_na_positions
            .filter(election_2014_query)
            .order_by('person__id')
            .distinct('person__id')
            .count()
            )
        context['current_mps']['all']['percent_rerunning'] = 100 * context['current_mps']['all']['rerunning'] / context['current_mps']['all']['current']

        #find the number of current MPs running for office per party
        for p in context['party_list']:
            party = models.Organisation.objects.get(slug=p.slug)
            current = (
                current_na_positions
                .filter(person__position__organisation__slug=p.slug)
                .order_by('person__id')
                .distinct('person__id')
                .count()
                )
            rerunning = (
                current_na_positions
                .filter(person__position__organisation__slug=p.slug)
                .filter(election_2014_query)
                .order_by('person__id')
                .distinct('person__id')
                .count()
                )
            if current:
                percent = 100 * rerunning / current
                context['current_mps']['byparty'].append({'party': party, 'current': current, 'rerunning': rerunning, 'percent_rerunning': percent})


        #find individuals who appear to have switched party
        context['people_new_party'] = []
        people = models.Person.objects.filter(position__organisation__kind__slug='party', position__title__slug='member').annotate(num_parties=Count('position')).filter(num_parties__gt=1)

        for person in people:
            #check whether the person is a candidate - there is probably be a cleaner way to do this in the initial query
            person_list = person.position_set.all().filter(organisation__slug__contains='election-list-2014')
            if person_list:
                context['people_new_party'].append({
                    'person': person,
                    'current_positions': person.position_set.all().filter(organisation__kind__slug='party').currently_active(),
                    'former_positions': person.position_set.all().filter(organisation__kind__slug='party').currently_inactive(),
                    'person_list': person_list
                })

        return context

class SAElectionNationalView(SAElectionOverviewMixin):
    template_name = 'south_africa/election/national.html'
    election_type = 'national'

class SAElectionProvincialView(SAElectionOverviewMixin):
    template_name = 'south_africa/election/provincial.html'
    election_type = 'provincial'

class SAElectionPartyCandidatesView(TemplateView):

    template_name = 'south_africa/election_candidates_party.html'

    election_type = 'national'

    def get_context_data(self, **kwargs):
        context = super(SAElectionPartyCandidatesView, self).get_context_data(**kwargs)

        # These are common bits
        election_year = self.kwargs['election_year']
        election_type = self.election_type

        context['election_year'] = election_year
        context['election_type'] = election_type

        # Details from the URI
        if 'party_name' in self.kwargs:
            party_name = self.kwargs['party_name']
        else:
            party_name = None

        if 'province_name' in self.kwargs:
            province_name = self.kwargs['province_name']
            # Also get the province object, so we can use its details
            province_kind = models.PlaceKind.objects.get(slug='province')
            context['province'] = models.Place.objects.get(
                kind=province_kind,
                slug=province_name)
        else:
            province_name = None

        # All lists of candidates share this kind
        election_list = models.OrganisationKind.objects.get(slug='election-list')

        # Build the right election list name
        election_list_name = party_name

        if election_type == 'provincial':
            election_list_name += '-provincial'
            election_list_name += '-' + province_name
        elif election_type == 'national' and province_name is not None:
            election_list_name += '-regional'
            election_list_name += '-' + province_name
        else:
            election_list_name += '-national'

        election_list_name += '-election-list'
        election_list_name += '-' + election_year

        # This is a party template, so get the party
        context['party'] = get_object_or_404(models.Organisation, slug=party_name)

        # Now go get the party's election list (assuming it exists)
        election_list = get_object_or_404(models.Organisation,
            slug=election_list_name
        )

        candidates = election_list.position_set.select_related('title').all()

        context['party_election_list'] = sorted(candidates,key=lambda x:
            int(re.match('\d+', x.title.name).group())
        )

        # Grab a list of provinces in which the party is actually running
        # Only relevant for national election non-province party lists
        if election_type == 'national' and province_name is None:

            # Find the lists of regional candidates for this party
            party_election_lists_startwith = party_name + '-regional-'
            party_election_lists_endwith = '-election-list-' + election_year

            party_election_lists = models.Organisation.objects.filter(
                slug__startswith=party_election_lists_startwith,
                slug__endswith=party_election_lists_endwith
            ).order_by('name')

            # Loop through lists and extract province slugs
            party_provinces = []
            for l in party_election_lists:
                province_slug = l.slug.replace(party_election_lists_startwith, '')
                province_slug = province_slug.replace(party_election_lists_endwith, '')
                party_provinces.append(province_slug)

            context['province_list'] = models.Place.objects.filter(
                kind__slug='province',
                slug__in=party_provinces
            )

        return context

class SAElectionProvinceCandidatesView(TemplateView):

    template_name = 'south_africa/election_candidates_province.html'

    election_type = 'national'

    def get_context_data(self, **kwargs):
        context = super(SAElectionProvinceCandidatesView, self).get_context_data(**kwargs)

        # These are common bits
        election_year = self.kwargs['election_year']
        election_type = self.election_type

        context['election_year'] = election_year
        context['election_type'] = election_type

        # Details from the URI
        if 'party_name' in self.kwargs:
            party_name = self.kwargs['party_name']
        else:
            party_name = None

        # The province name should always exist
        province_name = self.kwargs['province_name']

        # All lists of candidates share this kind
        election_list = models.OrganisationKind.objects.get(slug='election-list')

        # Build the right election list name
        election_list_name = ''

        if election_type == 'provincial':
            election_list_name += '-provincial'
            election_list_name += '-' + province_name
        elif election_type == 'national' and province_name is not None:
            election_list_name += '-regional'
            election_list_name += '-' + province_name

        election_list_name += '-election-list'
        election_list_name += '-' + election_year

        # Go get all the election lists!
        election_lists = models.Organisation.objects.filter(
            slug__endswith=election_list_name
        ).order_by('name')

        # Loop round each election list so we can go do other necessary queries
        context['province_election_lists'] = []

        for election_list in election_lists:

            # Get the party data, finding the raw party slug from the list name
            party = models.Organisation.objects.get(
                slug=election_list.slug.replace(election_list_name, '')
            )

            # Get the candidates data for that list
            candidate_list = election_list.position_set.select_related('title').all()

            candidates = sorted(candidate_list, key=lambda x:
                int(re.match('\d+', x.title.name).group())
            )

            context['province_election_lists'].append({
                'party': party,
                'candidates': candidates
            })

        # Get the province object, so we can use its details
        province_kind = models.PlaceKind.objects.get(slug='province')
        context['province'] = models.Place.objects.get(
            kind=province_kind,
            slug=province_name)

        return context

class SAMembersInterestsIndex(TemplateView):
    template_name = "interests_register/index.html"

    def get_context_data(self, **kwargs):
        context = {}

        #get the data for the form
        kind_slugs = (
            'parliament',
            'executive',
            'joint-committees',
            'ncop-committees',
            'ad-hoc-committees',
            'national-assembly-committees'
        )
        context['categories'] = Category.objects.all()
        context['parties'] = models.Organisation.objects.filter(kind__slug='party')
        context['organisations'] = models.Organisation.objects \
            .filter(kind__slug__in=kind_slugs) \
            .order_by('kind__id','name')
        context['releases'] = Release.objects.all()

        #set filter values
        for key in ('display', 'category', 'party', 'organisation', 'release'):
            context[key] = 'all'
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        try:
            if context['release']!='all':
                release = Release.objects.get(slug=context['release'])
                context['release_id'] = release.id

            if context['category']!='all':
                categorylookup = Category.objects.get(slug=self.request.GET['category'])
                context['category_id'] = categorylookup.id
        except ObjectDoesNotExist:
            return context

        #complete view - declarations for multiple people in multiple categories
        if context['display']=='all' and context['category']=='all':
            context = self.get_complete_view(context)

        #section view - data for multiple people in different categories
        elif context['display']=='all' and context['category']!='all':
            context = self.get_section_view(context)

        #numberbyrepresentative view - number of declarations per person per category
        elif context['display']=='numberbyrepresentative':
            context = self.get_number_by_representative_view(context)

        #numberbysource view - number of declarations by source per category
        elif context['display']=='numberbysource':
            context = self.get_numberbysource_view(context)

        return context

    def get_complete_view(self, context):

        release_content_type = ContentType.objects.get_for_model(Release)

        #complete view - declarations for multiple people in multiple categories
        context['layout'] = 'complete'

        when = datetime.date.today()
        now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        people = Entry.objects.order_by(
            'person__legal_name',
            'release__date'
        ).distinct(
            'person__legal_name',
            'release__date'
        )

        if context['release']!='all':
            people = people.filter(release=context['release_id'])

        if context['party']!='all':
            people = people.filter(
                Q(person__position__end_date__gte=now_approx) | Q(person__position__end_date=''),
                person__position__organisation__slug=context['party'],
                person__position__start_date__lte=now_approx)

        if context['organisation']!='all':
            people = people.filter(
                Q(person__position__end_date__gte=now_approx) | Q(person__position__end_date=''),
                person__position__organisation__slug=context['organisation'],
                person__position__start_date__lte=now_approx)

        paginator = Paginator(people, 10)
        page = self.request.GET.get('page')

        try:
            people_paginated = paginator.page(page)
        except PageNotAnInteger:
            people_paginated = paginator.page(1)
        except EmptyPage:
            people_paginated = paginator.page(paginator.num_pages)

        context['paginator'] = people_paginated

        #tabulate the data
        data = []
        for entry_person in people_paginated:
            person = entry_person.person
            year = entry_person.release.date.year
            person_data = []
            person_categories = person.interests_register_entries.filter(
                release=entry_person.release
            ).order_by(
                'category__id'
            ).distinct(
                'category__id'
            )

            sources = models.InformationSource.objects.filter(
                content_type=release_content_type,
                object_id=entry_person.release.id
            )
            if sources:
                source_url = sources[0].source
            else:
                source_url = ''

            for cat in person_categories:
                entries = person.interests_register_entries.filter(
                    category=cat.category,
                    release=entry_person.release)

                headers = []
                headers_index = {}
                cat_data = []
                for entry in entries:
                    row = ['']*len(headers)

                    for entrylineitem in entry.line_items.all():
                        if entrylineitem.key not in headers:
                            headers_index[entrylineitem.key] = len(headers)
                            headers.append(entrylineitem.key)
                            row.append('')

                        row[headers_index[entrylineitem.key]] = entrylineitem.value

                    cat_data.append(row)

                person_data.append({
                    'category': cat.category,
                    'headers': headers,
                    'data': cat_data})
            data.append({
                'person': person,
                'data': person_data,
                'year': year,
                'source_url': source_url})

        context['data'] = data

        return context

    def get_section_view(self, context):
        release_content_type = ContentType.objects.get_for_model(Release)

        #section view - data for multiple people in different categories
        context['layout'] = 'section'

        when = datetime.date.today()
        now_approx = repr(ApproximateDate(year=when.year, month=when.month, day=when.day))

        entries = Entry.objects.select_related(
            'person',
            'category'
        ).all().filter(
            category__id=context['category_id']
        ).order_by(
            'person',
            'category'
        )

        if context['release']!='all':
            entries = entries.filter(release=context['release_id'])

        if context['party']!='all':
            entries = entries.filter(
                Q(person__position__end_date__gte=now_approx) | Q(person__position__end_date=''),
                person__position__organisation__slug=context['party'],
                person__position__start_date__lte=now_approx)

        if context['organisation']!='all':
            entries = entries.filter(
                Q(person__position__end_date__gte=now_approx) | Q(person__position__end_date=''),
                person__position__organisation__slug=context['organisation'],
                person__position__start_date__lte=now_approx)

        paginator = Paginator(entries, 25)
        page = self.request.GET.get('page')

        try:
            entries_paginated = paginator.page(page)
        except PageNotAnInteger:
            entries_paginated = paginator.page(1)
        except EmptyPage:
            entries_paginated = paginator.page(paginator.num_pages)

        headers = ['Year', 'Person', 'Type']
        headers_index = {'Year': 0, 'Person': 1, 'Type': 2}
        data = []
        for entry in entries_paginated:
            sources = models.InformationSource.objects.filter(
                content_type=release_content_type,
                object_id=entry.release.id
            )
            if sources:
                source_url = sources[0].source
            else:
                source_url = ''

            entry.release.source_url = source_url

            row = ['']*len(headers)
            row[0] = entry.release
            row[1] = entry.person
            row[2] = entry.category.name

            for entrylineitem in entry.line_items.all():
                if entrylineitem.key not in headers:
                    headers_index[entrylineitem.key] = len(headers)
                    headers.append(entrylineitem.key)
                    row.append('')

                row[headers_index[entrylineitem.key]] = entrylineitem.value

            data.append(row)

        context['data'] = data
        context['headers'] = headers
        context['paginator'] = entries_paginated

        return context

    def get_number_by_representative_view(self, context):
        release_content_type = ContentType.objects.get_for_model(Release)

        #numberbyrepresentative view - number of declarations per person per category
        context['layout'] = 'numberbyrepresentative'

        #custom sql used as
        #Entry.objects.values('category', 'release', 'person').annotate(c=Count('id')).order_by('-c')
        #returns a ValueQuerySet with foreign keys, not model instances
        if context['category']=='all' and context['release']=='all':
            data = Entry.objects.raw(
                '''SELECT max(id) as id, category_id, release_id, person_id,
                count(*) as c FROM "interests_register_entry"
                GROUP BY category_id, release_id, person_id ORDER BY c DESC''',
                [])
        elif context['category'] == 'all':
            data = Entry.objects.raw(
                '''SELECT max(id) as id, category_id, release_id, person_id,
                count(*) as c FROM "interests_register_entry"
                WHERE "interests_register_entry"."release_id" = %s
                GROUP BY category_id, release_id, person_id ORDER BY c DESC''',
                [context['release_id']])
        elif context['category'] != 'all' and context['release']=='all':
            data = Entry.objects.raw(
                '''SELECT max(id) as id, category_id, release_id, person_id,
                count(*) as c FROM "interests_register_entry"
                WHERE "interests_register_entry"."category_id" = %s
                GROUP BY category_id, release_id, person_id ORDER BY c DESC''',
                [context['category_id']])
        else:
            data = Entry.objects.raw(
                '''SELECT max(id) as id, category_id, release_id, person_id,
                count(*) as c FROM "interests_register_entry"
                WHERE "interests_register_entry"."category_id" = %s
                AND "interests_register_entry"."release_id" = %s
                GROUP BY category_id, release_id, person_id ORDER BY c DESC''',
                [context['category_id'], context['release_id']])

        paginator = Paginator(data, 20)
        paginator._count = len(list(data))
        page = self.request.GET.get('page')

        try:
            data_paginated = paginator.page(page)
        except PageNotAnInteger:
            data_paginated = paginator.page(1)
        except EmptyPage:
            data_paginated = paginator.page(paginator.num_pages)

        for row in data_paginated:
            sources = models.InformationSource.objects.filter(
                content_type=release_content_type,
                object_id=row.release.id
            )
            if sources:
                source_url = sources[0].source
            else:
                source_url = ''

            row.release.source_url = source_url

        context['data'] = data_paginated

        return context

    def get_numberbysource_view(self, context):
        release_content_type = ContentType.objects.get_for_model(Release)

        #numberbysource view - number of declarations by source per category
        context['layout'] = 'numberbysource'
        if context['category']=='all' and context['release']=='all':
            data = Entry.objects.raw(
                '''SELECT max("interests_register_entrylineitem"."id") as id,
                value, count(*) as c, release_id, category_id
                FROM "interests_register_entrylineitem"
                INNER JOIN "interests_register_entry"
                ON ("interests_register_entrylineitem"."entry_id"
                = "interests_register_entry"."id")
                WHERE ("interests_register_entrylineitem"."key" = 'Source')
                GROUP BY value, release_id, category_id ORDER BY c DESC''',
                [])
        elif context['category'] == 'all':
            data = Entry.objects.raw(
                '''SELECT max("interests_register_entrylineitem"."id") as id,
                value, count(*) as c, release_id, category_id
                FROM "interests_register_entrylineitem"
                INNER JOIN "interests_register_entry"
                ON ("interests_register_entrylineitem"."entry_id"
                = "interests_register_entry"."id")
                WHERE ("interests_register_entrylineitem"."key" = 'Source'
                AND "interests_register_entry"."release_id" = %s)
                GROUP BY value, release_id, category_id ORDER BY c DESC''',
                [context['release_id']])
        elif context['release']=='all':
            data = Entry.objects.raw(
                '''SELECT max("interests_register_entrylineitem"."id") as id,
                value, count(*) as c, release_id, category_id
                FROM "interests_register_entrylineitem"
                INNER JOIN "interests_register_entry"
                ON ("interests_register_entrylineitem"."entry_id"
                = "interests_register_entry"."id")
                WHERE ("interests_register_entry"."category_id" = %s
                AND "interests_register_entrylineitem"."key" = 'Source')
                GROUP BY value, release_id, category_id ORDER BY c DESC''',
                [context['category_id']])
        else:
            data = Entry.objects.raw(
                '''SELECT max("interests_register_entrylineitem"."id") as id,
                value, count(*) as c, release_id, category_id
                FROM "interests_register_entrylineitem"
                INNER JOIN "interests_register_entry"
                ON ("interests_register_entrylineitem"."entry_id"
                = "interests_register_entry"."id")
                WHERE ("interests_register_entry"."category_id" = %s
                AND "interests_register_entrylineitem"."key" = 'Source'
                AND "interests_register_entry"."release_id" = %s)
                GROUP BY value, release_id, category_id ORDER BY c DESC''',
                [context['category_id'], context['release_id']])

        paginator = Paginator(data, 20)
        paginator._count = len(list(data))
        page = self.request.GET.get('page')

        try:
            data_paginated = paginator.page(page)
        except PageNotAnInteger:
            data_paginated = paginator.page(1)
        except EmptyPage:
            data_paginated = paginator.page(paginator.num_pages)

        for row in data_paginated:
            sources = models.InformationSource.objects.filter(
                content_type=release_content_type,
                object_id=row.release.id
            )
            if sources:
                source_url = sources[0].source
            else:
                source_url = ''

            row.release.source_url = source_url

        context['data'] = data_paginated

        return context

class SAMembersInterestsSource(TemplateView):
    template_name = "interests_register/source.html"

    def get_context_data(self, **kwargs):
        context = {}

        context['categories'] = Category.objects.filter(
            slug__in = ['sponsorships',
                        'gifts-and-hospitality',
                        'benefits',
                        'pensions'])
        context['releases'] = Release.objects.all()

        context['source'] = ''
        context['match'] = 'absolute'
        context['category'] = context['categories'][0].slug
        context['release'] = 'all'

        for key in ('source', 'match', 'category', 'release'):
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        if not context['match'] in ('absolute', 'contains'):
            context['match'] = 'absolute'

        #if a source is specified perform the search
        if context['source']!='':
            if context['match']=='absolute':
                entries = Entry.objects.filter(line_items__key='Source',
                    line_items__value=context['source'],
                    category__slug=context['category'])
            else:
                entries = Entry.objects.filter(line_items__key='Source',
                    line_items__value__contains=context['source'],
                    category__slug=context['category'])

            if context['release']!='all':
                entries = entries.filter(release__slug=context['release'])

            paginator = Paginator(entries, 25)
            page = self.request.GET.get('page')

            try:
                entries_paginated = paginator.page(page)
            except PageNotAnInteger:
                entries_paginated = paginator.page(1)
            except EmptyPage:
                entries_paginated = paginator.page(paginator.num_pages)

            #tabulate the data
            headers = ['Year', 'Person', 'Type']
            headers_index = {'Year': 0, 'Person': 1, 'Type': 2}
            data = []
            for entry in entries_paginated:
                row = ['']*len(headers)
                row[0] = entry.release.date.year
                row[1] = entry.person
                row[2] = entry.category.name

                for entrylineitem in entry.line_items.all():
                    if entrylineitem.key not in headers:
                        headers_index[entrylineitem.key] = len(headers)
                        headers.append(entrylineitem.key)
                        row.append('')

                    row[headers_index[entrylineitem.key]] = entrylineitem.value

                data.append(row)

            context['data'] = data
            context['headers'] = headers
            context['paginator'] = entries_paginated

        else:
            context['data'] = None

        return context

class SAMpAttendanceView(TemplateView):
    template_name = "south_africa/mp_attendance.html"

    def calculate_abs_percenatge(self, num, total):
        """
        Return the truncated value of num, as a percentage of total.
        """
        return int("{:.0f}".format(num / total * 100))

    def download_attendance_data(self):
        attendance_url = next_url = 'https://api.pmg.org.za/committee-meeting-attendance/summary/'

        cache = caches['pmg_api']
        results = cache.get(attendance_url)

        if results is None:
            results = []
            while next_url:
                resp = requests.get(next_url, timeout=API_REQUESTS_TIMEOUT)
                data = json.loads(resp.text)
                results.extend(data.get('results'))

                next_url = data.get('next')

            cache.set(attendance_url, results)

        # Results are returned from the API most recent first, which
        # is convenient for us.
        return results

    def get_context_data(self, **kwargs):
        data = self.download_attendance_data()

        #  A:   Absent
        #  AP:  Absent with Apologies
        #  DE:  Departed Early
        #  L:   Arrived Late
        #  LDE: Arrived Late and Departed Early
        #  P:   Present

        present_codes = ['P', 'L', 'LDE', 'DE']
        arrive_late_codes = ['L', 'LDE']
        depart_early_codes = ['DE', 'LDE']

        context = {}
        context['year'] = str(
            dateutil.parser.parse(data[0]['end_date']).year)
        context['party'] = ''

        for key in ('year', 'party'):
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        context['attendance_data'] = []
        context['years'] = []
        context['download_url'] = 'http://api.pmg.org.za/committee-meeting-attendance/data.xlsx'

        for annual_attendance in data:
            year = str(dateutil.parser.parse(annual_attendance['end_date']).year)
            context['years'].append(year)

            if year == context['year']:
                parties = set(ma['member']['party_name'] for
                    ma in annual_attendance['attendance_summary'])
                parties.discard(None)
                context['parties'] = sorted(parties)

                attendance_summary = annual_attendance['attendance_summary']
                if context['party']:
                    attendance_summary = [mbr_att for mbr_att in attendance_summary if
                        mbr_att['member']['party_name'] == context['party']]

                aggregate_total = aggregate_present = 0

                for summary in attendance_summary:
                    total = sum(v for v in summary['attendance'].itervalues())

                    present = sum(
                        v for k, v in summary['attendance'].iteritems()
                        if k in present_codes)

                    arrive_late = sum(
                        v for k, v in summary['attendance'].iteritems()
                        if k in arrive_late_codes)

                    depart_early = sum(
                        v for k, v in summary['attendance'].iteritems()
                        if k in depart_early_codes)

                    aggregate_total += total
                    aggregate_present += present

                    present_perc = self.calculate_abs_percenatge(present, total)
                    arrive_late_perc = self.calculate_abs_percenatge(arrive_late, total)
                    depart_early_perc = self.calculate_abs_percenatge(depart_early, total)

                    context['attendance_data'].append({
                        "name": summary['member']['name'],
                        "pa_url": summary['member']['pa_url'],
                        "party_name": summary['member']['party_name'],
                        "present": present_perc,
                        "absent": 100 - present_perc,
                        "arrive_late": arrive_late_perc,
                        "depart_early": depart_early_perc,
                        "total": total,
                    })

                if aggregate_total == 0:
                    # To avoid a division by zero if there's no data...
                    aggregate_attendance = -1
                else:
                    aggregate_attendance = self.calculate_abs_percenatge(aggregate_present, aggregate_total)
                context['aggregate_attendance'] = aggregate_attendance

        return context


class SAInfoBlogView(CommentArchiveMixin, InfoBlogView):
    pass
