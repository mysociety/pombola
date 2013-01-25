# This is designed to be called from a datamigration after the
# migrations that introduce the core_parliamentarysession table has
# been create and add the parliamentary_session_id column to
# core_place.  This script creates the ParliamentarySessions for Kenya
# or Nigeria and links Places with the right one.

import datetime
from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation, Type, NameType, Country, CodeType
from core.models import ParliamentarySession, Organisation, OrganisationKind, PlaceKind, Place
from settings import COUNTRY_APP
from optparse import make_option
import sys


class Command(NoArgsCommand):

    help = 'Create ParliamentarySessions and update Places to point to them'
    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--reverse', action='store_true', dest='reverse', help='Reverse these actions'),
    )

    def handle_noargs(self, **options):

        def maybe_save(o):
            if options['commit']:
                print >> sys.stderr, "Saving", o, "to the database"
                o.save()
            else:
                print >> sys.stderr, "Not saving", o, "to the database, since --commit wasn't specified"

        if options['reverse']:
            # All we need to do when migrating backwards is to
            # recreate the PlaceKind for '2013 Constituencies', and
            # associate all the 2013 Session constituencies with them.
            # Then the earlier reverse migrations will remove the
            # parliamentary_sessions column in core_places and the
            # parliamentary_sessions table.
            pk_2013 = PlaceKind(slug="constituency-2013",
                                name="2013 Constituency",
                                plural_name="2013 Constituencies")
            maybe_save(pk_2013)
            na2_kenya = ParliamentarySession.objects.get(name="National Assembly 2013-")
            for place in Place.objects.filter(parliamentary_session=na2_kenya):
                place.kind = pk_2013
                maybe_save(place)
            return

        # First, create the ParliamentarySession objects.  (If there
        # are already parliamentary sessions, then don't try to create
        # any new ones.)

        na1_kenya = None
        na2_kenya = None
        senate = None

        house = None


        if 0 == ParliamentarySession.objects.count():
            if COUNTRY_APP == 'kenya':
                ok_na = Organisation.objects.get(name='Parliament', kind__name='Governmental')
                try:
                    ok_senate = Organisation.objects.get(name='Senate', kind__name='Governmental')
                except Organisation.DoesNotExist:
                    ok_senate = Organisation(name='Senate',
                                             slug='senate',
                                             kind=OrganisationKind.objects.get(name='Governmental'))
                    maybe_save(ok_senate)

                na1_kenya = ParliamentarySession(name="National Assembly 2007-2013",
                                                 slug='na2007',
                                                 start_date=datetime.date(2007, 12, 28),
                                                 end_date=datetime.date(2013, 1, 14),
                                                 mapit_generation=2,
                                                 house=ok_na)
                maybe_save(na1_kenya)
                na2_kenya = ParliamentarySession(name="National Assembly 2013-",
                                                 slug='na2013',
                                                 start_date=datetime.date(2013, 3, 5),
                                                 end_date=datetime.date(9999, 12, 31),
                                                 mapit_generation=3,
                                                 house=ok_na)
                maybe_save(na2_kenya)
                senate = ParliamentarySession(name="Senate 2013-",
                                              slug='s2013',
                                              start_date=datetime.date(2013, 3, 5),
                                              end_date=datetime.date(9999, 12, 31),
                                              mapit_generation=3,
                                              house=ok_senate)
                maybe_save(senate)
            elif COUNTRY_APP == 'nigeria':
                ok_senate = Organisation.objects.get(name='Senate', kind__name='Political')
                ok_house = Organisation.objects.get(name='House of Representatives', kind__name='Political')
                senate = ParliamentarySession(name="Senate 2011-",
                                              slug='s2011',
                                              start_date=datetime.date(2011, 4, 10),
                                              end_date=datetime.date(9999, 12, 31),
                                              mapit_generation=1,
                                              house=ok_senate)
                maybe_save(senate)
                house = ParliamentarySession(name="House of Representatives 2011-",
                                             slug='hr2011',
                                             start_date=datetime.date(2011, 04, 10),
                                             end_date=datetime.date(9999, 12, 31),
                                             mapit_generation=1,
                                             house=ok_house)
                maybe_save(house)
            else:
                # There's nothing to do:
                print >> sys.stderr, "Unknown COUNTRY_APP (%s) - not creating parliamentary sessions"
        else:
            # There's nothing to do:
            print >> sys.stderr, "There were already ParliamentarySessions - skipping their creation"

        # Now link each Place to the right ParliamentarySession:

        if COUNTRY_APP == 'kenya':

            pk_constituency = PlaceKind.objects.get(name='Constituency')
            pk_2013_constituency = PlaceKind.objects.get(name='2013 Constituency')
            pk_county = PlaceKind.objects.get(name='County')

            if not na1_kenya:
                na1_kenya = ParliamentarySession.objects.get(name="National Assembly 2007-2013")
            if not na2_kenya:
                na2_kenya = ParliamentarySession.objects.get(name="National Assembly 2013-")
            if not senate:
                senate = ParliamentarySession.objects.get(name="Senate 2013-")

            for place in pk_constituency.place_set.all():
                if place.name == 'Mbeere South':
                    print >> sys.stderr, "Skipping Mbeere South, which shouldn't be there"
                place.parliamentary_session = na1_kenya
                maybe_save(place)

            for place in pk_2013_constituency.place_set.all():
                place.parliamentary_session = na2_kenya
                place.kind = pk_constituency
                maybe_save(place)

            for place in pk_county.place_set.all():
                place.parliamentary_session = senate
                maybe_save(place)

            # We don't need the '2013 Constituencies' PlaceKind any
            # more, so remove it:
            if options['commit']:
                pk_2013_constituency.delete()
            else:
                print "Not removing %s, since --commit wasn't specified" % (pk_2013_constituency,)

        elif COUNTRY_APP == 'nigeria':

            if not house:
                house = ParliamentarySession.objects.get(name="House of Representatives 2011-")
            if not senate:
                senate = ParliamentarySession.objects.get(name="Senate 2011-")

            pk_fed = PlaceKind.objects.get(name='Federal Constituency')
            pk_sen = PlaceKind.objects.get(name='Senatorial District')

            for place in pk_fed.place_set.all():
                place.parliamentary_session = house
                maybe_save(place)

            for place in pk_sen.place_set.all():
                place.parliamentary_session = senate
                maybe_save(place)

        else:
            # There's nothing to do:
            print >> sys.stderr, "There were already ParliamentarySessions - skipping their creation"
