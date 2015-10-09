import csv
import sys

from django.core.management.base import BaseCommand, CommandError

from pombola.core.models import Organisation, OrganisationRelationship

MAPS_URL_TEMPLATE = 'https://www.google.com/maps/place/{lat}+{lon}/@{lat},{lon},17z'

def encode_row_values_to_utf8(row):
    return {
        k: unicode(v).encode('utf-8')
        for k, v in row.items()
    }

class Command(BaseCommand):

    def handle(self, *args, **options):

        fields = [
            'OfficeID',
            'OfficeName',
            'ClosedDate',
            'MapURL',
            'PhysicalAddress',
            'Latitude',
            'Longitude',
            'PartyName',
            'PartyID'
        ]

        writer = csv.DictWriter(sys.stdout, fieldnames=fields)

        writer.writeheader()

        for o in Organisation.objects. \
            filter(kind__slug='constituency-office'). \
            order_by('slug'):
            places = o.place_set.filter(
                kind__slug='constituency-office',
                name__startswith='Approximate position of ',
            )
            place_count = places.count()
            if place_count > 1:
                msg = "Multiple places ({place_count}) found for {organisation_id}"
                raise CommandError(msg.format(
                    place_count=place_count,
                    organisation_id=o.id
                ))
            row = {'OfficeID': o.id, 'OfficeName': o.name}
            if o.ended and not o.ended.future:
                row['ClosedDate'] = o.ended
            if place_count:
                location = places[0].location
                row['Latitude'] = location.y
                row['Longitude'] = location.x
                row['MapURL'] = MAPS_URL_TEMPLATE.format(
                    lat=location.y,
                    lon=location.x,
                )
            # Try to find the party whose office this is:
            try:
                party = OrganisationRelationship.objects.get(
                    organisation_b=o,
                    kind__name='has_office'
                ).organisation_a
                row['PartyID'] = party.id
                row['PartyName'] = party.name
            except OrganisationRelationship.DoesNotExist:
                message = "No party found for office with ID {office_id}\n"
                self.stderr.write(message.format(office_id=o.id))
            # Now try to find the address from the office
            # organisation's contacts:
            addresses = o.contacts.filter(kind__slug='address')
            address_count = addresses.count()
            if address_count > 1:
                msg = "Multiple address found for {organisation_id}"
                raise CommandError(msg.format(
                    address_count=address_count,
                    organisation_id=o.id
                ))
            if address_count:
                row['PhysicalAddress'] = addresses[0].value
            writer.writerow(encode_row_values_to_utf8(row))
