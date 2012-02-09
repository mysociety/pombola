from optparse import make_option
from pprint import pprint
import csv
import StringIO
import re

from django.core.management.base import BaseCommand
from django.conf import settings

from core import models
from scorecards.models import Entry

class Command(BaseCommand):
    help = 'Output CSV of all MPs and their scorecard ratings'

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
        scorecard_field_names_set = set()
        mp_data = []

        mps = models.Person.objects.all().is_mp()
        
        for mp in mps:
            data = {}
            
            data['Name'] = mp.name.encode('utf-8')

            try:
                data['Constituency'] = mp.constituencies()[0].name.encode('utf-8')
            except IndexError:
                data['Constituency'] = u'N/A' # some mps don't have constituencies

            for scorecard_entry in mp.active_scorecards():
                category_name = scorecard_entry.category.name
                rating = scorecard_entry.score_as_word()

                scorecard_field_names_set.add(category_name)
                data[ category_name ] = rating

            mp_data.append(data)
        
        csv_output = StringIO.StringIO()
        csv_fieldnames =  [ 'Name', 'Constituency' ] + sorted( list(scorecard_field_names_set) )
        writer = csv.DictWriter( csv_output, csv_fieldnames )
        

        # Needs Python 2.7
        # writer.writeheader()
        
        # Silly dance for Python 2.6.6's csv.DictWriter which bizarrely does not have writeheader
        fieldname_dict = {}
        for key in csv_fieldnames:
            fieldname_dict[key] = key
        writer.writerow( fieldname_dict )
        
        for data in mp_data:
            writer.writerow( data )
        
        print csv_output.getvalue()
