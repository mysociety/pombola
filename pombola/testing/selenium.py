from __future__ import absolute_import

from django.contrib.auth.models import User
from django.core.management import call_command 

from django_selenium.testcases import SeleniumTestCase

# Reference pages for selenium commands:
#   driver:   http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html
#   elements: http://selenium.googlecode.com/svn/trunk/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html

class PombolaSeleniumTestCase(SeleniumTestCase):
    """Wrapper around SeleniumTestCase with some helpful additions"""

    def setUp(self):
        super(PombolaSeleniumTestCase, self).setUp()

        # run the collectstatic command - so that all the static files can be served.
        call_command('collectstatic', interactive=False) 

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
    

    def assert_user_logged_in(self):
        self.assertTrue( self.get_current_user_id() )


    def assert_user_logged_out(self):
        self.assertFalse( self.get_current_user_id() )


    def login_to_admin(self, username, password='secret'):
        """Login to the admin interface"""

        self.driver.open_url("/admin/")
        
        self.driver.find_element_by_id("id_username").clear()
        self.driver.find_element_by_id("id_username").send_keys(username)
        self.driver.find_element_by_id("id_password").clear()
        self.driver.find_element_by_id("id_password").send_keys(password)
        self.driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def resize_to_mobile(self):
        self.driver.set_window_size(400, 600)

    def resize_to_desktop(self):
        self.driver.set_window_size(800, 1000)
    


