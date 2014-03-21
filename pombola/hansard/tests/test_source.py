import datetime
import os
import time
import json
import tempfile
from collections import namedtuple
import subprocess

from django.test import TestCase
from django.utils import unittest

from pombola.hansard.models import Source, SourceUrlCouldNotBeRetrieved


class FakeHttp(object):

    def __init__(self, status_code=200):
        self.status_code = status_code

    def request(self, _):
        FakeResponse = namedtuple('FakeResponse', ['status'])
        # With the tests as they are at the moment, the response could
        # actually be any data, but might as well make it HTML:
        return FakeResponse(self.status_code), """<!doctype html>
<html lang=en>
  <head>
    <meta charset=utf-8>
    <title>Example Document</title>
  </head>
  <body>
    <p>Some text here...</p>
  </body>
</html>"""


class HansardSourceTest(TestCase):

    def setUp(self):
        """Create a test source"""
        source = Source(
            name = 'Test Source',
            url  = 'http://example.com/whatever',
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
        self.assertTrue( len( source.file(http_object=FakeHttp()).read() ) )
        self.assertTrue( os.path.exists( cache_file_path ))

        # change file, retrieve again and check we get cached version
        self.assertTrue( os.path.exists( cache_file_path ))
        added_text = "some random testing nonsense"
        self.assertFalse( added_text in source.file(http_object=FakeHttp()).read() )
        with open(cache_file_path, "a") as append_to_me:
            append_to_me.write("\n\n" + added_text + "\n\n")        
        self.assertTrue( added_text in source.file(http_object=FakeHttp()).read() )
        
        # delete the object - check cache file gone to
        source.delete()
        self.assertFalse( os.path.exists( cache_file_path ))
        
        # check that the object is gone
        self.assertFalse( Source.objects.filter(name="Test Source").count() )


    def test_source_file_404(self):
        """Check that urls that 404 are handled correctly"""
        source = self.source
        source.url = source.url + 'xxx'        
        self.assertRaises(
            SourceUrlCouldNotBeRetrieved,
            Source.file,
            source,
            http_object=FakeHttp(404))
        self.assertFalse( os.path.exists( source.cache_file_path() ))


    def test_requires_processing(self):
        """Check requires_processing qs works"""
        
        # There should just be one source that needs processing
        self.assertEqual( Source.objects.all().requires_processing().count(), 1 )


        # Check that a source that we have attempted to process, but not successfully is not tried again
        self.source.last_processing_attempt = datetime.datetime.now()
        self.source.last_processing_success = None
        self.source.save()

        # none should match now
        self.assertEqual( Source.objects.all().requires_processing().count(), 0 )


        # give the source a last_processing_success time
        self.source.last_processing_attempt = datetime.datetime.now()
        self.source.last_processing_success = datetime.datetime.now()
        self.source.save()

        # none should match now
        self.assertEqual( Source.objects.all().requires_processing().count(), 0 )




