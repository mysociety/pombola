"""Export a CSV listing committee members with term dates."""

import unicodecsv as csv
import os
import collections

from pombola.core.models import Person, Organisation, OrganisationKind

from django.core.management.base import BaseCommand, CommandError
from django.utils import dateformat


def formatApproxDate(date):
        if date:
            if date.future:
                return 'future'
            if date.past:
                return 'past'
            elif date.year and date.month and date.day:
                return dateformat.format(date, 'Y-m-d')
            elif date.year and date.month:
                return dateformat.format(date, 'Y-m')
            elif date.year:
                return dateformat.format(date, 'Y')
        else:
            return None


class Command(BaseCommand):
    args = 'destination'
    help = 'Export a CSV listing committee members with term dates.'

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError("You must provide a destination.")

        destination = args[0]

        organisationKinds = [
            # OrganisationKind.objects.filter(slug='committee').get(),
            OrganisationKind.objects.filter(slug='national-assembly-committees').get(),
            # OrganisationKind.objects.filter(slug='ad-hoc-committees').get(),
            # OrganisationKind.objects.filter(slug='joint-committees').get(),
            # OrganisationKind.objects.filter(slug='ncop-committees').get(),
        ]
        organisations = Organisation.objects.filter(kind__in=organisationKinds)

        fields = [
            'name',
            'title',
            'given_name',
            'family_name',
            'committee',
            'committee_kind',
            'position',
            'url',
            'start_date',
            'end_date',
            'parties',
            'cell',
            'voice',
            'email',
        ]

        contact_kinds = [
            'cell',
            'voice',
            'email',
        ]

        with open(os.path.join(destination), 'wb') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fields)

            writer.writeheader()

            for organisation in organisations:

                # Get the list of positions
                positions = organisation.position_set.filter(person__hidden=False)

                # Write all the outputs
                for position in positions:
                    print position
                    person = position.person

                    parties = []
                    for party in person.parties():
                        parties.append(party.name)

                    contacts = {}
                    for contact_kind in contact_kinds:
                        contacts[contact_kind] = []
                        for contact in person.contacts.all().filter(kind__slug=contact_kind):
                            contacts[contact_kind].append(contact.value)

                    position_output = {
                        'name': person.name,
                        'title': person.title,
                        'given_name': person.given_name,
                        'family_name': person.family_name,
                        'committee': organisation.name,
                        'committee_kind': organisation.kind,
                        'position': position.title,
                        'url': 'https://www.pa.org.za/person/{}/'.format(person.slug),
                        'start_date': formatApproxDate(position.start_date),
                        'end_date': formatApproxDate(position.end_date),
                        'parties': ', '.join(parties),
                        'cell': ', '.join(contacts['cell']),
                        'voice': ', '.join(contacts['voice']),
                        'email': ', '.join(contacts['email']),
                    }
                    writer.writerow(position_output)

        print "Done! Exported CSV of memberships of " + str(len(organisations)) + " committees."
