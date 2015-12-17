import csv
import StringIO
import re

from django.core.management.base import BaseCommand

from pombola.core import models


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
        politician_data = []

        mps = models.Person.objects.all().is_politician()
        
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
                if data.get( kind_name, None ):
                    data[ kind_name ] += '; ' + value
                else:
                    data[ kind_name ] = value

            politician_data.append(data)
        
        csv_output = StringIO.StringIO()
        csv_fieldnames =  [ 'Name', 'Constituency' ] + sorted( list(contact_field_names_set) )
        writer = csv.DictWriter( csv_output, csv_fieldnames )
        

        # Needs Python 2.7
        # writer.writeheader()
        
        # Silly dance for Python 2.6.6's csv.DictWriter which bizarrely does not have writeheader
        fieldname_dict = {}
        for key in csv_fieldnames:
            fieldname_dict[key] = key
        writer.writerow( fieldname_dict )
        
        for data in politician_data:
            writer.writerow( data )
        
        print csv_output.getvalue()
