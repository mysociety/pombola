import time

from django.core.urlresolvers import reverse
from mzalendo.testing.selenium import MzalendoSeleniumTestCase

from feedback.models import Feedback

class FeedbackTestCase(MzalendoSeleniumTestCase):

    fixtures = ['test_data']    

    thanks_text = 'Thank you for your feedback!'

    def test_all(self):
        driver = self.driver
        self.open_url(reverse('home'))


        # make the window small so that the mobile js is loaded
        self.create_feedback_using_narrow_screen(message='narrow window')

        # use a large window so we get the dialog
        self.create_feedback_using_wide_screen(message='wide window')

        # Test again with emails
        self.create_feedback_using_narrow_screen(message='narrow window + email', email="foo@example.com")
        self.create_feedback_using_wide_screen(message='wide window + email', email="foo@example.com")

        # log in and check that the user is stored.
        self.login('superuser')
        self.create_feedback_using_wide_screen(message='logged_in_user')

        actual = {}
        for fb in Feedback.objects.all():
            data = {}

            data['email'] = fb.email

            if fb.user: data['username'] = fb.user.username
            else:       data['username'] = None

            actual[fb.comment] = data

        # import pprint
        # pprint.pprint(actual)

        self.assertEqual(
            actual,
            {
                'narrow window':         {'username': None,        'email': '', },
                'wide window':           {'username': None,        'email': '', },
                'narrow window + email': {'username': None,        'email': 'foo@example.com', },
                'wide window + email':   {'username': None,        'email': 'foo@example.com', },
                'logged_in_user':        {'username': 'superuser', 'email': '', },
            }
        )


    def create_feedback_using_wide_screen(self, message, email=''):
        self.resize_to_desktop()
        self.open_url(reverse('home'))        

        driver = self.driver

        driver.find_element_by_link_text("Give us feedback").click()
        self.fill_in_feedback_form(message, email)
        driver.find_element_by_css_selector("span.ui-icon.ui-icon-closethick").click()


    def create_feedback_using_narrow_screen(self, message, email=''):
        self.resize_to_mobile()
        self.open_url(reverse('home'))

        driver = self.driver

        driver.find_element_by_link_text("Give us feedback").click()
        self.fill_in_feedback_form(message, email)
        driver.find_element_by_link_text("page you were on").click()
    
    
    def fill_in_feedback_form(self, message, email):
        driver = self.driver
        driver.find_element_by_id("id_comment").clear()
        driver.find_element_by_id("id_comment").send_keys(message)
        driver.find_element_by_id("id_email").clear()
        driver.find_element_by_id("id_email").send_keys(email)
        driver.find_element_by_xpath("//input[@value='Send feedback']").click()
        time.sleep(1) # just to let things catch up
        self.failUnless(self.thanks_text in driver.page_source)
        