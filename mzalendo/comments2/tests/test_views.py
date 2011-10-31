from django.conf import settings

import pprint

from comments2.models import Comment, CommentFlag
from comments2.tests.models import RockStar
from comments2.tests.test_base import CommentsTestBase

class CommentsViews(CommentsTestBase):

    def get_comments(self, test_object, user=None):
        url = "/comments/for/%s/%s/" % ( test_object._meta.module_name, test_object.slug )
        return self.app.get( url, user=user )
    
    def get_comments_add(self, test_object, user=None):
        url = "/comments/for/%s/%s/add/" % ( test_object._meta.module_name, test_object.slug )
        return self.app.get( url, user=user )
    
    def test_leaving_comment(self):
        # go to the test_object and check that there are no comments
        test_object = self.test_object
        app = self.app
        
        # check that anon can't leave comments
        response = self.get_comments( test_object )
        self.assertContains( response, 'login to add your own comment' )
        response = self.get_comments_add( test_object )
        self.assertEqual( response.status, '302 FOUND' )
        
        # check that logged in users can
        response = self.get_comments( test_object, user=self.test_user )
        self.assertContains( response, 'Add your own comment' )
        response = self.get_comments_add( test_object, user=self.test_user )
        self.assertEqual( response.status, '200 OK' )
        
        # check that our comment is not in the system
        self.assertEqual( Comment.objects.filter(title="Test123").count(), 0 )
        
        # Fill in the comment form
        form = response.forms['add_comment']
        form['title']   = 'Test123'
        form['comment'] = 'Test comment'
        form_response = form.submit()
        self.assertEqual(response.context['user'].username, 'test-user')
        
        # check that our comment is in the system
        self.assertEqual( Comment.objects.filter(title="Test123").count(), 1 )
        comment = Comment.objects.get(title="Test123")
        self.assertEqual(comment.status, 'unmoderated')
        
        # check comment is not visible on site
        res = self.get_comments( test_object )
        self.assertNotContains( res, comment.title )
                
        # approve the comment
        comment.status = 'approved'
        comment.save()
        
        # check that it is shown on site
        self.assertContains( self.get_comments( test_object ), comment.title )
        
        # reject the comment
        comment.status = 'rejected'
        comment.save()
        self.assertNotContains( self.get_comments( test_object ), comment.title )
        
        # delete the comment
        comment.delete()
        # check that comment not shown
        res =  self.get_comments( test_object )
        self.assertNotContains( res, comment.title )

    def test_trusted_users(self):
        """Test that users in the 'trusted' group have their comments posted at once"""
        test_object = self.test_object
        trusted_user = self.trusted_user
        comment_title = "Trusted user comment"
        
        # get the test_object page with comment form on it
        res = self.get_comments_add( test_object, trusted_user )
    
        # leave a comment
        form = res.forms['add_comment']
        form['title']   = comment_title
        form['comment'] = 'Test comment'
        form_response = form.submit()
            
        # check that the comment is correct and public
        comment = Comment.objects.get(title=comment_title)
        self.assertEqual( comment.title, comment_title )
        self.assertEqual( comment.status, 'approved' )
        
        # check that it is shown on site
        self.assertContains( self.get_comments( test_object ), comment_title )
        
