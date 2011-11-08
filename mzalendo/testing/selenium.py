from django_selenium.testcases import SeleniumTestCase
from django.contrib.auth.models import User

class MzalendoSeleniumTestCase(SeleniumTestCase):
    """Wrapper around SeleniumTestCase with some helpful additions"""

    def get_current_user_id(self):
        user_id = self.driver.find_element_by_id('current_user_id').text
        return int(user_id) or None

    def get_current_user(self):
        user_id = self.get_current_user_id()

        if user_id:
            return User.objects.get( id=user_id )
        
        return None