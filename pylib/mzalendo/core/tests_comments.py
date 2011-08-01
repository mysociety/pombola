import settings

from django_webtest import WebTest
from core         import models
from tasks.models import Task
from django.test.client import Client
from django.contrib.auth.models import User

from django_date_extensions.fields import ApproximateDate
from django.contrib.contenttypes.models import ContentType

import pprint

class CommentsCase(WebTest):
    def setUp(self):
        self.person, created = models.Person.objects.get_or_create(
            first_name = 'Test',
            last_name  = 'Person',
            slug       = 'test-person',
        )
        
        self.test_user = User.objects.create_user(
            username = 'test-admin',
            email    = 'test-admin@example.com',
            password = 'secret',
        )

    def test_leaving_comment(self):
        # go to the person and check that there are no comments
        person = self.person
        app = self.app
        response = app.get( person.get_absolute_url() )
        self.assertEqual(response.status_int, 200)                
        
        # check that anon can't leave comments
        self.assertTemplateNotUsed( response, 'comments/form.html' )
        self.assertContains( response, "login to leave a comment" )
        
        # check that there is now a comment form
        response = app.get( person.get_absolute_url(), user=self.test_user )
        self.assertTemplateUsed( response, 'comments/form.html' )
        
        # leave a comment
        form = response.form
        form['title']   = 'Test Title'
        form['comment'] = 'Test comment'
        form_response = form.submit()
        self.assertEqual(response.context['user'].username, 'test-admin')

        # check that the comment is pending review
        # check it is not visible on site
        
        # approve the comment
        # check that it is shown on site
        
        # flag the comment
        # check that 'removed' notice is shown on site
        
        # delete the comment
        # check that comment not shown
        
        pass

