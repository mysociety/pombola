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

ideal_collection_order = ('organizations', 'persons', 'posts', 'memberships')

class Command(BaseCommand):
    args = 'FILENAME-PREFIX POMBOLA-URL'
    help = 'Export all people, organisations and memberships to Popolo JSON and mongoexport format'

    option_list = BaseCommand.option_list + (
            make_option(
                "--pombola",
                dest="pombola",
                action="store_true",
                help="Make a single file with inline memberships, suitable for core_import_popolo"
            ),
    )

    def handle(self, *args, **options):

        if len(args) != 2:
            raise CommandError, "You must provide a filename prefix and the Pombola instance URL"

        filename_prefix, pombola_url = args
        parsed_url = urlparse.urlparse(pombola_url)

        primary_id_scheme = '.'.join(reversed(parsed_url.netloc.split('.')))

        inline_memberships = options['pombola']

        popolo_data = get_popolo_data(
            primary_id_scheme,
            pombola_url,
            inline_memberships=inline_memberships
        )

        if options['pombola']:
            output_filename = filename_prefix + '-pombola.json'
            with open(output_filename, 'w') as f:
                json.dump(popolo_data, f, indent=4, sort_keys=True)
        else:
            for collection, data in popolo_data.items():
                for mongoexport_format in (True, False):
                    output_filename = filename_prefix + '-'
                    if mongoexport_format:
                        output_filename += 'mongo-'
                    output_filename += collection + ".json"
                    with open(output_filename, 'w') as f:
                        if mongoexport_format:
                            for item in data:
                                item['_id'] = item['id']
                                json.dump(item, f, sort_keys=True)
                                f.write("\n")
                        else:
                            json.dump(data, f, indent=4, sort_keys=True)
