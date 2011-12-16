import datetime

from django.core.management.base import NoArgsCommand

from hansard.models import Entry, Alias

class Command(NoArgsCommand):
    help = 'List all the speaker names that have not been matched up to a real person'
    args = ''

    def handle_noargs(self, **options):

        qs = Entry.objects.all().unassigned_speaker_names()
        count = qs.count()
        
        if count:
            print "There are %u Hansard speaker names that could not be matched to a person" % count
            print ""

            for entry in qs:
                print "\t'%s'" % entry['speaker_name']