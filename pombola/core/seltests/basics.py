from django.core.urlresolvers import reverse
from pombola.testing.selenium import PombolaSeleniumTestCase

class CoreTestCase(PombolaSeleniumTestCase):
    

    def test_home(self):
        self.open_url(reverse('home'))
        self.assertRegexpMatches(self.get_title(), 'Home')

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
