import re

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Count, Min, Max
from django.http import Http404
from django.views.generic import RedirectView, TemplateView
from django.shortcuts import get_object_or_404, redirect

from haystack.query import RelatedSearchQuerySet
from haystack.inputs import AutoQuery

from pombola.core import models
from pombola.core.views import PersonSpeakerMappingsMixin

from slug_helpers.views import SlugRedirect

from speeches.models import Section, Speaker, Speech, Tag
from speeches.views import NamespaceMixin, SpeechView, SectionView


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
    top_section_name = 'Hansard'
    sections_to_show = 25
    section_parent_field = 'parent__parent__parent__parent'

    def get_context_data(self, **kwargs):
        context = super(SASpeechesIndex, self).get_context_data(**kwargs)
        self.page = self.request.GET.get('page')

        # Get the top level section, or 404
        top_section = get_object_or_404(
            Section, heading=self.top_section_name, parent=None)
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
            self.section_parent_field: top_section,
            'children__speech__id__isnull': False,
            'children__id__isnull': False
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
    top_section_name = 'Hansard'
    section_parent_field = 'parent__parent__parent__parent'
    sections_to_show = 15


class SACommitteeIndex(SASpeechesIndex):
    template_name = 'south_africa/hansard_index.html'
    top_section_name = 'Committee Minutes'
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
                'title': minister.title.replace('Questions asked to the ', ''),
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
                tags__name__in=['question', 'answer'],
                content=AutoQuery(context['q']),
            ).load_all()

            all_speeches = Speech.objects.all().filter(
                tags__name__in=['question', 'answer'])

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

        if len(search_result_sections) > 0:
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
            question.questionto = section.parent.heading.replace(
                'Questions asked to the ', '')
            question.questionto_slug = section.parent.slug

            #assume if there is more than one speech that the question is answered
            if len(section.speech_set.all()) > 1:
                question.answer = section \
                    .speech_set \
                    .all()[len(section.speech_set.all()) - 1]

                #extract the actual reply from the reply text (replies
                #often include the original question and other text,
                #such as a letterhead)
                text = question.answer.text.split('REPLY')
                if len(text) > 1:
                    question.answer.text = text[len(text) - 1]
                    if question.answer.text[0] == ':':
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
        speech_tag = self.kwargs['speech_tag']

        # Find (or 404) matching objects
        person = get_object_or_404(models.Person, slug=person_slug)
        tag = get_object_or_404(Tag, name=speech_tag)

        # SayIt speaker is different to core.Person, Load the speaker
        speaker = self.pombola_person_to_sayit_speaker(person)

        # Load the speeches. Pagination is done in the template
        speeches = Speech.objects \
            .filter(tags=tag, speaker=speaker) \
            .order_by('-start_date', '-start_time')

        # Store person as 'object' for the person_base.html template
        context['object'] = person
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
                # level two question sections are displayed on the
                # landing page
                redirect_url = '/question/?minister=%s&orderby=recentquestions' % \
                    (self.object.slug)
                return redirect(redirect_url)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
