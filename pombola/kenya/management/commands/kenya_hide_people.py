from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.db.models import Q

from pombola.core.models import Person


class Command(NoArgsCommand):

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        for possible_person in Person.objects.filter(
            Q(position__title__slug='governor') |
            Q(position__title__slug__contains='aspirant') |
            Q(position__title__slug='ward-representative')):
            interesting_positions = possible_person.position_set.filter(
                Q(title__slug='member-national-assembly', organisation__slug='parliament') |
                Q(title__slug='mp', organisation__slug='parliament') |
                Q(title__slug='aspirant-president', organisation__slug='republic-of-kenya') |
                Q(title__slug='deputy-president-aspirant', organisation__slug='republic-of-kenya') |
                Q(title__slug='president', organisation__slug='republic-of-kenya') |
                Q(title__slug='vice-president', organisation__slug='cabinet') |
                Q(title__slug='vice-president-of-kenya', organisation__slug='cabinet') |
                Q(organisation__slug='cabinet') |
                Q(title__slug='senator') |
                Q(title__name='Minister')
            )
            if interesting_positions:
                print "Ignoring", possible_person, "since they have the following positions:"
                for p in interesting_positions:
                    print "  ", p
            else:
                if options['commit']:
                    print "Hiding", possible_person, "; all their positions:"
                    possible_person.hidden = True
                    possible_person.save()
                else:
                    print "Would hide", possible_person, " (no --commit); all their positions:"
                for p in possible_person.position_set.all():
                    print "  ", p
