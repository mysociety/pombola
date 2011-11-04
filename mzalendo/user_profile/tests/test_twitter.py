from django.conf import settings

from django.contrib.auth.models import User
from django.utils import unittest
from django.test import TestCase

from user_profile.models import UserProfile

# gather the twitter details. Do this here so that the values can be used in the
# skip decorators.
twitter_user = settings.TEST_TWITTER_USERNAME
twitter_pass = settings.TEST_TWITTER_PASSWORD
twitter_app_enabled = 'twitter' in settings.SOCIAL_AUTH_ENABLED_BACKENDS
can_test_twitter = twitter_app_enabled and twitter_user and twitter_pass
def can_test_twitter_skip_message():
    if not twitter_app_enabled:
        return "Twitter auth not configured, add TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET to your settings"
    else:
        return "Do not have twitter login details, add TEST_TWITTER_USERNAME and TEST_TWITTER_PASSWORDWORD to your settings"

class TwitterTestCase(TestCase):
    def setUp(self):
        pass

    @unittest.skipUnless( can_test_twitter, can_test_twitter_skip_message() )
    def test_account_creation(self):
        self.assertTrue( twitter_user )
        pass


#     def test_login_succeful(self):
#         response = self.client.get(self.reverse('socialauth_begin', 'twitter'))
#         # social_auth must redirect to service page
#         self.assertEqual(response.status_code, 302)
# 
#         # Open first redirect page, it contains user login form because
#         # we don't have cookie to send to twitter
#         login_content = self.get_content(response['Location'])
#         parser = FormParserByID('login_form')
#         parser.feed(login_content)
#         auth = {'session[username_or_email]': self.user,
#                 'session[password]': self.passwd}
# 
#         # Check that action and values were loaded properly
#         self.assertTrue(parser.action)
#         self.assertTrue(parser.values)
# 
#         # Post login form, will return authorization or redirect page
#         parser.values.update(auth)
#         content = self.get_content(parser.action, data=parser.values)
# 
#         # If page contains a form#login_form, then we are in the app
#         # authorization page because the app is not authorized yet,
#         # otherwise the app already gained permission and twitter sends
#         # a page that redirects to redirect_url
#         if 'login_form' in content:
#             # authorization form post, returns redirect_page
#             parser = FormParserByID('login_form').feed(content)
#             self.assertTrue(parser.action)
#             self.assertTrue(parser.values)
#             parser.values.update(auth)
#             redirect_page = self.get_content(parser.action, data=parser.values)
#         else:
#             redirect_page = content
# 
#         parser = RefreshParser()
#         parser.feed(redirect_page)
#         self.assertTrue(parser.value)
# 
#         response = self.client.get(self.make_relative(parser.value))
#         self.assertEqual(response.status_code, 302)
#         location = self.make_relative(response['Location'])
#         login_redirect = getattr(settings, 'LOGIN_REDIRECT_URL', '')
#         self.assertTrue(location == login_redirect)
