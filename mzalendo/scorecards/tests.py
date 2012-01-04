"""
Test that the scorecards works as expected
"""

import datetime
import pprint
import tempfile
import csv

from django.test import TestCase

from core.models import Place, PlaceKind
from models import Category, Entry

class DataTest(TestCase):
    pass

    # Tests are mostly for importing the CSV file, which is currently commented
    # out following the migration across from the place_data app. Should be
    # reinstated if the CSV import is permitted again
    
    # def setUp(self):
    #     self.place_kind    = PlaceKind.objects.create( slug='pk_test', name='PK Test')
    #     self.place         = Place.objects.create( slug='place_test', name='PLace Test', kind=self.place_kind)
    #     self.data_category = DataCategory.objects.create( slug='dc_test', name='DC Test')        
    #     
    # def csv_file(self, entries):
    #     temp_csv_file = tempfile.TemporaryFile()
    #     fieldnames = sorted( entries[0].keys() )
    #     writer = csv.DictWriter( temp_csv_file, fieldnames )
    # 
    #     # Could use this if we had python >= 2.7
    #     # writer.writeheader()
    # 
    #     # workaround for python < 2.7
    #     header_row = {}
    #     for key in fieldnames:
    #         header_row[key] = key
    #     writer.writerow( header_row )
    # 
    #     writer.writerows( entries )
    #     temp_csv_file.seek(0)
    #     return temp_csv_file
    # 
    # 
    # def default_csv_entry(self):
    #     return dict(
    #         place_slug         = self.place.slug,
    #         category_slug      = self.data_category.slug,
    #         date               = '2011/09/30',
    #         value              = 42, 
    #         general_remark     = 'test general_remark',
    #         comparative_remark = 'c_average',
    #         equivalent_remark  = 'test equivalent_remark',
    #         source_url         = 'http://example.com/',
    #         source_name        = 'Source',            
    #     )
    # 
    # def create_csv_entry(self, **kwargs):
    #     """take the default entry and change using the kwargs given"""
    #     entry = self.default_csv_entry()
    #     for key, value in kwargs.items():
    #         entry[key] = value
    #     return entry
    # 
    # def run_process_csv( self, entries, save=False ):
    #     csv_file = self.csv_file(entries)
    #     results = Data.process_csv( csv_file, save=save )
    #     return results
    #     
    # 
    # def test_csv_new_data_row(self):
    #     results = self.run_process_csv( [ self.create_csv_entry() ] )
    #     self.assertEqual( results['error_count'], 0 )
    #     self.assertEqual( len(results['entries']), 1 )
    #     self.assertEqual( results['entries'][0]['action'], 'create' )
    # 
    # 
    # def test_csv_update_data_row(self):
    #     results = self.run_process_csv( [ self.create_csv_entry() ], save=True )
    #     results = self.run_process_csv( [ self.create_csv_entry() ] )
    #     self.assertEqual( results['error_count'], 0 )
    #     self.assertEqual( len(results['entries']), 1 )
    #     self.assertEqual( results['entries'][0]['action'], 'update' )
    # 
    # def test_csv_bad_values(self):
    #     results = self.run_process_csv( [ self.create_csv_entry(value='bad') ] )
    #     self.assertEqual( results['error_count'], 1 )
    #     self.assertEqual( len(results['entries']), 1 )
    #     self.assertEqual( results['entries'][0]['action'], None )
    #     self.assertEqual( results['entries'][0]['error'], 'value: This value must be a float.' )
    # 
    #     results = self.run_process_csv( [ self.create_csv_entry(date='foobar') ] )
    #     self.assertEqual( results['error_count'], 1 )
    #     self.assertEqual( len(results['entries']), 1 )
    #     self.assertEqual( results['entries'][0]['action'], None )
    #     self.assertEqual( results['entries'][0]['error'], "date: Not a valid yyyy/mm/dd date: 'foobar'" )
    # 
    #     results = self.run_process_csv( [ self.create_csv_entry(place_slug='non-existant') ] )
    #     self.assertEqual( results['error_count'], 1 )
    #     self.assertEqual( len(results['entries']), 1 )
    #     self.assertEqual( results['entries'][0]['action'], None )
    #     self.assertEqual( results['entries'][0]['error'], 'place or category slug not found' )
    # 
    # def test_csv_duplicate_row(self):
    #     entries = [ self.create_csv_entry(), self.create_csv_entry() ]
    #     results = self.run_process_csv( entries )
    #     self.assertEqual( results['error_count'], 1 )
    #     self.assertEqual( len(results['entries']), 2 )
    #     self.assertEqual( results['entries'][0]['action'], 'create' )
    #     self.assertEqual( results['entries'][1]['action'], None )
    #     self.assertEqual( results['entries'][1]['error'], 'Duplicate of entry on line 2' )
    # 
    # def test_csv_extra_headers(self):
    #     entries = [ self.create_csv_entry( extra_header='should not be here') ]
    #     results = self.run_process_csv( entries )
    #     self.assertEqual( results["file_error"], "Found unexpected header(s): extra_header" )
    # 
    # def test_csv_missing_headers(self):
    #     entries = [ self.create_csv_entry() ]
    #     del( entries[0]['general_remark'] )
    #     results = self.run_process_csv( entries )
    #     self.assertEqual( results["file_error"], "Missing expected header(s): general_remark" )
    # 
    # 
    # 
