import re 
import csv
import sys

import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from pombola.ghana import data


class Command(BaseCommand):
    """Read in an info page file and either create or update existing info"""

    help = 'Create/Update info page'
    args = '<file> <Title> [<slug>]'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) < 2 or len(args) > 3:
            raise CommandError
        
        path = args[0]
        content = open(path, 'r').read()
        title = args[1]
        
        if len(args) == 3:
            slug = args[2]
        else:
            slug = os.path.basename(path)[:-3]

        data.add_info_page(slug, title, content)