from __future__ import unicode_literals

from itertools import groupby
import re

from pombola.core.models import Position

from django.db.models import Q
from django.views.generic import TemplateView


FIRST_ALPHABETIC_CHARACTER_RE = re.compile(r'(\w)', re.UNICODE)


def get_sort_letter(position):
    name = position.person.sort_name
    return FIRST_ALPHABETIC_CHARACTER_RE.search(name).group(1).upper()


class SAMembersView(TemplateView):

    template_name = 'south_africa/mp_profiles.html'

    def get_context_data(self, **kwargs):
        context = super(SAMembersView, self).get_context_data(**kwargs)
        positions = Position.objects.filter(
            Q(title__slug='member', organisation__kind__slug='parliament') |
            Q(organisation__slug='ncop')) \
            .currently_active() \
            .select_related(
                'organisation__kind', 'person') \
            .prefetch_related(
                'person__alternative_names',
                'person__images') \
            .order_by('person__sort_name')
        # It's easy to accidentally evaluate the lazy grouper and then
        # not be able to get at the positions, so turn them into lists
        # here:
        context['grouped_by_sort_letter'] = [
            (letter, list(positions_for_that_letter))
            for letter, positions_for_that_letter in
            groupby(positions, get_sort_letter)]
        return context
