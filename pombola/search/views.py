from datetime import datetime
import re
import sys
import simplejson

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings

from django.views.generic import TemplateView

from pombola.core import models

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery, Raw

from pygeolib import GeocoderError
from sorl.thumbnail import get_thumbnail
from .geocoder import geocoder


class SearchBaseView(TemplateView):

    top_hits_under = {
        'persons': 2,
        'blog_posts': 2,
    }

    results_per_page = 20

    def __init__(self, *args, **kwargs):
        super(SearchBaseView, self).__init__(*args, **kwargs)
        self.section_ordering = ['persons', 'position_titles', 'organisations', 'places']
        self.search_sections = {
            'persons': {
                'model': models.Person,
                'title': 'People',
                'exclude': {'hidden': True},
            },
            'position_titles': {
                'model': models.PositionTitle,
                'title': 'Positions',
            },
            'organisations': {
                'model': models.Organisation,
                'title': 'Organisations',
            },
            'places': {
                'model': models.Place,
                'title': 'Places',
            },
        }
        if settings.ENABLED_FEATURES['speeches']:
            from speeches.models import Speech
            self.section_ordering.append('speeches')
            self.search_sections['speeches'] = {
                'model': Speech,
                'title': 'Speeches',
            }
        if settings.ENABLED_FEATURES['hansard']:
            from pombola.hansard.models import Entry
            self.section_ordering.append('hansard')
            self.search_sections['hansard'] = {
                'model': Entry,
                'title': 'Hansard',
            }
        if 'info' in settings.INSTALLED_APPS:
            from info.models import InfoPage
            self.section_ordering += ['blog_posts', 'info_pages']
            self.search_sections['blog_posts'] = {
                'model': InfoPage,
                'title': 'Blog Posts',
                'filter': {
                    'kwargs': {
                        'kind': 'blog'
                    }
                },
            }
            self.search_sections['info_pages'] = {
                'model': InfoPage,
                'title': 'Info Pages',
                'filter': {
                    'kwargs': {
                        'kind': 'page'
                    }
                },
            }

        # Remove any sections that are configured to be excluded
        for section in settings.EXCLUDE_FROM_SEARCH:
            if section in self.search_sections:
                del self.search_sections[section]
            if section in self.section_ordering:
                self.section_ordering.remove(section)

    def parse_params(self):
        # Check that the specified section is one we actually know
        # about
        self.section = self.request.GET.get('section')
        if self.section == 'global':
            self.section = None
        self.query = self.request.GET.get('q', '')
        self.page = self.request.GET.get('page')
        self.order = self.request.GET.get('order')
        self.start_date_range = self.request.GET.get('start')
        self.start_date_range = self.format_search_date(self.start_date_range)
        self.end_date_range = self.request.GET.get('end')
        self.end_date_range = self.format_search_date(self.end_date_range)

    def format_search_date(self, search_date):
        if search_date:
            try:
                formatted_date = datetime.strptime(search_date, '%Y-%m-%d')
                return formatted_date.date()
            except ValueError:
                return None
        else:
            return None

    def get(self, request, *args, **kwargs):
        self.parse_params()
        if self.section and (self.section not in self.search_sections):
            message = 'The section {0} was not known'
            return HttpResponseBadRequest(message.format(self.section))
        return super(SearchBaseView, self).get(request, *args, **kwargs)

    def get_template_names(self):
        if self.section:
            return ['search/section_search.html']
        else:
            return ['search/global_search.html']

    def get_paginated_results(self, paginator):
        try:
            results = paginator.page(self.page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)
        return results

    # This applies the 'fuzzy' query string modifier to queries which
    # entirely contain [a-zA-Z0-9 ] characters. See:
    # https://www.elastic.co/guide/en/elasticsearch/reference/0.90/query-dsl-query-string-query.html
    def generate_fuzzy_query_object(self, query_string):
        if re.match("^[a-z0-9 ]*$", query_string, re.IGNORECASE):
            query_string = ' '.join(word + '~1' for word in query_string.split(' '))
            query_object = Raw(query_string)
        else:
            query_object = AutoQuery(query_string)

        return query_object

    def get_global_context(self, context):
        # Find all the models to search over...
        models = set(
            self.search_sections[section]['model']
            for section in self.search_sections
        )

        show_top_hits = (self.page == '1' or not self.page)

        top_hits_ids = []

        if show_top_hits:
            context['top_hits'] = []
            for section, max_for_top_hits in SearchBaseView.top_hits_under.items():
                data = self.get_section_data(section)
                if data['results_count'] <= max_for_top_hits:
                    context['top_hits'] += data['results']
            top_hits_ids = set(r.id for r in context['top_hits'])

        sqs = SearchQuerySet().models(*list(models))
        # Exclude anything that will already have been shown in the top hits:
        for top_hit_id in top_hits_ids:
            sqs = sqs.exclude(id=top_hit_id)
        sqs = sqs. \
            exclude(hidden=True). \
            filter(content=self.generate_fuzzy_query_object(self.query)). \
            highlight()

        if self.start_date_range:
            sqs = sqs.filter(start_date__gte=self.start_date_range)

        if self.end_date_range:
            sqs = sqs.filter(start_date__lte=self.end_date_range)

        if self.order == 'date':
            sqs = sqs.order_by('-start_date')

        context['paginator'] = Paginator(sqs, self.results_per_page)
        context['page_obj'] = self.get_paginated_results(context['paginator'])
        return context

    def get_section_context(self, context, section):
        data = self.get_section_data(section)
        context['paginator'] = Paginator(data['results'], self.results_per_page)
        context['page_obj'] = self.get_paginated_results(context['paginator'])
        return context

    def get_date_range_context(self, context):
        if self.start_date_range:
            context['search_start_date_range'] = self.start_date_range.strftime("%Y-%m-%d")
        if self.end_date_range:
            context['search_end_date_range'] = self.end_date_range.strftime("%Y-%m-%d")

    def get_context_data(self, **kwargs):
        context = super(SearchBaseView, self).get_context_data(**kwargs)
        context['query'] = self.query
        context['order'] = self.order
        context['section'] = self.section

        self.get_date_range_context(context)

        if self.section:
            context['section_title'] = self.search_sections[self.section]['title']
        context['form_options'] = [('global', 'All', (not self.section))]
        query_dict = self.request.GET.copy()
        if 'page' in query_dict:
            del query_dict['page']
        context['query_string'] = query_dict.urlencode()

        for section in self.section_ordering:
            context['form_options'].append(
                (section,
                 self.search_sections[section]['title'],
                 section == self.section)
            )
        if not self.query:
            return context

        if self.section:
            return self.get_section_context(context, self.section)
        else:
            return self.get_global_context(context)

    def get_section_data(self, section):
        defaults = self.search_sections[section]
        extra_filter = defaults.get('filter', {})
        filter_args = extra_filter.get('args', [])
        filter_kwargs = extra_filter.get('kwargs', {})
        extra_exclude = defaults.get('exclude', {})
        query = SearchQuerySet().models(defaults['model'])
        if extra_exclude:
            query = query.exclude(**extra_exclude)

        query = query.filter(
            content=self.generate_fuzzy_query_object(self.query),
            *filter_args,
            **filter_kwargs
        )

        if self.start_date_range:
            query = query.filter(start_date__gte=self.start_date_range)

        if self.end_date_range:
            query = query.filter(start_date__lte=self.end_date_range)

        if self.order == 'date':
            query = query.order_by('-start_date')

        result = defaults.copy()
        result['results'] = query.highlight()
        result['results_count'] = result['results'].count()
        result['section'] = section
        result['section_dashes'] = section.replace('_', '-')
        return result

