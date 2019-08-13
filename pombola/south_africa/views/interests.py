import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.views.generic import TemplateView

from django_date_extensions.fields import ApproximateDate

from pombola.core import models
from pombola.interests_register.models import Release, Category, Entry


class SAMembersInterestsIndex(TemplateView):
    template_name = "interests_register/index.html"

    def get_context_data(self, **kwargs):
        context = {}

        primary_party_slugs = [
            'acdp', 'agang-sa', 'aic', 'anc', 'apc', 'azapo', 'cope',
            'da', 'eff', 'ff', 'id', 'ifp', 'mf', 'nfp', 'pac', 'udm']
        other_parties = (models.Organisation.objects
            .filter(kind__slug='party')
            .exclude(slug__in=primary_party_slugs))
        other_party_slugs = [
            p.slug for p in other_parties]

        # Get the data for the form
        context['categories'] = Category.objects.all()
        context['parties'] = models.Organisation.objects.filter(
            kind__slug='party',
            slug__in=primary_party_slugs)
        context['releases'] = Release.objects.all().order_by('-date')

        # Set filter values
        for key in ('display', 'category', 'party', 'release'):
            context[key] = 'all'
            if key == 'release':
                # Default to latest release
                context[key] = context['releases'].first().slug
            if key in self.request.GET:
                context[key] = self.request.GET[key]

        if context['party'] != 'all':
            if context['party'] == 'other':
                context['party_slug_filter'] = other_party_slugs
            else:
                context['party_slug_filter'] = [context['party']]

        try:
            if context['release'] != 'all':
                release = Release.objects.get(slug=context['release'])
                context['release_id'] = release.id

            if context['category'] != 'all':
                categorylookup = Category.objects.get(
                    slug=self.request.GET['category'])
                context['category_id'] = categorylookup.id
        except ObjectDoesNotExist:
            return context

        # Complete view - declarations for multiple people in multiple categories
        if context['display'] == 'all' and context['category'] == 'all':
            context = self.get_complete_view(context)

        # Section view - data for multiple people in different categories
        elif context['display'] == 'all' and context['category'] != 'all':
            context = self.get_section_view(context)

        # numberbyrepresentative view - number of declarations per person per category
        elif context['display'] == 'numberbyrepresentative':
            context = self.get_number_by_representative_view(context)

        # numberbysource view - number of declarations by source per category
        elif context['display'] == 'numberbysource':
            context = self.get_numberbysource_view(context)

        return context

    def get_complete_view(self, context):
        release_content_type = ContentType.objects.get_for_model(Release)

        # Complete view - declarations for multiple people in multiple categories
        context['layout'] = 'complete'

        when = datetime.date.today()
        now_approx = repr(
            ApproximateDate(year=when.year, month=when.month, day=when.day))

        people = Entry.objects.order_by(
            'person__legal_name',
            'release__date'
        ).distinct(
            'person__legal_name',
            'release__date'
        )

        if context['release'] != 'all':
            people = people.filter(release=context['release_id'])

        if context['party'] != 'all':
            people = people.filter(
                Q(person__position__end_date__gte=now_approx) |
                Q(person__position__end_date=''),
                person__position__organisation__slug__in=context['party_slug_filter'],
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

        # Tabulate the data
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
                    row = [''] * len(headers)

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

        # Section view - data for multiple people in different categories
        context['layout'] = 'section'

        when = datetime.date.today()
        now_approx = repr(
            ApproximateDate(year=when.year, month=when.month, day=when.day))

        entries = Entry.objects.select_related(
            'person',
            'category'
        ).all().filter(
            category__id=context['category_id']
        ).order_by(
            'person',
            'category'
        )

        if context['release'] != 'all':
            entries = entries.filter(release=context['release_id'])

        if context['party'] != 'all':
            entries = entries.filter(
                Q(person__position__end_date__gte=now_approx) |
                Q(person__position__end_date=''),
                person__position__organisation__slug__in=context['party_slug_filter'],
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

            row = [''] * len(headers)
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

        # numberbyrepresentative view - number of declarations per person per category
        context['layout'] = 'numberbyrepresentative'

        # Custom sql used as:
        # Entry.objects.values('category', 'release', 'person').annotate(c=Count('id')).order_by('-c')
        # ... returns a ValueQuerySet with foreign keys, not model instances
        if context['category'] == 'all' and context['release'] == 'all':
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
        elif context['category'] != 'all' and context['release'] == 'all':
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

        context['categories'] = Category.objects.filter(
            slug__in=['sponsorships',
                      'gifts-and-hospitality',
                      'benefits',
                      'pensions'])

        # numberbysource view - number of declarations by source per category
        context['layout'] = 'numberbysource'
        if context['category'] == 'all' and context['release'] == 'all':
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
        elif context['release'] == 'all':
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
            slug__in=['sponsorships',
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

        # If a source is specified perform the search
        if context['source'] != '':
            if context['match'] == 'absolute':
                entries = Entry.objects.filter(
                    line_items__key='Source',
                    line_items__value=context['source'],
                    category__slug=context['category'])
            else:
                entries = Entry.objects.filter(
                    line_items__key='Source',
                    line_items__value__contains=context['source'],
                    category__slug=context['category'])

            if context['release'] != 'all':
                entries = entries.filter(release__slug=context['release'])

            paginator = Paginator(entries, 25)
            page = self.request.GET.get('page')

            try:
                entries_paginated = paginator.page(page)
            except PageNotAnInteger:
                entries_paginated = paginator.page(1)
            except EmptyPage:
                entries_paginated = paginator.page(paginator.num_pages)

            # Tabulate the data
            headers = ['Year', 'Person', 'Type']
            headers_index = {'Year': 0, 'Person': 1, 'Type': 2}
            data = []
            for entry in entries_paginated:
                row = [''] * len(headers)
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
