"""Command to import PMG's constitiency office data

PMG are undertaking an exercise to visit all the constituency
offices and collect accurate locations and photographs.
The data from this is available at

https://app.m4jam.com/app/campaigns/2298/export/

This script parses the resulting CSV file and updates our data
on constituency offices to have the correct location.
"""


import csv
import os.path
import re
from StringIO import StringIO

from PIL import Image as PillowImage

import requests

from django.conf import settings

from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from pombola.core.models import (
    Organisation,
    )
from pombola.core.utils import mkdir_p

from pombola.images.models import Image


PILLOW_FORMAT_EXTENSIONS = {
    'JPEG': 'jpg',
    'PNG': 'png',
    'GIF': 'gif',
    'BMP': 'bmp',
}


# Taken from https://github.com/mysociety/yournextrepresentative
def get_image_extension(image):
    try:
        pillow_image = PillowImage.open(image)
    except IOError as e:
        if 'cannot identify image file' in e.args[0]:
            print("Ignoring a non-image file {0}".format(image))
            return None
        raise
    return PILLOW_FORMAT_EXTENSIONS[pillow_image.format]


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

        storage = FileSystemStorage()

        storage_path = os.path.join('images', 'constituency-offices')
        images_directory = os.path.join(
            settings.MEDIA_ROOT,
            storage_path
            )
        mkdir_p(images_directory)

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

                # Now get the photo
                photo_url = row.get('Constituency_Photo')

                try:
                    org.images.get(source=photo_url)
                    print (
                        "Skipping {} as url matches existing image."
                        .format(org.slug)
                        )
                    continue
                except Image.DoesNotExist:
                    print "Adding new image to {}.".format(org.slug)

                if photo_url:
                    response = requests.get(photo_url)
                    extension = get_image_extension(StringIO(response.content))

                    if extension is None:
                        continue

                    image_filename = '{}.{}'.format(org.slug, extension)

                    desired_storage_path = os.path.join(storage_path, image_filename)

                    storage_filename = storage.save(desired_storage_path, StringIO(response.content))

                    image = Image(
                        content_object=org,
                        source=photo_url,
                        is_primary=True,
                        image=storage_filename,
                        )
                    image.save()
