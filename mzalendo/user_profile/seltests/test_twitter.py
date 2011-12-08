from mzalendo.testing import TwitterSeleniumTestCase

class TwitterTestCase(TwitterSeleniumTestCase):


    def test_create_account_via_twitter(self):
        driver = self.driver

        self.twitter_login()
        self.twitter_revoke_access_to_test_app()
        
        start_url = '/person/all'
        
        self.open_url(start_url)

        # Go to twitter and cancel the login
        self.twitter_click_login_link_on_mzalendo_site()
        driver.find_element_by_link_text("Cancel, and return to app").click()
        
        # Check that the text is helpful
        self.assertTrue( '/accounts/login/' in driver.current_url )
        self.assertTrue(
            'You tried to login using a website like Twitter' in self.page_source
        )

        # Note - ideally even the failed login would lead to us retaining the
        # 'next' parameter so that an alternative login would work. Have created an
        # issue for this: https://github.com/omab/django-social-auth/issues/192
        
        # for now go back to the page we want to return to
        self.open_url(start_url)

        # go to Twitter and confirm the log in
        self.twitter_click_login_link_on_mzalendo_site()
        driver.find_element_by_id("allow").click()

        # check that we are now logged in
        self.assert_user_logged_in()
        
        # check that we are still on the start_url page
        # print start_url
        # print driver.current_url
        self.assertTrue( start_url in driver.current_url )

        # check that the user created has the correct name
        user = self.get_current_user()
        self.assertTrue( user )
        self.assertEqual( user.get_full_name(), self.twitter_real_name )

        # change the user's name
        user.first_name = "Firstly"
        user.last_name = "Lastly"
        user.save()

        # now logout of Mzalendo
        self.logout()

        # log back in using twitter - should not need to approve anything
        self.twitter_click_login_link_on_mzalendo_site()
        self.assert_user_logged_in()
        
        # check that the name has not been updated
        user = self.get_current_user()
        self.assertTrue( user )
        self.assertEqual( user.get_full_name(), "Firstly Lastly" )
