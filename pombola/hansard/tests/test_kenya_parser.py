import datetime
import os
import re
import time
import json
import tempfile
import subprocess

from django.test import TestCase
from django.utils import unittest

from nose.plugins.attrib import attr

from pombola.hansard.kenya_parser import KenyaParser, KenyaParserCouldNotParseTimeString
from pombola.hansard.models import Source, Sitting, Entry, Venue, Alias

from pombola.core.models import Person, PositionTitle, Position

from django_date_extensions.fields import ApproximateDate
from django.conf import settings

@attr(country='kenya')
class KenyaParserVenueSpecificTestBase(object):

    def setUp(self):
        # create the venue
        Venue.objects.create(slug='national_assembly', name='National Assembly')

    def _create_source_and_load_test_json_to_entries(self):
        source   = Source.objects.create(
            name = 'Test source',
            url  = 'http://example.com/foo/bar/testing',
            date = datetime.date( 2011, 9, 1 )
        )
        data = json.loads( open( self.expected_data_json, 'r'  ).read() )
        KenyaParser.create_entries_from_data_and_source( data, source )
        return source

    def test_converting_pdf_to_html(self):
        """Test that the pdf becomes the html that we expect"""
        pdf_file = open( self.sample_pdf, 'r' )
        html = KenyaParser.convert_pdf_to_html( pdf_file )

        expected_html = open( self.sample_html, 'r' ).read()

        self.assertEqual( html, expected_html )

    def test_converting_html_to_data(self):
        """test the convert_pdf_to_data function"""

        html_file = open( self.sample_html, 'r')
        html = html_file.read()

        data = KenyaParser.convert_html_to_data( html=html )

        # Whilst developing the code this proved useful
        # out = open( self.expected_data_json, 'w')
        # json_string = json.dumps( data, sort_keys=True, indent=4 )
        # json_string = re.sub(r" +\n", "\n", json_string) # trim trailing whitespace
        # json_string += "\n"
        # out.write( json_string )
        # out.close()

        expected = json.loads( open( self.expected_data_json, 'r'  ).read() )

        self.assertEqual( data['transcript'], expected['transcript'] )

        # FIXME
        self.assertEqual( data['meta'], expected['meta'] )


@attr(country='kenya')
@unittest.skipUnless(settings.KENYA_PARSER_PDF_TO_HTML_HOST, "setting 'KENYA_PARSER_PDF_TO_HTML_HOST' not set")
class KenyaParserSenateTest(KenyaParserVenueSpecificTestBase, TestCase):

    local_dir          = os.path.abspath( os.path.dirname( __file__ ) )
    sample_pdf         = os.path.join( local_dir, '2013-07-31-senate-sample.pdf'  )
    sample_html        = os.path.join( local_dir, '2013-07-31-senate-sample.html' )
    expected_data_json = os.path.join( local_dir, '2013-07-31-senate-sample.json' )

