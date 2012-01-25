import re
import datetime

from django.conf import settings
from django.core import mail
from django_webtest import WebTest
from django.test.client import Client
from django.test import TestCase

from django.contrib.auth.models import User

from core import models
import mzalendo.scorecards.models

class PersonTest(WebTest):
    def test_naming(self):        
        # create a test person
        person = models.Person(
            legal_name="Alfred Smith"
        )
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name, "Alfred Smith" )
        self.assertEqual( person.additional_names(), [] )
        
        # Add an alternative name
        person.other_names = "Freddy Smith"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name, "Freddy Smith" )
        self.assertEqual( person.additional_names(), [] )

        # Add yet another alternative name
        person.other_names = "Fred Smith\nFreddy Smith"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name, "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )

        # Add yet another alternative name
        person.other_names = "\n\nFred Smith\n\nFreddy Smith\n\n\n"
        person.clean()   # would normally be called by 'save()'
        self.assertEqual( person.name, "Fred Smith" )
        self.assertEqual( person.additional_names(), ['Freddy Smith'] )
        
class PersonScorecardTest(TestCase):
    def setUp(self):    
        # create a test person
        self.alf = models.Person.objects.create(
            legal_name="Alfred Smith"
        )
        
        self.score_category_1 = mzalendo.scorecards.models.Category.objects.create(
            name='Test1',
            slug='test1',
            synopsis='Test1 Synopsis',
            description='Test1 Description',
            )

        self.score_category_2 = mzalendo.scorecards.models.Category.objects.create(
            name='Test2',
            slug='test2',
            synopsis='Test2 Synopsis',
            description='Test2 Description',
            )

        self.alf.scorecard_entries.create(
            category=self.score_category_1,
            date=datetime.date(2525, 1, 1),
            remark="Very good!",
            score=1,
            )

    def testScorecardOverall(self):
        # import pdb;pdb.set_trace()
        assert self.alf.scorecard_overall() == 1
        assert self.alf.scorecard_overall_as_word() == 'good'

        self.alf.scorecard_entries.create(
            category=self.score_category_2,
            date=datetime.date(2525, 1, 1),
            remark="Awful.",
            score=-1,
            )

        assert self.alf.scorecard_overall() == 0
        assert self.alf.scorecard_overall_as_word() == 'average'
