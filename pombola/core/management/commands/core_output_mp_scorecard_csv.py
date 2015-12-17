import csv
import StringIO

from django.core.management.base import BaseCommand

from pombola.core import models


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
        politician_data = []

        mps = models.Person.objects.all().is_politician()
        
        for mp in mps:
            data = {}
            
            data['Name'] = mp.name.encode('utf-8')

            try:
                data['Constituency'] = mp.constituencies()[0].name.encode('utf-8')
            except IndexError:
                data['Constituency'] = u'N/A' # some mps don't have constituencies

            # we want all scorecards - the person model has an overide on the 'scorecards'
            # method that mixes in the constituency ones
            for scorecard_entry in mp.scorecards():
                if scorecard_entry.disabled: continue # don't want these - their rating is bogus

                category_name = scorecard_entry.category.name
                rating = scorecard_entry.score_as_word()

                scorecard_field_names_set.add(category_name)
                data[ category_name ] = rating

            politician_data.append(data)
        
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
        
        for data in politician_data:
            writer.writerow( data )
        
        print csv_output.getvalue()