@attr(country='kenya')
@unittest.skipUnless(settings.KENYA_PARSER_PDF_TO_HTML_HOST, "setting 'KENYA_PARSER_PDF_TO_HTML_HOST' not set")
class KenyaParserAssemblyTest(KenyaParserVenueSpecificTestBase, TestCase):

    local_dir          = os.path.abspath( os.path.dirname( __file__ ) )
    sample_pdf         = os.path.join( local_dir, '2011-09-01-assembly-sample.pdf'  )
    sample_html        = os.path.join( local_dir, '2011-09-01-assembly-sample.html' )
    expected_data_json = os.path.join( local_dir, '2011-09-01-assembly-sample.json' )

    def test_create_entries_from_data_and_source(self):
        """Take the data and source, and create the sitting and entries from it"""

        source = self._create_source_and_load_test_json_to_entries()

        # check source now marked as processed
        source = Source.objects.get(id=source.id) # reload from db
        self.assertEqual( source.last_processing_success.date(), datetime.date.today() )

        # check sitting created
        sitting_qs = Sitting.objects.filter(source=source)
        self.assertEqual( sitting_qs.count(), 1 )
        sitting = sitting_qs[0]

        # check start and end date and times correct
        self.assertEqual( sitting.start_date, datetime.date( 2011, 9, 1 ) )
        self.assertEqual( sitting.start_time, datetime.time( 14, 30, 00 ) )
        self.assertEqual( sitting.end_date,   datetime.date( 2011, 9, 1 ) )
        self.assertEqual( sitting.end_time,   datetime.time( 18, 30, 00 ) )

        # check correct venue set
        self.assertEqual( sitting.venue.slug, 'national_assembly' )

        # check entries created and that we have the right number
        entries = sitting.entry_set
        self.assertEqual( entries.count(), 64 )

    def test_assign_speaker_names(self):
        """Test that the speaker names are assigned as expected"""

        # This should really be in a separate file as it is not related to the
        # Kenya parser, but keeping it here for now as it is a step in the
        # parsing flow that is being tested.

        # set up the entries
        source = self._create_source_and_load_test_json_to_entries()

        entry_qs = Entry.objects.all()
        unassigned_aliases_qs = Alias.objects.all().unassigned()

        # check that none of the speakers are assigned
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )

        # Assign speakers
        Entry.assign_speakers()

        # check that none of the speakers got assigned - there are no entries in the database
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )
        self.assertEqual( unassigned_aliases_qs.count(), 11 )


        # print entry_qs.unassigned_speaker_names()


        # Add an mp that should match but don't make an mp - no match
        james_gabbow = Person.objects.create(
            legal_name = 'James Gabbow',
            slug       = 'james-gabbow',
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )
        self.assertEqual( unassigned_aliases_qs.count(), 11 )

        # create the position - check matched
        mp = PositionTitle.objects.create(
            name = 'Member of Parliament',
            slug = 'mp',
        )
        Position.objects.create(
            person     = james_gabbow,
            title      = mp,
            start_date = ApproximateDate( year=2011, month=1, day = 1 ),
            end_date   = ApproximateDate( future=True ),
            category = 'political',
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 26 )
        self.assertEqual( unassigned_aliases_qs.count(), 10 )

        # Add a nominated MP and check it is matched

        nominated_politician = PositionTitle.objects.create(
            name='Nominated MP',
            slug='nominated-member-parliament',
            )

        calist_mwatela = Person.objects.create(
            legal_name='Calist Mwatela',
            slug='calist-mwatela',
            )

        Position.objects.create(
            person = calist_mwatela,
            title = nominated_politician,
            start_date = ApproximateDate( year=2011, month=1, day = 1 ),
            end_date   = ApproximateDate( future=True ),
            category = 'political',
            )

        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 24 )
        self.assertEqual( unassigned_aliases_qs.count(), 9 )

        # Add an mp that is no longer current, check not matched
        bob_musila = Person.objects.create(
            legal_name = 'Bob Musila',
            slug       = 'bob-musila',
        )
        Position.objects.create(
            person     = james_gabbow,
            title      = mp,
            start_date = ApproximateDate( year=2007, month=1, day = 1 ),
            end_date   = ApproximateDate( year=2009, month=1, day = 1 ),
            category = 'political',
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 24 )
        self.assertEqual( unassigned_aliases_qs.count(), 9 )

        # Add a name to the aliases and check it is matched
        betty_laboso = Person.objects.create(
            legal_name = 'Betty Laboso',
            slug       = 'betty-laboso',
        )
        betty_laboso_alias = Alias.objects.get(alias  = 'Dr. Laboso')
        betty_laboso_alias.person = betty_laboso
        betty_laboso_alias.save()

        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 22 )
        self.assertEqual( unassigned_aliases_qs.count(), 8 )

        # Add a name to alias that should be ignored, check not matched but not listed in names any more
        prof_kaloki_alias = Alias.objects.get( alias = 'Prof. Kaloki')
        prof_kaloki_alias.ignored = True
        prof_kaloki_alias.save()

        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 22 )
        self.assertEqual( unassigned_aliases_qs.count(), 7 )

        # Add all remaining names to alias and check that all matched
        for alias in unassigned_aliases_qs.all():
            alias.person = betty_laboso
            alias.save()

        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 8 )
        self.assertEqual( unassigned_aliases_qs.count(), 0 )



class KenyaParserTest(TestCase):

    def test_parse_time_string(self):

        time_tests = {
            '1.00 p.m.':  '13:00:00',
            '1.00 a.m.':  '01:00:00',
            '12.00 p.m.': '12:00:00', # am and pm make no sense at noon or midnight - but define what we want to happen
            '12.30 p.m.': '12:30:00',
            "twenty-four minutes past Six o'clock" : '18:24:00',
            "Fifteen minutes to two o'clock" : '13:45:00',
            "Fifty five minutes past Nine o'clock" : '09:55:00',
            "One minute past eight o'clock": '08:01:00'
        }

        for string, output in time_tests.items():
            self.assertEqual( KenyaParser.parse_time_string( string ), output )

        self.assertRaises(
            KenyaParserCouldNotParseTimeString,
            KenyaParser.parse_time_string,
            'foo.bar'
        )


