import re

import settings

from django.core import mail
from django_webtest import WebTest
from core         import models
from django.test.client import Client
from django.contrib.auth.models import User


class AccountTest(WebTest):
    def setUp(self):
        pass
        
    def test_create_account(self):
        app = self.app

        # go to home page, go to login page, go to new account page
        res = (
            app
              .get( '/' )
              .click( description='login' )
              .click( description='Need an account' )
        )
        
        # create an account
        form = res.form
        form['username']  = 'test_user'
        form['email']     = 'test@example.com'
        form['password1'] = 's3cr3t'
        form['password2'] = 's3cr3t'
        res = form.submit()
        
        # check that user created but not active
        user = User.objects.get(username='test_user')
        self.assertFalse( user.is_active )

        # check that an email has been sent
        self.assertEqual(len(mail.outbox), 1)
        confirm_url = re.search( r'/accounts/activate/\S+', mail.outbox[0].body ).group()
        res = app.get( confirm_url, auto_follow=True )
        self.assertContains( res, 'activation complete' )
        
        # check that user now active
        user = User.objects.get(username='test_user')
        self.assertTrue( user.is_active )

        # check that the user con login
        res = res.click(description='login', index=1)
        form = res.form
        form['username'] = 'test_user'
        form['password'] = 's3cr3t'
        res = form.submit().follow()
        
        # check that we are back on homepage and logged in
        self.assertEqual('/',  res.request.path, 'back on home page')
        self.assertContains( res, 'test_user' )
        
        # logout
        res = res.click( description='logout' )
        self.assertEqual('/accounts/logout/',  res.request.path)
        
