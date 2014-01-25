import os

from django.test import TestCase
from django.core.files import File
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from models import Image

from nose.tools import nottest

from sorl.thumbnail import get_thumbnail

class ImageTest(TestCase):

    @nottest
    def get_test_file_content(self, filename):
        """
        Open the given file an dreturn it
        """
        full_path = os.path.join(
            os.path.abspath( os.path.dirname(__file__) ),
            'tests',
            filename,
        )

        return File( open(full_path) )
    
    def reload_image(self, image):
        """because there is no reload in Django models (silly really)"""
        return Image.objects.get(id=image.id)
    
    def test_uploading(self):
        """
        Test that uploading an image works
        """
        
        test_site = Site.objects.all()[0]
        test_site_ct = ContentType.objects.get_for_model(test_site)
        test_site_id = test_site.id
        
        # check that there are no images
        self.assertEqual( Image.objects.all().count(), 0 )
        
        # create an image
        first = Image(
            content_type = test_site_ct,
            object_id    = test_site_id,
            source       = 'test directory',            
        )
        first.image.save(
            name    = 'foo.png',
            content = self.get_test_file_content('foo.png'),
        )
        
        # check that the is_primary is true
        self.assertTrue( first.is_primary )
        
        # create another image
        second = Image(
            content_type = test_site_ct,
            object_id    = test_site_id,
            source       = 'test directory',            
        )
        second.image.save(
            name    = 'bar.png',
            content = self.get_test_file_content('bar.png'),
        )
        
        # check that is_primary is false
        self.assertTrue( self.reload_image(first).is_primary )
        self.assertFalse( self.reload_image(second).is_primary )

        # change is_primary on second image
        second.is_primary = True
        second.save()
        
        # check that it changed on first too
        self.assertFalse( self.reload_image(first).is_primary )
        self.assertTrue( self.reload_image(second).is_primary )
        
        # create a third image with is_primary true at the start
        third = Image(
            content_type = test_site_ct,
            object_id    = test_site_id,
            source       = 'test directory',            
            is_primary   = True,
        )
        third.image.save(
            name    = 'baz.png',
            content = self.get_test_file_content('baz.png'),
        )
        
        # check that is_primary is updated for all
        self.assertFalse( self.reload_image(first).is_primary )
        self.assertFalse( self.reload_image(second).is_primary )
        self.assertTrue(  self.reload_image(third).is_primary )
        
        # Now try to create an thumbnail with sorl.  If this fails
        # with "IOError: decoder zip not available", then probably
        # this is a problem with an old version of PIL, or one that
        # wasn't installed when the right build dependencies were
        # present.  The simplest solution in most solutions is:
        #   pip uninstall PIL
        #   pip install pillow

        im = get_thumbnail(third.image, '100x100', crop='center', quality=99)
