from __future__ import absolute_import

import urllib
from time import sleep

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import unittest

from selenium.common.exceptions import NoSuchElementException

from django_selenium.testcases import SeleniumTestCase

# Reference pages for selenium commands:
#   driver:   http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html
#   elements: http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html

class MzalendoSeleniumTestCase(SeleniumTestCase):
    """Wrapper around SeleniumTestCase with some helpful additions"""

    def setUp(self):
        super(MzalendoSeleniumTestCase, self).setUp()

        # don't wait too long for things
        self.driver.implicitly_wait(5)


    def get_current_user_id(self):
        """Returns current user id, or None if not logged in"""
        user_id = self.driver.find_element_by_id('current_user_id').text
        return int(user_id) or None


    def get_current_user(self):
        """Returns current User object, or None if not logged in"""
        user_id = self.get_current_user_id()

        if user_id:
            return User.objects.get( id=user_id )
        
        return None
    

# gather the twitter details. Do this here so that the values can be used in the
# skip decorators.
twitter_username  = settings.TEST_TWITTER_USERNAME
twitter_password  = settings.TEST_TWITTER_PASSWORD
twitter_real_name = settings.TEST_TWITTER_REAL_NAME
twitter_app_enabled = 'twitter' in settings.SOCIAL_AUTH_ENABLED_BACKENDS

# can twitter actually be tested?
twitter_can_be_tested = twitter_app_enabled and twitter_username and twitter_password and twitter_real_name

# prepare a message to show to users if it can't
if twitter_can_be_tested:
    twitter_skip_message = ''
elif not twitter_app_enabled:
    twitter_skip_message = "Twitter auth not configured, add TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET to your settings"
else:
    twitter_skip_message = "Do not have twitter login details, add TEST_TWITTER_USERNAME, TEST_TWITTER_PASSWORD and TEST_TWITTER_APP_NAME to your settings"

@unittest.skipUnless( twitter_can_be_tested, twitter_skip_message )
class TwitterSeleniumTestCase(MzalendoSeleniumTestCase):
    """
    Twitter related add ons.

    Tests based on this test case will be automatically skipped if the details
    required for twitter testing are missing, and a message telling you haw to
    enable them produced instead.
    """

    def setUp(self):
        super(TwitterSeleniumTestCase, self).setUp()

        # make local copies of the twitter details so that we can access them
        # in the test scripts
        self.twitter_username  = twitter_username
        self.twitter_password  = twitter_password
        self.twitter_real_name = twitter_real_name
        

    def twitter_get_username_field(self):
        return self.driver.find_element_by_css_selector("form.signin.js-signin > fieldset.textbox > label.username.js-username > input[name=\"session[username_or_email]\"]")


    def twitter_get_password_field(self):
        return self.driver.find_element_by_css_selector("form.signin.js-signin > fieldset.textbox > label.password > input[name=\"session[password]\"]")


    def twitter_enter_username_and_password(self, submit=True):
        self.twitter_get_username_field().clear()
        self.twitter_get_username_field().send_keys(twitter_username)
        self.twitter_get_password_field().clear()
        self.twitter_get_password_field().send_keys(twitter_password)
        if submit:
            self.twitter_get_username_field().submit()


    def twitter_login(self):
        driver = self.driver
        driver.get("https://twitter.com/#!/login/")

        # Perhaps we are already logged in?
        if not self.is_text_present(twitter_username):

            self.twitter_enter_username_and_password()

            if 'captcha' in driver.current_url:
                self.twitter_enter_username_and_password(submit=False)

                while 'captcha' in driver.current_url:
                    print "Please complete the twitter captcha and submit the form"
                    sleep(2)

        self.assertEquals( driver.current_url, "http://twitter.com/")
        self.assertTrue(twitter_username in self.find_element_by_id('screen-name').text)


    def twitter_revoke_access_to_test_app(self):
        driver = self.driver
        driver.get("http://twitter.com/settings/applications")

        try:
            # Possibly bad assumption - there will be only one app to revoke
            driver.find_element_by_link_text("Revoke Access").click()
            sleep(2)
        except NoSuchElementException:
            pass

