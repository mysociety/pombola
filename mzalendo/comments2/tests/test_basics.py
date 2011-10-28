from django.conf import settings

from django_webtest import WebTest
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.db import IntegrityError

import pprint

from comments2.models import Comment
from comments2.tests.models import RockStar

class CommentsCase(WebTest):
    def setUp(self):

        # use the sites as the test object as we can be sure that there is one
        self.test_object, created = RockStar.objects.get_or_create(
            name   = 'Slash',
        )

        # create a normal user
        self.test_user = User.objects.create_user(
            username = 'test-user',
            email    = 'test-user@example.com',
            password = 'secret',
        )

        # create a user we trust - has the 'can_post_without_moderation' permission
        self.trusted_user = User.objects.create_user(
            username = 'trusted-user',
            email    = 'trusted-user@example.com',
            password = 'secret',
        )
        can_post_without_moderation = Permission.objects.get(codename='can_post_without_moderation')
        self.trusted_user.user_permissions.add( can_post_without_moderation )


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



    # def get_comments(self, test_object, user=None):
    #     return (
    #         self
    #           .app
    #           .get( test_object.get_absolute_url(), user=user )
    #           .click(description=r'^\d+ comments?$')
    #     )
    # 
    # def get_comments_add(self, test_object, user=None):
    #     return (
    #         self
    #           .get_comments( test_object, user )
    #           .click( description='Add your own comment' )
    #     )
    # 
    # def test_leaving_comment(self):
    #     # go to the test_object and check that there are no comments
    #     test_object = self.test_object
    #     app = self.app
    #     response = self.get_comments( test_object )
    #     
    #     # check that anon can't leave comments
    #     self.assertTemplateNotUsed( response, 'comments/form.html' )
    #     self.assertContains( response, "login to add your own comment" )
    #     
    #     # check that there is now a comment form
    #     response = self.get_comments_add( test_object, user=self.test_user  )
    #     
    #     self.assertTemplateUsed( response, 'comments/form.html' )
    #     
    #     # leave a comment
    #     form = response.forms['comment_form']
    #     form['title']   = 'Test Title'
    #     form['comment'] = 'Test comment'
    #     form_response = form.submit()
    #     self.assertEqual(response.context['user'].username, 'test-user')
    # 
    #     # check that the comment is correct and pending review
    #     comment = mz_comments.models.CommentWithTitle.objects.filter(
    #         content_type = ContentTypeManager().get_for_model(self.test_object),
    #         object_pk    = self.test_object.id,
    #     )[0]
    #     self.assertEqual( comment.title, 'Test Title' )
    #     self.assertEqual( comment.comment, 'Test comment' )
    #     self.assertEqual( comment.name, 'test-user' )
    #     self.assertEqual( comment.is_public, False )
    #     self.assertEqual( comment.is_removed, False )
    #     
    #     # check it is not visible on site
    #     res = self.get_comments( test_object )
    #     self.assertNotContains( res, comment.title )
    #             
    #     # approve the comment
    #     comment.is_public = True
    #     comment.save()
    #     
    #     # check that it is shown on site
    #     self.assertContains( self.get_comments( test_object ), comment.title )
    #     
    #     # flag the comment
    #     comment.is_removed = True
    #     comment.save()
    #     self.assertNotContains( self.get_comments( test_object ), comment.title )
    #     
    #     # delete the comment
    #     comment.delete()
    #     # check that comment not shown
    #     res =  self.get_comments( test_object )
    #     self.assertNotContains( res, comment.title )
    #     self.assertNotContains( res, 'comment removed' )
    # 
    # def test_trusted_users(self):
    #     """Test that users in the 'trusted' group have their comments posted at once"""
    # 
    #     app = self.app
    # 
    #     test_object = self.test_object
    #     trusted_user = self.trusted_user
    #     comment_title = "Trusted user comment"
    #     
    #     # get the test_object page with comment form on it
    #     res = self.get_comments_add( test_object, trusted_user )
    # 
    #     # leave a comment
    #     form = res.forms['comment_form']
    #     form['title']   = comment_title
    #     form['comment'] = 'Test comment'
    #     form_response = form.submit()
    # 
    #     # check that the comment is correct and public
    #     comment = mz_comments.models.CommentWithTitle.objects.filter(
    #         content_type = ContentTypeManager().get_for_model(self.test_object),
    #         object_pk    = self.test_object.id,
    #     )[0]
    #     self.assertEqual( comment.title, comment_title )
    #     self.assertEqual( comment.is_public, True )
    #     self.assertEqual( comment.is_removed, False )
    #     
    #     # check that it is shown on site
    #     self.assertContains( self.get_comments( test_object ), comment_title )
    #     
