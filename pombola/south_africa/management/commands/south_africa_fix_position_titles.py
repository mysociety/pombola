# Fixup PositionTitles on Party memberships in ZA.
#
# Some positions were created with the PositionTitle of "Party Member", that
# title is obsolete and should just be "Member". We just check that the
# type of organisation a Person is a Member of is party when we want to
# know about party membership.

from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction

from pombola.core.models import PositionTitle, Position, OrganisationKind


class Command(NoArgsCommand):
    """Fix South African PositionTitles"""

    help = 'Replace "Party Member" PositionTitles with just "Member", then delete the "Party Member" PositionTitle altogether'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_noargs(self, **options):
        party_member = PositionTitle.objects.get(name="Party Member")
        member = PositionTitle.objects.get(name="Member")
        party = OrganisationKind.objects.get(name="Party")

        with transaction.commit_manually():
            positions = Position.objects.filter(
                title=party_member,
                )
            positions_at_parties = positions.filter(
                organisation__kind=party
            )
            no_non_party_positions = (positions.count() == positions_at_parties.count())
            assert no_non_party_positions, """There are some Party Member
                positions that point to an organisation that is not a party,
                please manually remove these before running this command"""

            updated = positions.update(title=member)
            self.stdout.write("Will update {0} Positions\n".format(updated))

            party_member.delete()

            if options['commit']:
                transaction.commit()
                self.stdout.write("Updated {0} Positions\n".format(updated))
                self.stdout.write("Deleted the Party Member PositionTitle\n")
            else:
                transaction.rollback()



