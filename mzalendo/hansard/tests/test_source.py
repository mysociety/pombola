import datetime
import os
import time
import json
import tempfile
import subprocess

from django.test import TestCase
from django.utils import unittest

from hansard.models import Source

class HansardSourceTest(TestCase):

    def setUp(self):
        """Create a test source (easier than fixture for now)"""
        source = Source(
            name = 'Test Source',
            url  = 'http://www.mysociety.org/robots.txt',
            date = datetime.date( 2011, 11, 14),
        )
        source.save()
        self.source = source


    def test_source_file(self):
        """Check that source file is retrieved and cached correctly"""

        source = self.source
        
        self.assertEqual( source.name, 'Test Source')

        # get where the file will be stored
        cache_file_path = source.cache_file_path()
        
        # check that the file does not exist
        self.assertFalse( os.path.exists( cache_file_path ))

        # retrieve and check it does
        self.assertTrue( len( source.file().read() ) )
        self.assertTrue( os.path.exists( cache_file_path ))

        # change file, retrieve again and check we get cached version
        self.assertTrue( os.path.exists( cache_file_path ))
        added_text = "some random testing nonsense"
        self.assertFalse( added_text in source.file().read() )
        with open(cache_file_path, "a") as append_to_me:
            append_to_me.write("\n\n" + added_text + "\n\n")        
        self.assertTrue( added_text in source.file().read() )
        
        # delete the object - check cache file gone to
        source.delete()
        self.assertFalse( os.path.exists( cache_file_path ))
        
        # check that the object is gone
        self.assertFalse( Source.objects.filter(name="Test Source").count() )


    def test_source_file_404(self):
        """Check that urls that 404 are handled correctly"""
        source = self.source
        source.url = source.url + 'xxx'        
        self.assertEqual( source.file(), None )
        self.assertFalse( os.path.exists( source.cache_file_path() ))


    def test_requires_processing(self):
        """Check requires_processing qs works"""
        
        # There should just be one source that needs processing
        self.assertEqual( Source.objects.all().requires_processing().count(), 1 )

        # give the source a last_processed time
        self.source.last_processed = datetime.date.today()
        self.source.save()

        # none should match now
        self.assertEqual( Source.objects.all().requires_processing().count(), 0 )



class HansardSourceParsingTest(TestCase):

    local_dir          = os.path.abspath( os.path.dirname( __file__ ) )
    sample_pdf         = os.path.join( local_dir, '2011-09-01-sample.pdf'  )
    sample_html        = os.path.join( local_dir, '2011-09-01-sample.html' )
    expected_data_json = os.path.join( local_dir, '2011-09-01-sample.json' )


    @unittest.skip( "Tests not written yet" )
    def test_converting_pdf_to_html(self):
        # FIXME - write these tests on a machine that supports the conversion
        pass


    
    def test_converting_pdf_to_html(self):
        """Test that the pdf becomes the html that we expect"""
        pdf_file = open( self.sample_pdf, 'r' )
        html = Source.convert_pdf_to_html( pdf_file )

        expected_html = open( self.sample_html, 'r' ).read()
        
        self.assertEqual( html, expected_html )


    def test_converting_html_to_data(self):
        """test the convert_pdf_to_data function"""
        
        html_file = open( self.sample_html, 'r')
        html = html_file.read()

        data = Source.convert_html_to_data( html=html )
                
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
        
        