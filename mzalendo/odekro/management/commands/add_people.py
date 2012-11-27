from django.core.management.base import BaseCommand, CommandError

import json
from odekro import data


class Command(BaseCommand):
    """Read in mps data and either create or update existing info"""

    help = 'Add Persons data'
    args = '<file>'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) != 1:
            raise CommandError
        
        path = args[0]
        content = open(path, 'r').read()
        for obj in json.loads(content):
            data.add_person_object(obj)
