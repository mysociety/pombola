"""Export a CSV listing National Assembly members with term dates."""

import unicodecsv as csv
import os
import collections

from pombola.core.models import Person, Organisation

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = 'destination'
    help = 'Export a CSV listing National Assembly members with term dates.'

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError("You must provide a destination.")

        destination = args[0]

        organisation = Organisation.objects.filter(slug='national-assembly').get()

        fields = [
            'name',
            'title',
            'given_name',
            'family_name',
            'url',
            'start_date',
            'end_date',
        ]

        with open(os.path.join(destination), 'wb') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fields)

            writer.writeheader()

            # Get the list of positions
            positions = organisation.position_set.filter(person__hidden=False)

            # Write all the outputs
            for position in positions:
                print position
                person = position.person
                position_output = {
                    'name': person.name,
                    'title': person.title,
                    'given_name': person.given_name,
                    'family_name': person.family_name,
                    'url': 'https://www.pa.org.za/person/{}/'.format(person.slug),
                    'start_date': position.start_date,
                    'end_date': position.end_date,
                }
                writer.writerow(position_output)

        print "Done! Exported CSV of " + str(len(positions)) + " positions."
