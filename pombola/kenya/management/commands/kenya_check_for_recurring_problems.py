import sys

from urlparse import urljoin

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.transaction import commit, set_autocommit

from pombola.core.models import (
    Organisation, Position, PositionTitle, approximate_date_to_date)

def admin_url(o):
    return urljoin('http://info.mzalendo.com', o.get_admin_url())


def existing_overlapping_party_position(position, correct_title):
    """Check if there is already an overlapping party position"""
    party = position.organisation
    assert party.kind.name == 'Political Party'
    person = position.person
    earliest_start_date = approximate_date_to_date(
        position.start_date, 'earliest')
    latest_end_date = approximate_date_to_date(
        position.end_date, 'latest')
    for existing in Position.objects.filter(
            person=person,
            title=correct_title,
            organisation=party,
    ):
        if existing.approximate_date_overlap(
                earliest_start_date,
                latest_end_date):
            return True
    return False


class ProblemFromQuerySet(object):

    """A class to represent simple types of problem to fix"""

    def __init__(self, qs, fix_kwargs):
        self.qs = qs
        self.model = qs.model
        self.fix_kwargs = fix_kwargs

    def count(self):
        return self.qs.count()

    def itermodels(self):
        for o in self.qs:
            yield o

    def fix_problems(self):
        return self.qs.update(**self.fix_kwargs)


class ParliamentPositionProblem(ProblemFromQuerySet):

    """A class for fixing Kenyan parliamentary organisation errors"""

    def __init__(self, qs, parliament_organisation):
        super(ParliamentPositionProblem, self).__init__(qs, None)
        self.parliament_organisation = parliament_organisation

    def fix_problems(self):
        fixed = 0
        member_pt = PositionTitle.objects.get(name='Member')
        for p in self.qs:
            print "  Fixing position", p
            # There are really two cases here; one where the position
            # just represents the membership of parliament, and one
            # where it represents the party that they were a member of
            # while a member of parliament. We want to make sure that
            # both of the positions are still represented afterwards.
            # (In the future these will hopefully both be represented by
            # single Position with an equivalent of Popolo memberships'
            # on_behalf_of property.)
            org = p.organisation
            org_kind = org.kind
            if org_kind.name == 'Political Party':
                if not existing_overlapping_party_position(p, member_pt):
                    new_position = Position.objects.create(
                        person=p.person,
                        organisation=org,
                        start_date=p.start_date,
                        end_date=p.end_date,
                        title=member_pt)
                    print "    Creating a party position for the same period:", new_position
            elif org.name in ('REPUBLIC OF KENYA', 'National Assembly'):
                # This is fine, we're just going to change the
                # organisation.
                pass
            else:
                msg = "Unknown organisation {0} of kind {1}"
                raise Exception(msg.format(org, org_kind))
            p.organisation = self.parliament_organisation
            p.save()
            fixed += 1
        return fixed


class Command(BaseCommand):

    help = 'Check for recurring data problems in Mzalendo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            help='Attempt to fix the problems as well as finding them',
            action='store_true',
            default=False)

    def handle(*args, **options):

        problem_types = [
            ParliamentPositionProblem(
                Position.objects.filter(
                    title__name='Member of the National Assembly',
                ).exclude(
                    organisation__name='Parliament',
                ),
                Organisation.objects.get(name='Parliament')),
            ParliamentPositionProblem(
                Position.objects.filter(
                    Q(title__name='Member of Parliament') |
                    Q(title__name='Nominated Member of Parliament')
                ).exclude(
                    organisation__name='Parliament'
                ),
                Organisation.objects.get(name='Parliament')),
        ]

        problems_found = 0
        set_autocommit(False)
        try:
            for problem_type in problem_types:
                problem_count = problem_type.count()
                if problem_count:
                    msg = "The following {0} instances of {1} were broken:"
                    print msg.format(problem_count, problem_type.model.__name__)
                    for o in problem_type.itermodels():
                        print "  {0}: {1} {2}".format(o.id, o, admin_url(o))
                    number_fixed = problem_type.fix_problems()
                    print "Fixed {0} rows".format(number_fixed)
                problems_found += problem_count
        finally:
            if options['fix']:
                commit()
            elif problems_found > 0:
                print "No changes committed, since --fix wasn't specified"
        if problems_found > 0:
            sys.exit(1)
