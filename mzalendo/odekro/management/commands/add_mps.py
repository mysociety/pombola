import re 
import csv
import sys

import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from odekro import data


class Command(BaseCommand):
    """Read in an info page file and either create or update existing info"""

    help = 'Add MPs data'
    args = '<file>'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) != 1:
            raise CommandError
        
        path = args[0]
        content = open(path, 'r').read()
        data.add_mps_from_json(content)
