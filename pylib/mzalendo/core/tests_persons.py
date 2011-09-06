import re

import settings

from django.core import mail
from django_webtest import WebTest
from core         import models
from django.test.client import Client
from django.contrib.auth.models import User


class PersonTest(WebTest):
    def setUp(self):
        pass
        
    def test_naming(self):
        
        # create a test person
        person = models.Person(
            legal_name="Alfred Smith"
        )
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name(), "Alfred Smith" )
        self.assertEqual( person.additional_names(), [] )
        
        # Add an alternative name
        person.other_names = "Freddy Smith"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name(), "Freddy Smith" )
        self.assertEqual( person.additional_names(), [] )

        # Add yet another alternative name
        person.other_names = "Fred Smith\nFreddy Smith"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name(), "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )

        # Add yet another alternative name
        person.other_names = "\n\nFred Smith\n\nFreddy Smith\n\n\n"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name(), "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )
        