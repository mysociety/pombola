import datetime

from collections import defaultdict

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import get_object_or_404

from pombola.core import models
from pombola.core.views import (
    OrganisationDetailView, OrganisationDetailSub, CommentArchiveMixin,
    filter_by_alphabet)


def key_position_sort_last_name(position):
    """Take a position and return a tuple for sorting it with.

    This is intended for use as the key attribute of .sort() or
    sorted() when sorting positions, so that the positions are sorted
    by the appropriate name of the associated person. It also needs to sort by
    the person's id so as to avoid mixing up people with the similar names,
    and additionally, it puts positions which are membership
    of a parliament at the top of the group of positions for a single
    person.
    """

    org_kind_slug = position.organisation.kind.slug
    title_slug = position.title and position.title.slug
    is_parliamentary = org_kind_slug == 'parliament'
    is_member = title_slug in ('member', 'delegate')

    return (
        position.person.sort_name,
        position.person.id,
        # False if the position is member or delegate to a parliament
        # (False sorts to before True)
        not(is_parliamentary and is_member),
    )


class SAOrganisationDetailView(CommentArchiveMixin, OrganisationDetailView):
    def get_context_data(self, **kwargs):
        context = super(SAOrganisationDetailView, self).get_context_data(**kwargs)

        if self.object.kind.slug == 'parliament':
            self.add_parliament_counts_to_context_data(context)

        context['organisation_kind'] = self.object.kind

        # Sort the list of positions in an organisation by an approximation
        # of their holder's last name.
        context['positions'] = sorted(
            context['positions'].currently_active(),
            key=key_position_sort_last_name,
        )

        paginator = Paginator(context['positions'], 20)
        page = self.request.GET.get('page')
        try:
            context['positions'] = paginator.page(page)
        except PageNotAnInteger:
            context['positions'] = paginator.page(1)
        except EmptyPage:
            context['positions'] = paginator.page(paginator.num_pages)

        return context

    def add_parliament_counts_to_context_data(self, context):
        # Get all the currently active positions in the house:
        positions_in_house = models.Position.objects.filter(
            organisation=self.object). \
            select_related('person').currently_active()

        # Then find the distinct people who have those positions:
        people_in_house = set(p.person for p in positions_in_house)

        # Now find all the active party memberships for those people:
        party_counts = defaultdict(int)
        for current_party_position in models.Position.objects.filter(
            title__slug='member',
            organisation__kind__slug='party',
            person__in=people_in_house).currently_active(). \
                select_related('organisation'):
            party_counts[current_party_position.organisation] += 1
        parties = sorted(party_counts.keys(), key=lambda o: o.name)
        total_people = len(people_in_house)

        # Calculate the % of the house each party occupies.
        context['parties_counts_and_percentages'] = sorted(
            [
                (party,
                 party_counts[party],
                 (float(party_counts[party]) * 100) / total_people)
                for party in parties
            ],
            key=lambda x: x[1],
            reverse=True,
        )

        context['total_people'] = total_people

    def get_template_names(self):
        if self.object.kind.slug == 'parliament':
            return ['south_africa/organisation_house.html']
        else:
            return super(SAOrganisationDetailView, self).get_template_names()


class SAOrganisationDetailSub(OrganisationDetailSub):
    sub_page = None

    def add_sub_page_context(self, context):
        pass

    def get_context_data(self, *args, **kwargs):
        context = super(SAOrganisationDetailSub, self).get_context_data(
            *args, **kwargs)

        self.add_sub_page_context(context)

        context['sorted_positions'] = sorted(
            context['sorted_positions'],
            key=key_position_sort_last_name)

        return context


class SAOrganisationDetailSubParty(SAOrganisationDetailSub):
    sub_page = 'party'

    def add_sub_page_context(self, context):
        context['party'] = get_object_or_404(
            models.Organisation, slug=self.kwargs['sub_page_identifier'])

        # We need to find any position where someone was a member
        # of the organisation and that membership overlapped with
        # their membership of the party, and mark whether that
        # time includes the current date.
        current_date = str(datetime.date.today())
        params = [
            current_date, current_date, current_date, current_date,
            self.object.id, context['party'].id]
        # n.b. "hp" = "house position", "pp" = "party position"
        all_positions = models.raw_query_with_prefetch(
            models.Position,
            '''
SELECT
    hp.*,
    (hp.sorting_start_date <= %s AND
     hp.sorting_end_date_high >= %s AND
     pp.sorting_start_date <= %s AND
     pp.sorting_end_date_high >= %s) AS current
FROM core_position hp, core_position pp
  WHERE hp.person_id = pp.person_id
    AND hp.organisation_id = %s
    AND pp.organisation_id = %s
    AND hp.sorting_start_date <= pp.sorting_end_date_high
    AND pp.sorting_start_date <= hp.sorting_end_date_high
''',
            params,
            (('person', ('alternative_names', 'images')),
             ('place', ()),
             ('organisation', ()),
             ('title', ()))
        )

        current_person_ids = set(p.person_id for p in all_positions if p.current)

        if self.request.GET.get('all'):
            context['sorted_positions'] = all_positions
        elif self.request.GET.get('historic'):
            context['historic'] = True
            context['sorted_positions'] = [
                p for p in all_positions if p.person_id not in current_person_ids
            ]
        else:
            # Otherwise we're looking current positions:
            context['historic'] = True
            context['sorted_positions'] = [
                p for p in all_positions if p.current
            ]


class SAOrganisationDetailSubPeople(SAOrganisationDetailSub):
    sub_page = 'people'

    def add_sub_page_context(self, context):
        all_positions = self.object.position_set.all()

        context['historic_filter'] = False
        context['all_filter'] = False
        context['current_filter'] = False

        if self.request.GET.get('all'):
            context['all_filter'] = True
            context['sorted_positions'] = all_positions
        elif self.request.GET.get('historic'):
            context['historic_filter'] = True
            #FIXME - limited to members and delegates so that current members who are no longer officials are not displayed, but this
            #means that if a former member was an official this is not shown
            context['sorted_positions'] = all_positions.filter(
                Q(title__slug='member') | Q(title__slug='delegate')).currently_inactive()
        elif self.request.GET.get('historic'):
            context['historic_filter'] = True
            context['sorted_positions'] = all_positions.currently_inactive()
        else:
            context['current_filter'] = True
            context['sorted_positions'] = all_positions.currently_active()

        context['sorted_positions'], extra_context = \
            filter_by_alphabet(
                self.kwargs.get('person_prefix'), context['sorted_positions'])
        context.update(extra_context)

        if self.object.slug == 'ncop':
            context['membertitle'] = 'delegate'
        else:
            context['membertitle'] = 'member'
