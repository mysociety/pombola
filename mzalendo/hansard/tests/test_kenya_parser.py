import datetime
import os
import time
import json
import tempfile
import subprocess

from django.test import TestCase
from django.utils import unittest

from hansard.kenya_parser import KenyaParser, KenyaParserCouldNotParseTimeString
from hansard.models import Source, Sitting, Entry, Venue, Alias

from core.models import Person, PositionTitle, Position

from django_date_extensions.fields import ApproximateDate


class KenyaParserTest(TestCase):

    local_dir          = os.path.abspath( os.path.dirname( __file__ ) )
    sample_pdf         = os.path.join( local_dir, '2011-09-01-sample.pdf'  )
    sample_html        = os.path.join( local_dir, '2011-09-01-sample.html' )
    expected_data_json = os.path.join( local_dir, '2011-09-01-sample.json' )

    def setUp(self):
        # create the venue
        Venue(
            slug = 'national_assembly',
            name = 'National Assembly',
        ).save()
    
    
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
                
        # Whilst developing the code this proved useful (on a mac at least)
        # tmp = tempfile.NamedTemporaryFile( delete=False, suffix=".json" )
        # tmp = open( '/tmp/mzalend_hansard_parse.json', 'w')
        # tmp.write( json.dumps( data, sort_keys=True, indent=4 ) )
        # tmp.close()        
        # subprocess.call(['open', tmp.name ])
                
        expected = json.loads( open( self.expected_data_json, 'r'  ).read() )
        
        self.assertEqual( data['transcript'], expected['transcript'] )

        # FIXME
        self.assertEqual( data['meta'], expected['meta'] )
        

    def test_parse_time_string(self):
        
        time_tests = {
            '1.00 p.m.':  '13:00:00',
            '1.00 a.m.':  '01:00:00',
            '12.00 p.m.': '12:00:00', # am and pm make no sense at noon or midnight - but define what we want to happen
            '12.30 p.m.': '12:30:00',
        }
        
        for string, output in time_tests.items():
            self.assertEqual( KenyaParser.parse_time_string( string ), output )

        self.assertRaises(
            KenyaParserCouldNotParseTimeString,
            KenyaParser.parse_time_string,
            'foo.bar'
        )


    def _create_source_and_load_test_json_to_entries(self):
        source   = Source.objects.create(
            name = 'Test source',
            url  = 'http://example.com/foo/bar/testing',
            date = datetime.date( 2011, 9, 1 )
        )
        data = json.loads( open( self.expected_data_json, 'r'  ).read() )
        KenyaParser.create_entries_from_data_and_source( data, source )
        return source

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

        # This should really be in a seperate file as it is not related to the
        # Kenya parser, but keeping it here for now as it is a step in the
        # parsing flow that is being tested.
        
        # set up the entries
        source = self._create_source_and_load_test_json_to_entries()

        entry_qs = Entry.objects.all()

        # check that none of the speakers are assigned
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )
        
        # Assign speakers
        Entry.assign_speakers()
        
        # check that none of the speakers got assigned - there are no entries in the database
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 11 )


        # print entry_qs.unassigned_speaker_names()


        # Add an mp that should match but don't make an mp - no match
        james_gabbow = Person.objects.create(
            legal_name = 'James Gabbow',
            slug       = 'james-gabbow',
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 31 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 11 )


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
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 26 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 10 )

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
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 26 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 10 )
        
        # Add a name to the aliases and check it is matched
        betty_laboso = Person.objects.create(
            legal_name = 'Betty Laboso',
            slug       = 'betty-laboso',
        )
        Alias.objects.create(
            alias  = 'Dr. Laboso',
            person = betty_laboso,
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 24 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 9 )
        
        # Add a name to alias that should be ignored, check not matched but not listed in names any more
        Alias.objects.create(
            alias   = 'Prof. Kaloki',
            ignored = True,
        )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 24 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 8 )        
        
        # Add all remaining names to alias and check that all matched
        for name in entry_qs.unassigned_speaker_names():
            Alias.objects.create(
                alias  = name,
                person = betty_laboso,
            )
        Entry.assign_speakers()
        self.assertEqual( entry_qs.unassigned_speeches().count(), 8 )
        self.assertEqual( len(entry_qs.unassigned_speaker_names()), 0 )
        
    
    def test_can_ignore_some_speakers(self):

        # These are all names that appear because the parser sometimes gets confused.
        # Rather than fix the parser (very hard) make sure that we ignore these names so
        # that missing name report is not so long.
        speaker_names = [
            "10 Thursday 10th February, 2011(P) Mr. Kombo",
            "(a)",
            "Act to 58A.",
            "ADJOURNMENT 29 Wednesday, 1st December, 2010 (A) Mr. Deputy Speaker",
            "April 21, 2009 PARLIAMENTARY DEBATES 2 Mr. Speaker",
            "(b)",
            "Cap.114 26.",
            "COMMUNICATION FROM THE CHAIR Mr. Speaker",
            "Deputy Speaker",
            "(i) Energy, Communications and Information Committee",
            "NOTICES OF MOTIONS Mr. Affey",
            "QUORUM Mr. Ahenda",
            "Tellers of Ayes",
            "The Assistant for Lands",
            "The Assistant Minister for Agriculture",
            "The Attorney-General",
            "The Member for Fafi",
            "The Minister for Roads",
        ]
        
        false_count = 0
        
        for name in speaker_names:
            result = Entry.can_ignore_name( name ) 
            if not result:
                print "Got True for Entry.can_ignore_name( '%s' ), expecting False" % name
                false_count += 1
    
        self.assertEqual( false_count, 0 )