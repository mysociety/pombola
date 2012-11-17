from django.core.management.base import BaseCommand, CommandError

from odekro.management.hansard_parser import parse
from odekro import data


class Command(BaseCommand):
    """Import Hansard"""

    help = 'Import Hansard'
    args = '<file>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError
        
        path = args[0]
        content = open(path, 'r').read()
        data.add_hansard(*parse(content))
