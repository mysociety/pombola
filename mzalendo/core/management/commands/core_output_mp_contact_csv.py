from optparse import make_option
from pprint import pprint
import csv
import StringIO
import re

from django.core.management.base import BaseCommand
from django.conf import settings

from mzalendo.core import models

class Command(BaseCommand):
    help = 'Output CSV of all MPs and their contact details'

    # option_list = BaseCommand.option_list + (
    #     make_option(
    #         '--delete',
    #         action='store_true',
    #         dest='delete',
    #         default=False,
    #         help='Delete found duplicates'),
    #     )


    def handle(self, **options):
        """Create a CSV line for each MP"""

        # gather all the data before creating the CSV
        contact_field_names_set = set()
        mp_data = []

        mps = models.Person.objects.all().is_mp()
        
        for mp in mps:
            data = {}
            
            data['Name'] = mp.name.encode('utf-8')

            try:
                data['Constituency'] = mp.constituencies()[0].name.encode('utf-8')
            except IndexError:
                data['Constituency'] = u'N/A' # some mps don't have constituencies

            for contact in mp.contacts.all():
                kind_name = contact.kind.name
                value = contact.value
                value = re.sub( r'\s+', ' ', value )
                value = value.encode('utf-8')

                contact_field_names_set.add(kind_name)
                try:
                    data[ kind_name ] = value
                except KeyError:
                    data[ kind_name ] += '; ' + value

            mp_data.append(data)
        
        csv_output = StringIO.StringIO()
        csv_fieldnames =  [ 'Name', 'Constituency' ] + sorted( list(contact_field_names_set) )
        writer = csv.DictWriter( csv_output, csv_fieldnames )
        
        writer.writeheader()
        
        for data in mp_data:
            writer.writerow( data )
        
        print csv_output.getvalue()
