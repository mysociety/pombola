import re

from django.db.models import Count, Q
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from pombola.core import models


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

        # find individuals who appear to have switched party
        context['people_new_party'] = []
        people = models.Person.objects \
            .filter(
                position__organisation__kind__slug='party',
                position__title__slug='member') \
            .annotate(
                num_parties=Count('position')).filter(num_parties__gt=1)

        for person in people:
            #check whether the person is a candidate - there is probably be a cleaner way to do this in the initial query
            person_list = person.position_set.all().filter(
                organisation__slug__contains='election-list-2014')
            if person_list:
                context['people_new_party'].append({
                    'person': person,
                    'current_positions': person.position_set.all().filter(
                        organisation__kind__slug='party').currently_active(),
                    'former_positions': person.position_set.all().filter(
                        organisation__kind__slug='party').currently_inactive(),
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
        context = super(
            SAElectionPartyCandidatesView, self).get_context_data(**kwargs)

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
        election_list = get_object_or_404(
            models.Organisation,
            slug=election_list_name
        )

        candidates = election_list.position_set.select_related('title').all()

        context['party_election_list'] = sorted(
            candidates,
            key=lambda x: int(re.match('\d+', x.title.name).group())
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
                province_slug = province_slug.replace(
                    party_election_lists_endwith, '')
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
        context = super(
            SAElectionProvinceCandidatesView, self).get_context_data(**kwargs)

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

            candidates = sorted(
                candidate_list,
                key=lambda x: int(re.match('\d+', x.title.name).group())
            )

            context['province_election_lists'].append({
                'party': party,
                'candidates': candidates
            })

        # Get the province object, so we can use its details
        province_kind = models.PlaceKind.objects.get(slug='province')
        context['province'] = get_object_or_404(models.Place,
            kind=province_kind,
            slug=province_name)

        return context
