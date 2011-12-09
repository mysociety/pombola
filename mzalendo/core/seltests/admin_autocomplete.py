from mzalendo.testing.selenium import MzalendoSeleniumTestCase

# from mzalendo.core.models import Person
# from mzalendo.comments2.models import Comment

class AdminTestCase(MzalendoSeleniumTestCase):
    
    fixtures = ['test_data']

    def test_person_position_inline_autocomplete(self):
        driver = self.driver

        self.login_to_admin('superuser')

        # Go to the joe bloggs entry
        driver.find_element_by_link_text("Persons").click()
        driver.find_element_by_link_text("joseph-bloggs").click()

        # check that the parliament is not on the page
        self.assertFalse( 'Parliament (Political)' in self.page_source )

        # Start typing 'parl' into the field
        driver.find_element_by_id("id_position_set-0-organisation_text").clear()
        driver.find_element_by_id("id_position_set-0-organisation_text").send_keys("pa")

        # click the entry that pops up
        driver.find_element_by_css_selector("ul.ui-autocomplete li a").click()

        # check that the text is now on the page
        self.assertTrue( 'Parliament (Political)' in self.page_source )


    def test_position_person_autocomplete(self):
        driver = self.driver

        self.login_to_admin('superuser')

        # Go to the joe bloggs entry
        driver.find_element_by_link_text("Positions").click()
        driver.find_element_by_link_text("Add position").click()

        # check that the parliament is not on the page
        self.assertFalse( 'Joseph Jeremiah Bloggs' in self.page_source )

        # Start typing 'parl' into the field
        driver.find_element_by_id("id_person_text").clear()
        driver.find_element_by_id("id_person_text").send_keys("jos")

        # click the entry that pops up
        driver.find_element_by_css_selector("ul.ui-autocomplete li a").click()

        # check that the text is now on the page
        self.assertTrue( 'Joseph Jeremiah Bloggs' in self.page_source )
