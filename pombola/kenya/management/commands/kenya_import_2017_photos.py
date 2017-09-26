from __future__ import print_function

import csv
from os.path import abspath, dirname, exists, join
import shutil

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand
from images.models import Image
from pombola.core.models import Person
from pombola.core.utils import mkdir_p
from PIL import Image as PillowImage
import requests

results_directory = abspath(join(
    dirname(__file__), '..', '..', 'election_data_2017', 'results'
))

class Command(BaseCommand):
    help = 'Import photos for elected representatives from the 2017 election'

    def handle_person(self, row):
        person = Person.objects.get(
            identifiers__scheme='ynr-ke', identifiers__identifier=row['id'])
        image_url = row['image_url']
        if not image_url:
            return
        # If we haven't already downloaded this file, download it:
        image_filename = join(self.cache_directory, str(row['id']))
        if not exists(image_filename):
            r = requests.get(image_url, stream=True)
            r.raise_for_status()
            with open(image_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        # Check this is a file type we can cope with:
        try:
            pillow_image = PillowImage.open(image_filename)
        except IOError as e:
            if 'cannot identify image file' in e.args[0]:
                print("Ignoring a non-image file {0}".format(image_filename))
                return None
            raise
        if pillow_image.format not in ('PNG', 'JPEG'):
            raise Exception("Found an unsupported image format: {0}".format(pillow_image.format))
        extension = {'PNG': 'png', 'JPEG': 'jpg'}[pillow_image.format]
        storage = FileSystemStorage()
        desired_storage_path = join(
            'images', 'kenya-ynr', '{}.{}'.format(row['id'], extension))
        with open(image_filename, 'rb') as f:
            storage_filename = storage.save(desired_storage_path, f)
        Image.objects.create(
            content_object=person,
            source='http://kenya.ynr.mysociety.org/person/{0}'.format(row['id']),
            is_primary=(not person.images.exists()),
            image=storage_filename,
        )
        print("Created image for:", person)

    def handle(self, **options):
        self.cache_directory = join(results_directory, '.downloaded-images')
        mkdir_p(self.cache_directory)
        for filename in ('na.csv', 'senate.csv', 'wo.csv'):
            full_filename = join(results_directory, filename)
            with open(full_filename) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.handle_person(row)
