"""Command to import PMG's constitiency office data

PMG are undertaking an exercise to visit all the constituency
offices and collect accurate locations and photographs.
The data from this is available at

https://app.m4jam.com/app/campaigns/2298/export/

This script parses the resulting CSV file and updates our data
on constituency offices to have the correct location.
"""


import csv
import re

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from pombola.core.models import (
    Organisation,
    )


# Matches the format of the locations in the CSV we get from PMG.
location_re = re.compile(
    r'SRID=4326;POINT\((-?[0-9]+\.[0-9]+) (-?[0-9]+\.[0-9]+)\)')


class Command(BaseCommand):
    args = '<path to csv file>'
    help = 'Updates constituency offices based on the supplied CSV file.'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError(
                "You must provide the path to the CSV file as an argument."
                )

        constituency_offices = Organisation.objects.filter(
            kind__slug='constituency-office')

        with open(args[0]) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                poi_ref = row['POI_REFERENCE']
                party, name = (
                    re.match(
                        '(.*) Constituency Office (.*)', poi_ref
                        ).groups()
                    )
                name = re.sub('\s+', ' ', name)

                qs = constituency_offices.filter(
                    name__regex=r'^{}.+: {}$'.format(party, name))

                try:
                    org = qs.get()
                except Organisation.MultipleObjectsReturned:
                    print "Skipping {} as multiple orgs returned: {}".format(
                        poi_ref,
                        repr(qs),
                        )
                    continue
                except Organisation.DoesNotExist:
                    # Fall back to searching for the name and the party in the
                    # constituency office name
                    qs = (
                        Organisation.objects
                        .filter(kind__slug='constituency-office')
                        .filter(name__contains=name)
                        .filter(name__contains=party)
                        )

                    org = qs.get()

                place = (
                    org.place_set
                    .filter(name__contains='Approximate position of')
                    .filter(kind__slug='constituency-office')
                    .get()  # There should be only one.
                    )

                lon, lat = location_re.match(row['Constituency_Pin']).groups()

                place.location = Point(float(lon), float(lat))
                place.save()
