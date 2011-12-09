from django.core.urlresolvers import reverse
from mzalendo.testing.selenium import MzalendoSeleniumTestCase

class CoreTestCase(MzalendoSeleniumTestCase):
    

    def test_home(self):
        self.open_url(reverse('home'))
        self.failUnless(self.is_text_present('Mzalendo'))
        self.assertEquals(self.get_title(), 'Home :: Mzalendo')


    def test_static(self):
        """Test that the static files are being served"""

        self.open_url('/static/static_test.txt')
        self.assertTrue( 'static serving works!' in self.page_source )


    def test_404(self):
        """Test that proper 404 page is being shown"""
        self.open_url('/hash/bang/bosh')
        self.assertTrue( 'Page Not Found - 404' in self.text)


    def test_user_not_logged_in(self):
        """Test that by default user is not logged in"""
        self.open_url('/')

        self.assertEqual( self.get_current_user_id(), None )
        self.assertEqual( self.get_current_user(), None )
