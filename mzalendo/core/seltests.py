from django.core.urlresolvers import reverse
from django_selenium.testcases import SeleniumTestCase

class MyTestCase(SeleniumTestCase):

    def test_home(self):
        self.open_url(reverse('home'))
        # import time
        # # Sleep to check browser is opened
        # time.sleep(2)
        self.failUnless(self.is_text_present('Mzalendo'))
        self.assertEquals(self.get_title(), 'Home :: Mzalendo')
