# This command creates a new PopIt instance based on the Person,
# Position and Organisation models in Pombola.

import json
from optparse import make_option
import slumber
import sys
import urlparse

from pombola.core.popolo import get_popolo_data

from django.core.management.base import BaseCommand, CommandError

from popit_api import PopIt

class Command(BaseCommand):
    args = 'FILENAME-PREFIX POMBOLA-URL'
    help = 'Export all people, organisations and memberships to Popolo JSON'

    def handle(self, *args, **options):

        if len(args) != 2:
            raise CommandError, "You must provide a filename prefix and the Pombola instance URL"

        filename_prefix, pombola_url = args
        parsed_url = urlparse.urlparse(pombola_url)

        primary_id_scheme = '.'.join(reversed(parsed_url.netloc.split('.')))

        for collection, data in get_popolo_data(primary_id_scheme,
                                                pombola_url,
                                                inline_memberships=False).items():
            output_filename = filename_prefix + '-' + collection + ".json"
            with open(output_filename, 'w') as f:
                json.dump(data, f, indent=4)
