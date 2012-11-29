#!/usr/bin/env python

import sys
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from odekro.management.hansard_parser import normalised_lines, scan, \
                                             parse_head, meta

# from odekro import data

class Command(BaseCommand):
    """Rename hansard text files based on header information"""

    help = 'Rename hansard text files based on header information'
    args = '<file>'

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError
        
        src = args[0]
        self.rename(src)

    def rename(self, src, name=None, ext=None, verbose=False):
        if not name:
            name = self.filename(src)
        if not ext:
            ext = src[-4:]
        
        dst = os.path.join(os.path.dirname(src), '%s%s' % (name, ext))
        if verbose:
            print dst
        if src != dst:
            os.rename(src, dst)

    def filename(self, src):
        content = open(src, 'rU').read()
        lines = scan(meta(normalised_lines(content)), header=True)
        
        try:
            head = parse_head(lines)
            return 'debate-%(series)02d-%(volume)03d-%(number)03d-%(date)s' % head
        except:
            print 'Error processing %s ...' % src
            print lines[:20]
            sys.exit(1)



