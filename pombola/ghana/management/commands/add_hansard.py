import os

from django.core.management.base import BaseCommand, CommandError

from odekro.management.hansard_parser import parse
from odekro import data


class Command(BaseCommand):
    """Import Hansard"""

    help = 'Import Hansard'
    args = '<file1> <file2> ...'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError
        
        for src in args:
            if not os.path.exists(src):
                sys.exit(1)

            if os.path.isfile(src) and src.endswith('.txt'):
                self.add_hansard(src)
            elif os.path.isdir(src):
                for f in os.listdir(src):
                    self.handle(os.path.abspath(os.path.join(src, f)), **options)

    def add_hansard(self, src):
        try:
            data.add_hansard(*parse(open(src, 'r').read()))
        except Exception, e:
            print 'Error adding hansard: %s' % src
            print e
