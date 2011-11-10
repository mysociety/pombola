import urllib
from time import sleep

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest

from mzalendo.testing.selenium import MzalendoSeleniumTestCase
from selenium.common.exceptions import NoSuchElementException

from user_profile.models import UserProfile

# gather the twitter details. Do this here so that the values can be used in the
# skip decorators.
twitter_username  = settings.TEST_TWITTER_USERNAME
twitter_password  = settings.TEST_TWITTER_PASSWORD
twitter_real_name = settings.TEST_TWITTER_REAL_NAME
twitter_app_enabled = 'twitter' in settings.SOCIAL_AUTH_ENABLED_BACKENDS
can_test_twitter = twitter_app_enabled and twitter_username and twitter_password and twitter_real_name
def can_test_twitter_skip_message():
    if not twitter_app_enabled:
        return "Twitter auth not configured, add TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET to your settings"
    else:
        return "Do not have twitter login details, add TEST_TWITTER_USERNAME, TEST_TWITTER_PASSWORD and TEST_TWITTER_APP_NAME to your settings"

@unittest.skipUnless( can_test_twitter, can_test_twitter_skip_message() )
class TwitterTestCase(MzalendoSeleniumTestCase):

    # Reference pages for selenium commands:
    #   driver:   http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html
    #   elements: http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html


    def setUp(self):
        super(TwitterTestCase, self).setUp()

        # don't wait too long for things
        self.driver.implicitly_wait(5)


    def get_twitter_username_field(self):
        return self.driver.find_element_by_css_selector("form.signin.js-signin > fieldset.textbox > label.username.js-username > input[name=\"session[username_or_email]\"]")


    def get_twitter_password_field(self):
        return self.driver.find_element_by_css_selector("form.signin.js-signin > fieldset.textbox > label.password > input[name=\"session[password]\"]")

        
    def enter_username_and_password(self, submit=True):
        self.get_twitter_username_field().clear()
        self.get_twitter_username_field().send_keys(twitter_username)
        self.get_twitter_password_field().clear()
        self.get_twitter_password_field().send_keys(twitter_password)
        if submit:
            self.get_twitter_username_field().submit()


    def login_to_twitter(self):
        driver = self.driver
        driver.get("https://twitter.com/#!/login/")

        # Perhaps we are already logged in?
        if not self.is_text_present(twitter_username):

            self.enter_username_and_password()
            
            if 'captcha' in driver.current_url:
                self.enter_username_and_password(submit=False)
                
                while 'captcha' in driver.current_url:
                    print "Please complete the twitter captcha and submit the form"
                    sleep(2)

        self.assertEquals( driver.current_url, "http://twitter.com/")
        self.assertTrue(twitter_username in self.find_element_by_id('screen-name').text)


    def revoke_access_to_test_app(self):
        driver = self.driver
        driver.get("http://twitter.com/settings/applications")
        
        try:
            # Possibly bad assumption - there will be only one app to revoke
            driver.find_element_by_link_text("Revoke Access").click()
            sleep(2)
        except NoSuchElementException:
            pass


    def test_create_account_via_twitter(self):
        driver = self.driver

        self.login_to_twitter()
        self.revoke_access_to_test_app()
        
        self.open_url('/')

        # Go to twitter and cancel the login
        driver.find_element_by_link_text("twitter").click()
        driver.find_element_by_link_text("Cancel, and return to app").click()
        
        # Check that the text is helpful
        self.assertTrue( '/accounts/login/' in driver.current_url )
        self.assertTrue(
            'You tried to login using a website like Twitter' in self.page_source
        )

        # go to Twitter and confirm the log in
        driver.find_element_by_link_text("twitter").click()
        driver.find_element_by_id("allow").click()

        # check that we are now logged in
        self.assertTrue( '(logout)' in self.find_element_by_id('header').text )

        # check that the user created has the correct name
        user = self.get_current_user()
        self.assertEqual( user.get_full_name(), twitter_real_name )

        # change the user's name
        user.first_name = "Firstly"
        user.last_name = "Lastly"
        user.save()

        # now logout of Mzalendo
        driver.find_element_by_link_text("logout").click()
        self.assertTrue( '/accounts/logout/' in driver.current_url )
        self.assertTrue( 'logged out' in driver.find_element_by_id('content').text )

        # log back in using twitter - should not need to approve anything
        driver.find_element_by_link_text("twitter").click()
        self.assertTrue( '(logout)' in driver.find_element_by_id('header').text )
        
        # check that the name has not been updated
        user = self.get_current_user()
        self.assertEqual( user.get_full_name(), "Firstly Lastly" )
