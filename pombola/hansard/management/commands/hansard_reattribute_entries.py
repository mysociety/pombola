# This admin command is to save having to move Hansard Entries
# individually in the admin console, which is not fun - or particularly
# safe - when there are more than one or two of them

from dateutil import parser

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from optparse import make_option

import pombola.core.models as core_models
import pombola.hansard.models as hansard_models


class Command(BaseCommand):
    help = 'Move Hansard Entries from one Person to another'

    option_list = BaseCommand.option_list + (
        make_option("--person-from", dest="person_from", type="string",
                    help="The ID or slug of the person whose speeches you want to move",
                    metavar="PERSON-ID"),
        make_option("--person-to", dest="person_to", type="string",
                    help="The ID or slug of the person who will become associated with the speeches",
                    metavar="PERSON-ID"),
        make_option("--date-from", dest="date_from", type="string",
                    help="The date of the earliest entry to reattribute as YYYY-MM-DD (optional)"),
        make_option("--date-to", dest="date_to", type="string",
                    help="The date of the last entry to reattribute as YYYY-MM-DD (optional)"),
        make_option('--noinput',
                    action='store_false', dest='interactive', default=True,
                    help="Do NOT prompt the user for input of any kind."),
        make_option("--quiet", dest="quiet",
                    help="Suppress progress output",
                    default=False, action='store_true'))

    @transaction.atomic()
    def handle(self, *args, **options):
        if not options['person_from']:
            raise CommandError("You must specify --person-from")
        if not options['person_to']:
            raise CommandError("You must specify --person-to")
        if args:
            message = "Don't supply arguments, only --person-from and --person-to"
            raise CommandError(message)

        verbose = int(options['verbosity']) > 1

        entries_from = core_models.Person.objects.get_by_slug_or_id(options['person_from'])
        entries_to = core_models.Person.objects.get_by_slug_or_id(options['person_to'])

        if entries_from.id == entries_to.id:
            raise CommandError("--person-from and --person-to are the same")

        date_from = date_to = None
        if options['date_from']:
            date_from = parser.parse(options['date_from']).date()

        if options['date_to']:
            date_to = parser.parse(options['date_to']).date()

        entries = hansard_models.Entry.objects.filter(speaker=entries_from)
        if date_from:
            entries = entries.filter(sitting__start_date__gte=date_from)
        if date_to:
            entries = entries.filter(sitting__start_date__lte=date_to)

        message = "Going to move {count} entries from {from_name} ({from_id}) to {to_name} ({to_id})"
        message = message.format(
            count=entries.count(),
            from_name=entries_from.name,
            from_id=entries_from.id,
            to_name=entries_to.name,
            to_id=entries_to.id)
        print message

        if options['interactive']:
            answer = raw_input('Do you wish to continue? (y/[n]): ')
            if answer != 'y':
                raise Exception("Command halted by user, no changes made")

        entries.update(speaker=entries_to)
