from django.core.management.base import NoArgsCommand

from hansard import models
from hansard.kenya_parser import KenyaParser

class Command(NoArgsCommand):
    help = 'Process all sources that have not been done'
    args = ''

    def handle_noargs(self, **options):

        for source in Source.objects.all().requires_processing():
            print "Looking at %s" % source

            pdf = source.file()
            html = KenyaParser.convert_pdf_to_html( pdf )
            data = KenyaParser.convert_html_to_data( html )
            KenyaParser.create_entries_from_data_and_source( data, source )

