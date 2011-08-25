import re

import settings

from django.core import mail
from django_webtest import WebTest
from core         import models
from django.test.client import Client
from django.contrib.auth.models import User


class PersonTest(WebTest):
    def setUp(self):
        self.person = models.Person(
            legal_name = 'Test Person',
            slug       = 'test-person',
        )
        self.person.save()
        
    def test_unicode(self):
        """Check that missing attributes don't crash"""
        
        position = models.Position(
            person = self.person,
        )
        self.assertEqual( str(position), 'Test Person (??? at ???)' )

