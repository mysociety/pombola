from django.contrib.auth.models import User
from django.test import TestCase

from user_profile.models import UserProfile

class ProfileTest(TestCase):

    def setUp(self):
        pass

    def test_profile_created_when_user_is(self):
        """
        Test the post_save signal creates a profile for all users.
        """
        
        user = User(
            username = "test-user",
            password = '',
        )
        user.save()
        
        self.assertTrue( user.get_profile() )
        
        
        # delete the user_profile and check that the method we call from the migration
        # will create the profiles too. We can't test the migration directly here as th
        # emigrations are not run to set up the database for the tests. 
        user.get_profile().delete()
        user = User.objects.get(id=user.id) # profile is cached

        try:
            user.get_profile()
            self.assertFalse(1) # fail if we get here
        except UserProfile.DoesNotExist:
            self.assertTrue(1) # profile does not exist

        UserProfile.objects.create_missing()
        
        user = User.objects.get(id=user.id) # profile is cached
        self.assertTrue( user.get_profile() )
        