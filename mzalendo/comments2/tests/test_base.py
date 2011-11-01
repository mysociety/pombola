from django.conf import settings

from django_webtest import WebTest
from django.contrib.auth.models import User

from comments2.models import Comment
from comments2.tests.models import RockStar

class CommentsTestBase(WebTest):
    fixtures = ['comments2-test-data.json']
    
    def setUp(self):
        self.test_object  = RockStar.objects.get(name='Slash')
        self.test_user    = User.objects.get(username = 'test-user')
        self.trusted_user = User.objects.get(username = 'trusted-user')

    def tearDown(self):
        # Useful to spit out the database setup
        # from django.core.management import call_command
        # call_command(
        #     'dumpdata',
        #     'auth.User', 'comments2',
        #     indent=4, use_natural_keys=True
        # )
        pass

