from datetime import date

from django.test import TestCase
from pombola.core.models import Person, Place, PlaceKind, Position, PositionTitle
from pombola.hansard.models import Source, Sitting, Venue, Entry
from pombola.hansard.models.entry import NAME_SUBSTRING_MATCH


class HansardEntryTest(TestCase):

    def setUp(self):
        self.source = Source.objects.create(
            date = date(2011, 11, 15),
            name = 'test source'
        )
        na = Venue.objects.create(
            name='National Assembly',
            slug='national-assembly'
        )
        senate = Venue.objects.create(
            name='Senate',
            slug='senate'
        )

        self.na_sitting = Sitting(
            source     = self.source,
            venue      = na,
            start_date = date(2011, 11, 15),
        )

        self.senate_sitting = Sitting(
            source     = self.source,
            venue      = senate,
            start_date = date(2011, 11, 15),
        )

        na_member_title = PositionTitle.objects.create(
            name='Member of the National Assembly',
            slug='member-national-assembly',
        )

        senate_member_title = PositionTitle.objects.create(
            name='Senator',
            slug='senator'
        )

        place_kind_test = PlaceKind.objects.create(
            name='Test',
        )

        test_place = Place.objects.create(
            name="Some Place",
            slug='some_place',
            kind=place_kind_test,
        )

        self.senator = Person.objects.create(
            legal_name='Tom Jones',
            slug='tom-jones'
        )
        self.mp = Person.objects.create(
            legal_name='Paul Jones',
            slug='paul-jones'
        )

        senate_position = Position.objects.create(
                              person=self.senator,
                              place=test_place,
                              category='political',
                              title=senate_member_title,
        )

        na_position = Position.objects.create(
                          person=self.mp,
                          place=test_place,
                          category='political',
                          title=na_member_title,
        )

    def test_multiple_politician_name_matches_na(self):
        entry = Entry(
            sitting       = self.na_sitting,
            type          = 'text',
            page_number   = 12,
            text_counter  = 4,
            speaker_name  = 'Jones',
            speaker_title = 'Hon.',
            content       = 'test',
        )
        possible_speakers = entry.possible_matching_speakers(
            name_matching_algorithm=NAME_SUBSTRING_MATCH)

        self.assertEqual(1, len(possible_speakers))
        self.assertEqual(
            self.mp,
            possible_speakers[0]
        )

    def test_multiple_politician_name_matches_senate(self):
        entry = Entry(
            sitting       = self.senate_sitting,
            type          = 'text',
            page_number   = 12,
            text_counter  = 4,
            speaker_name  = 'Jones',
            speaker_title = 'Hon.',
            content       = 'test',
        )
        possible_speakers = entry.possible_matching_speakers(
            name_matching_algorithm=NAME_SUBSTRING_MATCH)

        self.assertEqual(1, len(possible_speakers))
        self.assertEqual(
            self.senator,
            possible_speakers[0]
        )

    def test_multiple_politician_name_matches_joint_sitting(self):
        self.source.name = "Joint Sitting of the Parliament"
        self.source.save()

        entry = Entry(
            sitting       = self.na_sitting,
            type          = 'text',
            page_number   = 12,
            text_counter  = 4,
            speaker_name  = 'Jones',
            speaker_title = 'Hon.',
            content       = 'test',
        )
        possible_speakers = entry.possible_matching_speakers(
            name_matching_algorithm=NAME_SUBSTRING_MATCH)
        self.assertEqual(2, len(possible_speakers))

    def test_exclude_hidden_profiles(self):
        self.senator.hidden = True
        self.senator.save()

        entry = Entry(
            sitting       = self.senate_sitting,
            type          = 'text',
            page_number   = 12,
            text_counter  = 4,
            speaker_name  = 'Jones',
            speaker_title = 'Hon.',
            content       = 'test',
        )
        possible_speakers = entry.possible_matching_speakers(
            name_matching_algorithm=NAME_SUBSTRING_MATCH)

        self.assertEqual(1, len(possible_speakers))
        self.assertEqual(
            self.mp,
            possible_speakers[0]
        )

    def test_exclude_hidden_profiles(self):
        self.senator.hidden = True
        self.senator.save()

        entry = Entry(
            sitting       = self.senate_sitting,
            type          = 'text',
            page_number   = 12,
            text_counter  = 4,
            speaker_name  = 'Jones',
            speaker_title = 'Hon.',
            content       = 'test',
        )

        self.assertEqual(
            self.mp,
            entry.possible_matching_speakers()[0]
        )
