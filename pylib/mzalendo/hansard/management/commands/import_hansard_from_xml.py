import pprint
import xml.sax
from hansard.xml_handlers import HansardXML
from django.core.management.base import LabelCommand

from hansard import models

class Command(LabelCommand):
    help = 'Import KML data'
    args = '<KML files>'

    def handle_label(self, filename, **options):

        # Extract text from the xml produced from the Hansard PDF using 'pdftohtml -xml ___.pdf'
        
        # dirty hacks:
        #  * manually remove the DTD line at the top - should ignore it in the code instead.
        
        filename = '/home/evdb/Hansard 01.09.11.xml'
        
        hansard_data = HansardXML()
        xml.sax.parse(filename, hansard_data)
        
        pp = pprint.PrettyPrinter(indent=4)
        
        
        
        for chunk in hansard_data.content_chunks:
            pp.pprint( chunk )
            
            models.Chunk.objects.get_or_create(
                date         = '2011-09-11',
                session      = 'pm',
                text_counter = chunk['text_counter'],
            
                defaults = dict(
                    type         = chunk['type'],
                    page         = chunk['page'],
                    speaker      = chunk.get('speaker', ''),
                    content      = chunk['content'],
                    source       = filename,
                )
            )
            
