#!/usr/bin/env python

import sys
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from odekro.management.hansard_parser import normalised_lines, scan, \
                                             parse_head, meta

# from odekro import data


class Command(BaseCommand):
    """Read in an info page file and either create or update existing info"""

    help = 'Create/Update info page'
    args = '<file> <Title> [<slug>]'

    def handle(self, *args, **options):
        # file = open(args[])
        if not len(args):
            raise CommandError
        
        src = args[0]

        
        content = open(src, 'rU').read()
        lines = scan(meta(normalised_lines(content)), header=True)
        head = parse_head(lines)
        
        try:
            fname = '%s.txt' % self.filename(head)
            dst = os.path.join(os.path.dirname(src), fname)
            print dst
            os.rename(src, dst)
        except:
            print 'Error processing %s ...' % src
            print lines
            sys.exit(1)

    def filename(self, head):
        return 'debate-%(series)02d-%(volume)03d-%(number)03d-%(date)s' % head