if settings.ENABLED_FEATURES['hansard']:
    class HansardSearchView(TemplateView):
        template_name = "search/hansard.html"
        results_per_page = 20

        def parse_params(self):
            self.query = self.request.GET.get('q', '')
            self.page = self.request.GET.get('page')
            self.order = self.request.GET.get('order')
            self.speaker = self.request.GET.get('speaker', '')

        def get_data(self):
            from pombola.hansard.models import Entry
            defaults = {
                'model': Entry,
                'title': 'Hansard',
            }
            data_query = SearchQuerySet().models(defaults['model'])
            data_query = data_query.filter(
                content=AutoQuery(self.query)
            )
            if self.order == 'date':
                data_query = data_query.order_by('-start_date')
            if self.order == 'adate':
                data_query = data_query.order_by('start_date')
            if self.speaker != '':
                data_query = data_query.filter(speaker_names=self.speaker)

            result = defaults.copy()
            result['results'] = data_query.highlight()
            result['results_count'] = result['results'].count()
            return result

        def get_paginated_results(self, sqs):
            paginator = Paginator(sqs, self.results_per_page)
            try:
                results = paginator.page(self.page)
            except PageNotAnInteger:
                results = paginator.page(1)
            except EmptyPage:
                results = paginator.page(paginator.num_pages)
            return results, paginator

        def get_context_data(self, **kwargs):
            self.parse_params()
            context = super(HansardSearchView, self).get_context_data(**kwargs)
            context['query'] = self.query
            context['order'] = self.order
            context['speaker'] = self.speaker

            query_dict = self.request.GET.copy()
            if 'page' in query_dict:
                del query_dict['page']
            context['query_string'] = query_dict.urlencode()
            if not self.query:
                return context

            data = self.get_data()
            page_obj, paginator = self.get_paginated_results(data['results'])
            context['page_obj'] = page_obj
            context['paginator'] = paginator

            return context


