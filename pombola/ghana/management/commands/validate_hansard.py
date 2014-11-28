import os

from django.core.management.base import BaseCommand, CommandError

from pombola.ghana.management.hansard_parser import parse
from pombola.ghana.management.hansard_parser import parse
from pombola.ghana import data




class Command(BaseCommand):
    """Validate Hansard"""

    help = 'Import Hansard'
    args = '<file1> <file2> ...'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError
        
        for src in args:
            if not os.path.exists(src):
                sys.exit(1)

            if os.path.isfile(src) and src.endswith('.txt'):
                self.validate_hansard(src)
            elif os.path.isdir(src):
                for f in os.listdir(src):
                    self.handle(os.path.abspath(os.path.join(src, f)), **options)

    def validate_hansard(self, src):
        try:
            head, entries = parse(open(src, 'rU').read())
            if self.validate_header(head):
                if self.validate_entries(entries):
                    print '%s is OK' % src
                else:
                    print 'Bad entry found in: %s' % src
            else:
                print 'Bad header found in: %s' % src
                print head
        except Exception, e:
            print 'Error validating hansard: %s' % src
            print e

    def validate_header(self, head):
        return head.get('series', None) and \
               head.get('volume', None) and \
               head.get('number', None) and \
               head.get('date', None) and \
               head.get('time', None)

    def validate_entries(self, entries):
        entry = None
        while len(entries):
            entry = entries.pop(0)
            if entry['kind'] == 'chair':
                break

        for entry in entries:

            kind = entry['kind']
            if not self.validate_entry(entry):
                print entry
                return False
        return True

    def validate_entry(self, entry):
        return entry.get('time', None) and True
        

    # def validate_speech(self, speech):
    #            True
