import datetime

from django.core.management.base import NoArgsCommand

from hansard.models import Source
from hansard.kenya_parser import KenyaParser

class Command(NoArgsCommand):
    help = 'Process all sources that have not been done'
    args = ''

    def handle_noargs(self, **options):

        for source in Source.objects.all().requires_processing():
            
            if int(options.get('verbosity')) >= 2:
                print "Looking at %s" % source

            source.last_processing_attempt = datetime.datetime.now()
            source.save()

            pdf = source.file()
            html = KenyaParser.convert_pdf_to_html( pdf )
            data = KenyaParser.convert_html_to_data( html )
            KenyaParser.create_entries_from_data_and_source( data, source )

