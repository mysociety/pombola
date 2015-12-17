from optparse import make_option

from django.core.management.base import NoArgsCommand
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Position


def yyyymmdd_to_approx(yyyymmdd):
    year, month, day = map(int, yyyymmdd.split('-'))
    return ApproximateDate(year, month, day)

class Command(NoArgsCommand):

    help = 'End positions which meet the criteria'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),

        make_option('--end-date',     dest="end-date",     help="The end date to apply to matching positions"),

        make_option('--title',             dest="title",             help="The title to match positions"),
        make_option('--organisation',      dest="organisation",      help="The organisation to match positions"),
        make_option('--organisation-kind', dest="organisation-kind", help="The kind of organisation to match positions")
    )

    def handle_noargs(self, **options):

        positions = Position.objects

        if options['title']:
            print 'Title filter: ' + options['title']
            positions = positions.filter(title__slug = options['title'])

        if options['organisation']:
            print 'Organisation filter: ' + options['organisation']
            positions = positions.filter(organisation__slug = options['organisation'])

        if options['organisation-kind']:
            print 'Organisation kind filter: ' + options['organisation-kind']
            positions = positions.filter(organisation__kind__slug = options['organisation-kind'])

        end_date = yyyymmdd_to_approx(options['end-date'])

        for position in positions.currently_active():
            print "  Ending %s" % position
            position.end_date = end_date
            if options['commit']:
                position.save()

        print 'Ended a total of ' + str(positions.count()) + ' positions.'
