import datetime

from django.core.management.base import NoArgsCommand

from hansard.models import Entry

class Command(NoArgsCommand):
    help = 'Try to assign a person to each entry'
    args = ''

    def handle_noargs(self, **options):

        Entry.assign_speakers()

