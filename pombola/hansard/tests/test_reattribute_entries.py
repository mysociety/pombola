# Tests for the Django management command hansard_reattribute_speeches

import contextlib
from datetime import date
from mock import patch
import sys

from pombola.core.models import Person
from pombola.hansard.models import (
    Entry, Source, Sitting, Venue
)

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import unittest

from pombola.core.tests.test_commands import no_stderr


class ReattributeEntriesCommandTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name = 'test'
        )
        self.source = Source.objects.create(
            date = date(2015, 8, 24)
        )
        self.sitting_1 = Sitting.objects.create(
            start_date = date( 2011, 11, 15 ),
            source = self.source,
            venue = self.venue,
        )
        self.sitting_2 = Sitting.objects.create(
            start_date = date( 2012, 11, 15 ),
            source = self.source,
            venue = self.venue,
        )
        self.sitting_3 = Sitting.objects.create(
            start_date = date( 2013, 11, 15 ),
            source = self.source,
            venue = self.venue,
        )

        self.person_a = Person.objects.create(
            name="Daffy Duck",
            slug="daffy-duck")
        self.person_b = Person.objects.create(
            name="Bugs Bunny",
            slug="bugs-bunny")

        self.entry_1 = Entry.objects.create(
            speaker = self.person_a,
            sitting = self.sitting_1,
            page_number = 42,
            text_counter = 12
        )
        self.entry_2 = Entry.objects.create(
            speaker = self.person_a,
            sitting = self.sitting_2,
            page_number = 42,
            text_counter = 12
        )
        self.entry_3 = Entry.objects.create(
            speaker = self.person_a,
            sitting = self.sitting_3,
            page_number = 42,
            text_counter = 12
        )

        self.options = {
            'person_to': self.person_b.id,
            'person_from': self.person_a.id,
            'quiet': True,
            'interactive': False
        }

    @patch('__builtin__.raw_input', return_value='y')
    def test_reassign_all(self, mock_input):
        call_command('hansard_reattribute_entries', **self.options)

        # Check that person_a has no entries and person_b has 3:
        self.assertEqual(0, Entry.objects.filter(speaker=self.person_a).count())
        self.assertEqual(3, Entry.objects.filter(speaker=self.person_b).count())

    @patch('__builtin__.raw_input', return_value='y')
    def test_reassign_all_with_slugs(self, mock_input):
        options = {
            'person_to': self.person_b.slug,
            'person_from': self.person_a.slug,
            'quiet': True
        }
        call_command('hansard_reattribute_entries', **options)

        # Check that person_a has no entries and person_b has 3:
        self.assertEqual(0, Entry.objects.filter(speaker=self.person_a).count())
        self.assertEqual(3, Entry.objects.filter(speaker=self.person_b).count())

    @patch('__builtin__.raw_input', return_value='y')
    def test_reassign_with_from_date(self, mock_input):
        options = self.options.copy()
        options['date_from'] = '2012-01-01'

        call_command('hansard_reattribute_entries', **options)

        # Check that person_a has 1 entry and person_b has 2:
        self.assertEqual(1, Entry.objects.filter(speaker=self.person_a).count())
        self.assertEqual(2, Entry.objects.filter(speaker=self.person_b).count())

    @patch('__builtin__.raw_input', return_value='y')
    def test_reassign_with_to_date(self, mock_input):
        options = self.options.copy()

        options['date_to'] = '2013-01-01'

        call_command('hansard_reattribute_entries', **options)

        # Check that person_a has 2 entries and person_b has 1:
        self.assertEqual(1, Entry.objects.filter(speaker=self.person_a).count())
        self.assertEqual(2, Entry.objects.filter(speaker=self.person_b).count())

    @patch('__builtin__.raw_input', return_value='y')
    def test_reassign_with_to_and_from_dates(self, mock_input):
        options = self.options.copy()
        options['date_from'] = '2012-01-01'
        options['date_to'] = '2013-01-01'

        call_command('hansard_reattribute_entries', **options)

        # Check that person_a has 1 entry and person_b has 2:
        self.assertEqual(2, Entry.objects.filter(speaker=self.person_a).count())
        self.assertEqual(1, Entry.objects.filter(speaker=self.person_b).count())
