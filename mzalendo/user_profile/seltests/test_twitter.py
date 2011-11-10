from mzalendo.testing import TwitterSeleniumTestCase

class TwitterTestCase(TwitterSeleniumTestCase):


    def test_create_account_via_twitter(self):
        driver = self.driver

        self.twitter_login()
        self.twitter_revoke_access_to_test_app()
        
        self.open_url('/')

        # Go to twitter and cancel the login
        self.click_twitter_login_link()
        driver.find_element_by_link_text("Cancel, and return to app").click()
        
        # Check that the text is helpful
        self.assertTrue( '/accounts/login/' in driver.current_url )
        self.assertTrue(
            'You tried to login using a website like Twitter' in self.page_source
        )

        # go to Twitter and confirm the log in
        self.click_twitter_login_link()
        driver.find_element_by_id("allow").click()

        # check that we are now logged in
        self.assertTrue( '(logout)' in self.find_element_by_id('header').text )

        # check that the user created has the correct name
        user = self.get_current_user()
        self.assertEqual( user.get_full_name(), self.twitter_real_name )

        # change the user's name
        user.first_name = "Firstly"
        user.last_name = "Lastly"
        user.save()

        # now logout of Mzalendo
        driver.find_element_by_link_text("logout").click()
        self.assertTrue( '/accounts/logout/' in driver.current_url )
        self.assertTrue( 'logged out' in driver.find_element_by_id('content').text )

        # log back in using twitter - should not need to approve anything
        self.click_twitter_login_link()
        self.assertTrue( '(logout)' in driver.find_element_by_id('header').text )
        
        # check that the name has not been updated
        user = self.get_current_user()
        self.assertEqual( user.get_full_name(), "Firstly Lastly" )
