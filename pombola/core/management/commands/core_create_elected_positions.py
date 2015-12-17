# This command is intended to help with these issues:
#
#   https://github.com/mysociety/pombola/issues/599
#   https://github.com/mysociety/pombola/issues/600
#   https://github.com/mysociety/pombola/issues/601
#   https://github.com/mysociety/pombola/issues/602
#
# This script takes arguments are passed in on the command line.

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person, Position, PositionTitle, Place, Organisation


def yyyymmdd_to_approx(yyyymmdd):
    year, month, day = map(int, yyyymmdd.split('-'))
    return ApproximateDate(year, month, day)

class Command(NoArgsCommand):

    help = 'create new position for election winners, end aspirant positions'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),

        make_option('--place',                help="The Place slug that the positions are linked to"),
        make_option('--elected-organisation', help="The Organisation slug that the person is elected to"),
        make_option('--aspirant-title',       help="The PositionTitle slug for aspirants"),
        make_option('--aspirant-end-date',    help="The end date to apply to matching positions"),
        make_option('--elected-person',       help="The Person slug of the winner"),
        make_option('--elected-title',        help="The PositionTitle slug for elected position"),
        make_option('--elected-subtitle',     help="Optional subtitle for elected position"),
        make_option('--elected-start-date',   help="The start date to apply to matching positions"),        
    )

    def handle_noargs(self, **options):
        
        print "Looking at '%s' in '%s'" % (options['elected_person'], options['place'] )

        # load up the place, org and positions
        place                 = Place.objects.get(slug=options['place'])
        organisation          = Organisation.objects.get(slug=options['elected_organisation'])
        aspirant_pos_title    = PositionTitle.objects.get(slug=options['aspirant_title'])
        elected_pos_title     = PositionTitle.objects.get(slug=options['elected_title'])
        elected_subtitle      = options['elected_subtitle'] or ''
        
        # convert the dates to approximate dates
        aspirant_end_date  = yyyymmdd_to_approx(options['aspirant_end_date'])
        elected_start_date = yyyymmdd_to_approx(options['elected_start_date'])
        future_date        = ApproximateDate(future=True)
        
        # get the winner
        elected = Person.objects.get(slug=options['elected_person'])

        # create (if needed) the elected positon.
        if options['commit']:
            elected_pos, created = Position.objects.get_or_create(
                person       = elected,
                title        = elected_pos_title,
                place        = place,
                organisation = organisation,
                start_date   = elected_start_date,
                defaults     = {
                    'end_date': future_date,
                    'subtitle': elected_subtitle,
                    'category': 'political',
                }
            )
            if created:
                print "  Created %s" % elected_pos
            

        # get all related aspirant positions
        for pos in Position.objects.filter(place=place, title=aspirant_pos_title).currently_active():
            print "  Ending %s" % pos
            pos.end_date = aspirant_end_date
            if options['commit']:
                pos.save()
