from django.conf import settings
from django.db import IntegrityError

import pprint

from comments2.models import Comment
from comments2.tests.models import RockStar
from comments2.tests.test_base import CommentsTestBase

class CommentsBasics(CommentsTestBase):

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

