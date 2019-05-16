import unicodecsv

from django.core.management.base import BaseCommand, CommandError

from pombola.core.models import Organisation, OrganisationKind


parties_csv = "pombola/south_africa/data/elections/2019/candidates-parties.csv"


class Command(BaseCommand):
    help = "Creates new parties for the 2019 elections"

    def handle(self, *args, **options):
        with open(parties_csv, "rb") as csvfile:
            csv = unicodecsv.reader(csvfile)
            for row in csv:
                party_slug = row[0]
                party_name = row[1]
                party_kind = OrganisationKind.objects.get(slug="party")
                party, created = Organisation.objects.get_or_create(
                    slug=party_slug, name=party_name, kind=party_kind
                )
                if created:
                    print("Created new party: {}".format(party))
                else:
                    print("Party already exists: {}".format(party))
