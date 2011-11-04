from djangomechanize import DjangoMechanizeTestCase
import urllib

from django.conf import settings

from django.contrib.auth.models import User
from django.utils import unittest
from django.test import TestCase
from django.core.urlresolvers import reverse

from user_profile.models import UserProfile

# gather the twitter details. Do this here so that the values can be used in the
# skip decorators.
twitter_username = settings.TEST_TWITTER_USERNAME
twitter_password = settings.TEST_TWITTER_PASSWORD
twitter_app_enabled = 'twitter' in settings.SOCIAL_AUTH_ENABLED_BACKENDS
can_test_twitter = twitter_app_enabled and twitter_username and twitter_password
def can_test_twitter_skip_message():
    if not twitter_app_enabled:
        return "Twitter auth not configured, add TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET to your settings"
    else:
        return "Do not have twitter login details, add TEST_TWITTER_USERNAME and TEST_TWITTER_PASSWORDWORD to your settings"

@unittest.skipUnless( can_test_twitter, can_test_twitter_skip_message() )
class TwitterTestCase(DjangoMechanizeTestCase):

    def setUp(self):
        # need to call the parent setup to initialize the browser
        super(TwitterTestCase, self).setUp()

        self.twitter_homepage_url = 'http://twitter.com/'
        

    def login_to_twitter(self):
        b = self.browser
        b.open( self.twitter_homepage_url )

        b.select_form(nr=1)
        b['session[username_or_email]'] = twitter_username
        b['session[password]']          = twitter_password
        b.submit()

        # check that we are logged in - this can break because we have the wrong
        # login '/#!/login/error' details, or because we've been presented with a
        # captcha '/#!/login/captcha' (which appears to be IP address related). 
        self.assertEqual( b.geturl(), self.twitter_homepage_url )


    def deauthorize_application(self):
        b = self.browser
        # b.open( 'http://twitter.com/settings/applications' )

        # no doubt out of date
        # data = urllib.urlencode( dict(
        #         authenticity_token= 'be2f7dfeedeb0acd2beb1eb8bfaba5e16505e155',
        #         token             = '15722485-oRIsEvNrfquBbRUKWQ2fqdTvuhpNHqeLrnUNs0Q',
        #         twttr             = 'true',
        # ) )
        # 
        # print data
        # 
        # # This should really be a post - no idea how to explicitly force one. 
        # b.open( 'http://twitter.com/oauth/revoke', data )


    def test_account_creation(self):
        b = self.browser

        self.login_to_twitter()
        self.deauthorize_application()
        
        twitter_login_url = reverse( 'socialauth_begin', args=['twitter'] )
        
        b.open(self.browser_url( twitter_login_url ))
        
        # response = self.client.get(self.reverse('socialauth_begin', 'twitter'))
        # # social_auth must redirect to service page
        # self.assertEqual(response.status_code, 302)
        # 
        # # Open first redirect page, it contains user login form because
        # # we don't have cookie to send to twitter
        # login_content = self.get_content(response['Location'])
        # parser = FormParserByID('login_form')
        # parser.feed(login_content)
        # auth = {'session[username_or_email]': self.user,
        #         'session[password]': self.passwd}
        # 
        # # Check that action and values were loaded properly
        # self.assertTrue(parser.action)
        # self.assertTrue(parser.values)
        # 
        # # Post login form, will return authorization or redirect page
        # parser.values.update(auth)
        # content = self.get_content(parser.action, data=parser.values)
        # 
        # # If page contains a form#login_form, then we are in the app
        # # authorization page because the app is not authorized yet,
        # # otherwise the app already gained permission and twitter sends
        # # a page that redirects to redirect_url
        # if 'login_form' in content:
        #     # authorization form post, returns redirect_page
        #     parser = FormParserByID('login_form').feed(content)
        #     self.assertTrue(parser.action)
        #     self.assertTrue(parser.values)
        #     parser.values.update(auth)
        #     redirect_page = self.get_content(parser.action, data=parser.values)
        # else:
        #     redirect_page = content
        # 
        # parser = RefreshParser()
        # parser.feed(redirect_page)
        # self.assertTrue(parser.value)
        # 
        # response = self.client.get(self.make_relative(parser.value))
        # self.assertEqual(response.status_code, 302)
        # location = self.make_relative(response['Location'])
        # login_redirect = getattr(settings, 'LOGIN_REDIRECT_URL', '')
        # self.assertTrue(location == login_redirect)
