from optparse import make_option
import sys

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from pombola.core.models import (
    Contact, ContactKind, Organisation, OrganisationKind, Place, PlaceKind
)

from ..helpers import geocode, LocationNotFound

class Command(BaseCommand):
    help = 'Update the physical address of a constituency office'
    args = '<CONSTITUENCY-OFFICE-ID>'

    option_list = BaseCommand.option_list + (
        make_option('--commit', dest='commit', action='store_true',
                    help='Actually update the database'),
        make_option('--lat', dest='lat', type='float', help='Latitude'),
        make_option('--lon', dest='lon', type='float', help='Longitude'),
        make_option("--address", dest="new_address",
                    help='The new street address of the constituency office',
                    metavar='STREET-ADDRESS'),
    )

    def handle(self, *args, **options):

        office_kind = OrganisationKind.objects.get(slug='constituency-office')

        if len(args) != 1:
            self.print_help(sys.argv[0], sys.argv[1])
            return

        office_id = args[0]

        if not options['new_address']:
            raise CommandError('You must supply --address')

        if (options['lat'] is None) ^ (options['lon'] is None):
            raise CommandError('You must supply both --lat and --lon')

        try:
            office = Organisation.objects.get(pk=office_id)
        except Organisation.DoesNotExist:
            raise CommandError("No office found with ID {0}".format(office_id))

        self.stdout.write(
            "Updating the constituency office: " + office.name.encode('utf-8')
        )

        if office.kind != office_kind:
            raise CommandError(
                "Organisation {0} isn't a constituency office".format(office_id)
            )

        if options['lat']:
            lon = options['lon']
            lat = options['lat']
        else:
            # Otherwise try to geocode the address:
            try:
                lon, lat, _ = geocode(options['new_address'])
                print "Location found"
            except LocationNotFound:
                raise CommandError(u"Couldn't find the location of:\n{0}".format(
                    options['new_address']
                ))

        # Check with the user if this is actually the location they
        # want:

        url_template = 'https://www.google.com/maps/place/{lat}+{lon}/@{lat},{lon},17z'
        print "This would update the office address to:"
        print ' ', url_template.format(lon=lon, lat=lat)
        print "If this is correct, type 'y' to continue:"
        response = raw_input('(y/n): ')
        if response != 'y':
            sys.stderr.write("Aborting.\n")
            return

        existing_positions = office.place_set.filter(
            kind__slug='constituency-office',
            name__startswith='Approximate position'
        )
        if len(existing_positions) > 1:
            msg = "Bad data: found multiple existing positions for the office"
            raise CommandError(msg)
        elif len(existing_positions) == 0:
            # Create a new position:
            position_name = u'Approximate position of ' + office.name
            position = Place(
                name=position_name,
                organisation=office,
                slug=slugify(position_name),
                location=Point(lon, lat),
                kind=PlaceKind.objects.get(slug='constituency-office'),
            )
        else:
            # Update the existing position:
            position = existing_positions[0]
            position.location = Point(lon, lat)

        existing_addresses = office.contacts.filter(kind__slug='address')
        if len(existing_addresses) > 1:
            msg = "Bad data: found multiple existing addresses for the office"
            raise CommandError(msg)
        elif len(existing_addresses) == 0:
            contact_address = Contact(
                value=options['new_address'],
                kind=ContactKind.objects.get(slug='address'),
            )
        else:
            contact_address = existing_addresses[0]
            contact_address.value = options['new_address']

        # Actually save to the database (or not, depending on whether
        # --commit was specified).

        if options['commit']:
            print "Saving to the database:"
        else:
            msg = "Not updating (--commit wasn't specified) but would save:"
            self.stdout.write(msg)
        self.stdout.write(
            'Place: ' + unicode(position).encode('utf-8')
        )
        self.stdout.write(
            'Contact: ' + unicode(contact_address).encode('utf-8')
        )

        if options['commit']:
            position.save()
            contact_address.save()
