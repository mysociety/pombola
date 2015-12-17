import sys
from optparse import make_option

from django.core.management.base import NoArgsCommand

from pombola.core.models import Person

from iebc_api import maybe_save, normalize_name


class Command(NoArgsCommand):
    help = 'Normalize the legal_name and other_names for each Person'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):
        for person in Person.objects.all():
            legal_name = person.legal_name
            other_names = person.other_names
            normalized_legal_name = normalize_name(legal_name)
            normalized_other_names = normalize_name(other_names)
            if (legal_name != normalized_legal_name) or (other_names != normalized_other_names):
                print >> sys.stderr, "Found difference(s):"
                if legal_name != normalized_legal_name:
                    print >> sys.stderr, "  ", legal_name, "should be", normalized_legal_name
                if other_names != normalized_other_names:
                    print >> sys.stderr, "  ", other_names, "should be", normalized_other_names
                person.legal_name = normalized_legal_name
                person.other_names = normalized_other_names
                maybe_save(person, **options)
