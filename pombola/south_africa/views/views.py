from __future__ import division
from .constants import API_REQUESTS_TIMEOUT

import datetime
import dateutil
import json
import warnings

import requests

from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from info.views import InfoBlogView

from info.views import InfoPageView

from pombola.core import models
from pombola.core.views import CommentArchiveMixin

from pombola.interests_register.models import Release, Category, Entry
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_date_extensions.fields import ApproximateDate


class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'


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
