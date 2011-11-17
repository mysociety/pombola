import datetime
import os
import time
import json
import tempfile
import subprocess

from django.test import TestCase
from django.utils import unittest

from hansard.kenya_parser import KenyaParser, KenyaParserCouldNotParseTimeString
from hansard.models import Source, Sitting, Entry


class KenyaParserTest(TestCase):

    local_dir          = os.path.abspath( os.path.dirname( __file__ ) )
    sample_pdf         = os.path.join( local_dir, '2011-09-01-sample.pdf'  )
    sample_html        = os.path.join( local_dir, '2011-09-01-sample.html' )
    expected_data_json = os.path.join( local_dir, '2011-09-01-sample.json' )

    
    def test_converting_pdf_to_html(self):
        """Test that the pdf becomes the html that we expect"""
        pdf_file = open( self.sample_pdf, 'r' )
        html = KenyaParser.convert_pdf_to_html( pdf_file )

        expected_html = open( self.sample_html, 'r' ).read()
        
        self.assertEqual( html, expected_html )


    def test_converting_html_to_data(self):
        """test the convert_pdf_to_data function"""
        
        html_file = open( self.sample_html, 'r')
        html = html_file.read()

        data = KenyaParser.convert_html_to_data( html=html )
                
        # Whilst developing the code this proved useful (on a mac at least)
        # tmp = tempfile.NamedTemporaryFile( delete=False, suffix=".json" )
        # tmp = open( '/tmp/mzalend_hansard_parse.json', 'w')
        # tmp.write( json.dumps( data, sort_keys=True, indent=4 ) )
        # tmp.close()        
        # subprocess.call(['open', tmp.name ])
                
        expected = json.loads( open( self.expected_data_json, 'r'  ).read() )
        
        self.assertEqual( data['transcript'], expected['transcript'] )

        # FIXME
        self.assertEqual( data['meta'], expected['meta'] )
        

    def test_parse_time_string(self):
        
        time_tests = {
            '1.00 p.m.':  '13:00:00',
            '1.00 a.m.':  '01:00:00',
            '12.00 p.m.': '12:00:00', # am and pm make no sense at noon or midnight - but define what we want to happen
            '12.30 p.m.': '12:30:00',
        }
        
        for string, output in time_tests.items():
            self.assertEqual( KenyaParser.parse_time_string( string ), output )

        self.assertRaises(
            KenyaParserCouldNotParseTimeString,
            KenyaParser.parse_time_string,
            'foo.bar'
        )


    def test_create_entries_from_data_and_source(self):
        """Take the data and source, and create the sitting and entries from it"""

        # Create a new source in the database to attach sitting to
        source   = Source(
            name = 'Test source',
            url  = 'http://example.com/foo/bar/testing',
            date = datetime.date( 2011, 9, 1 )
        )
        source.save()
        
        data = json.loads( open( self.expected_data_json, 'r'  ).read() )

        # hand the data and source over to the parser so that it can do the
        # inserting into the database.
        KenyaParser.create_entries_from_data_and_source( data, source )
        
        # check source now marked as processed
        source = Source.objects.get(id=source.id) # reload from db
        self.assertEqual( source.last_processing_success.date(), datetime.date.today() )
        
        # check sitting created
        sitting_qs = Sitting.objects.filter(source=source)
        self.assertEqual( sitting_qs.count(), 1 )
        sitting = sitting_qs[0]
        
        # check start and end date and times correct
        self.assertEqual( sitting.start_date, datetime.date( 2011, 9, 1 ) )
        self.assertEqual( sitting.start_time, datetime.time( 14, 30, 00 ) )
        self.assertEqual( sitting.end_date,   datetime.date( 2011, 9, 1 ) )
        self.assertEqual( sitting.end_time,   datetime.time( 18, 30, 00 ) )
        
        # check correct venue set
        print "FIXME - add venue"
        
        # check entries created and that we have the right number
        entries = sitting.entry_set
        self.assertEqual( entries.count(), 61 )
        

