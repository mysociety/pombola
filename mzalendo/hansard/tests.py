import os
import datetime
import time

from django.test import TestCase
from hansard.models import Source

class HansardTest(TestCase):

    def setUp(self):
        source = Source(
            name = 'Test Source',
            url  = 'http://www.mysociety.org/robots.txt',
            date = datetime.date( 2001, 11, 14),
        )
        source.save()
        self.source = source


    def test_source_file(self):
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
        source = self.source
        source.url = source.url + 'xxx'        
        self.assertEqual( source.file(), None )
        self.assertFalse( os.path.exists( source.cache_file_path() ))


    def test_requires_processing(self):
        
        # There should just be one source that needs processing
        self.assertEqual( Source.objects.all().requires_processing().count(), 1 )

        # give the source a last_processed time
        self.source.last_processed = datetime.date.today()
        self.source.save()

        # none should match now
        self.assertEqual( Source.objects.all().requires_processing().count(), 0 )