class GeocoderView(TemplateView):
    template_name = "search/location.html"

    # This should really be set somewhere is the app's config.
    # See https://github.com/mysociety/pombola/issues/829
    country_app_to_alpha2_mapping = {
        # http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
        "south_africa": "za",
        "kenya":        "ke",
    }

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(GeocoderView, self).get_context_data()

        country_alpha2 = self.country_app_to_alpha2_mapping.get(settings.COUNTRY_APP)

        if not country_alpha2:
            # search can still go ahead, but it will not be restricted to the country expected
            sys.stderr.write("Need to add country code for {0} to 'search.views.GeocoderView'".format(settings.COUNTRY_APP))

        query = self.request.GET.get('q')
        if query:
            context['query'] = query
            try:
                context['geocoder_results'] = geocoder(country=country_alpha2, q=query)
            except GeocoderError as e:
                if e.status == GeocoderError.G_GEO_ZERO_RESULTS:
                    context['geocoder_results'] = []
                else:
                    raise

        return context


known_kinds = {
    'person': models.Person,
    'place':  models.Place,
}

def places_ordered_by_session(place_a, place_b):
    """Return True if both places have sessions and place_b's is later"""
    a_session = place_a.parliamentary_session
    b_session = place_b.parliamentary_session
    if not (a_session and b_session):
        return False
    return a_session.end_date < b_session.end_date

def remove_duplicate_places(response_data):
    """Remove all but the newest of places with indistinguishable labels

    We have a slightly unpleasant problem where consituencies that
    have the same name from one parliament to the next appear twice
    with exactly the same label - people get confused if they pick the
    old one and don't find their aspirants.  We could exclude all
    older constituencies, but for people who don't know that their
    constituency name has changed, it's potentially useful to still
    have the old name returned in results.  So, look for duplicate
    labels, and (if they're places) delete the one from the older
    parliamentary session."""

    indices_to_remove = []
    previous_label_index = {}

    for i, result in enumerate(response_data):
        this_label = (result['name'], result['extra_data'])
        this_object = result['object']
        if (this_label in previous_label_index) and type(this_object) == models.Place:
            previous_i = previous_label_index[this_label]
            if places_ordered_by_session(response_data[previous_i]['object'], this_object):
                indices_to_remove.append(previous_i)
                previous_label_index[this_label] = i
            else:
                indices_to_remove.append(i)
        else:
            previous_label_index[this_label] = i

    # Now remove those marked for deletion:
    indices_to_remove.sort(reverse=True)
    for index_to_remove in indices_to_remove:
        del response_data[index_to_remove]

def autocomplete(request):
    """Return autocomplete JSON results"""

    term = request.GET.get('term','').strip()
    response_data = []

    if len(term):

        # Does not work - probably because the FLAG_PARTIAL is not set on Xapian
        # (trying to set it in settings.py as documented appears to have no effect)
        # sqs = SearchQuerySet().autocomplete(name_auto=term)

        # Split the search term up into little bits
        terms = re.split(r'\s+', term)

        # Build up a query based on the bits
        sqs = SearchQuerySet()
        for bit in terms:
            # print "Adding '%s' to the '%s' query" % (bit,term)
            sqs = sqs.filter_and(
                name_auto__startswith = sqs.query.clean( bit )
            )
        sqs = sqs.exclude(hidden=False)

        # If we have a kind then filter on that too
        model_kind = request.GET.get('model', None)
        if model_kind:
            model = known_kinds.get(model_kind, None)
            if model:
                sqs = sqs.models(model)
        else:
            sqs = sqs.models(
                models.Person,
                models.Organisation,
                models.Place,
                models.PositionTitle,
            )

        # collate the results into json for the autocomplete js
        for result in sqs.all()[0:10]:

            o = result.object
            css_class = o.css_class()

            extra_autocomplete_data = None
            if hasattr(o, 'extra_autocomplete_data'):
                extra_autocomplete_data = o.extra_autocomplete_data

            image_url = None
            if hasattr(o, 'primary_image'):
                image = o.primary_image()
                if image:
                    image_url = get_thumbnail(image, '16x16', crop="center").url

            if not image_url:
                image_url = "/static/images/" + css_class + "-16x16.jpg"

            response_data.append({
                'url': o.get_absolute_url(),
                'name': o.name,
                'image_url': image_url,
                'extra_data': extra_autocomplete_data,
                'type': css_class,
                'value': o.name,
                'object': o
            })

    remove_duplicate_places(response_data)

    # Remove the 'object' elements before returning the response:
    for d in response_data:
        del d['object']

    # send back the results as JSON
    return HttpResponse(
        simplejson.dumps(response_data),
        content_type='application/json',
    )
