import datetime

from django.core.management.base import NoArgsCommand

from pombola.hansard.models import Source
from pombola.hansard.kenya_parser import KenyaParser

class Command(NoArgsCommand):
    help = 'Process all sources that have not been done'
    args = ''

    def handle_noargs(self, **options):

        verbose = int(options.get('verbosity')) >= 2

        for source in Source.objects.all().requires_processing():

            if verbose:
                message = "{0}: Looking at {1}"
                print message.format(source.list_page, source)

            pdf = source.file()

            source.last_processing_attempt = datetime.datetime.now()
            source.save()

            try:
                html = KenyaParser.convert_pdf_to_html( pdf )
                data = KenyaParser.convert_html_to_data( html )
                KenyaParser.create_entries_from_data_and_source( data, source )
            except Exception as e:
                print "There was an exception when parsing {0}".format(pdf)
                raise
