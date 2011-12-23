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
        self.create_feedback_using_narrow_screen('narrow window')

        # use a large window so we get the dialog
        self.create_feedback_using_wide_screen('wide window')

        # log in and check that the user is stored.
        self.login('superuser')
        self.create_feedback_using_wide_screen('logged_in_user')

        # check that the two bits of feedback are stored in the the database
        self.assertEqual( Feedback.objects.all().count(), 3 )

        actual = {}
        for fb in Feedback.objects.all():
            if fb.user: actual[fb.comment] = fb.user.username
            else:       actual[fb.comment] = None

        self.assertEqual(
            actual,
            {
                'narrow window':  None,
                'wide window':    None,
                'logged_in_user': 'superuser',
            }
        )


    def create_feedback_using_wide_screen(self, message):
        self.resize_to_desktop()
        self.open_url(reverse('home'))        

        driver = self.driver

        driver.find_element_by_link_text("Give us feedback").click()
        driver.find_element_by_id("id_comment").clear()
        driver.find_element_by_id("id_comment").send_keys(message)
        driver.find_element_by_xpath("//input[@value='Leave feedback']").click()
        time.sleep(1) # just to let things catch up
        self.failUnless(self.thanks_text in driver.page_source)
        driver.find_element_by_css_selector("span.ui-icon.ui-icon-closethick").click()


    def create_feedback_using_narrow_screen(self, message):
        self.resize_to_mobile()
        self.open_url(reverse('home'))

        driver = self.driver

        driver.find_element_by_link_text("Give us feedback").click()
        driver.find_element_by_id("id_comment").clear()
        driver.find_element_by_id("id_comment").send_keys(message)
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        self.failUnless(self.thanks_text in driver.page_source)
        driver.find_element_by_link_text("page you were on").click()
        