from django.conf import settings

from django_webtest import WebTest
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.db import IntegrityError

import pprint

from comments2.models import Comment
from comments2.tests.models import RockStar

class CommentsBasics(WebTest):
    urls = 'comments2.urls'
    fixtures = ['comments2-test-data.json']
    
    def setUp(self):
    
        self.test_object  = RockStar.objects.get(name='Slash')
        self.test_user    = User.objects.get(username = 'test-user')
        self.trusted_user = User.objects.get(username = 'trusted-user')

        # check that the trusted user has the correct permissions - don't trust
        # that the permission id listed in the fixture won't change
        self.assertFalse( self.test_user.has_perm('comments2.can_post_without_moderation') )
        self.assertTrue( self.trusted_user.has_perm('comments2.can_post_without_moderation') )

        # Useful to spit out the database setup
        # from django.core.management import call_command
        # call_command(
        #     'dumpdata',
        #     'auth.User', 'comments2.RockStar',
        #     indent=4, natural=True
        # )

    def test_sanity(self):
        self.assertEqual( 2+2, 4 )
        
        
    def test_automoderate(self):
        """check that the can_post_without_moderation perm is respected"""
        def create_test_get_status(user):
            comment = Comment(
                content_object  = self.test_object,
                user    = user,
                title   = 'Foo',
                comment = 'Foo content',
            )
            comment.save()
            return comment.status
            
        self.assertEqual( create_test_get_status( self.test_user ),    'unmoderated' )
        self.assertEqual( create_test_get_status( self.trusted_user ), 'approved'    )
    

    def test_user_is_required(self):
        """check that the user is required"""
        def create_no_user_comment():
            comment = Comment(
                content_object  = self.test_object,
                # user  <-- deliberately missing
                title   = 'Foo',
                comment = 'Foo content',
            )
            comment.save()
    
        self.assertRaises( IntegrityError, create_no_user_comment )

