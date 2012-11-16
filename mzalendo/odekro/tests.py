import os
import datetime
import json
# import time
# import tempfile
# import subprocess

# from unittest import TestCase

import unittest

from management.hansard_parser import parse, parse_time, normalise_line_breaks
from utils import split_name, legal_name


class ImporterTest(unittest.TestCase):
    NAMES =  (
        ('Abayateye, Alfred W. G.', 
            ('Abayateye', 'Alfred', 'W. G.', ''),
            'Alfred W. G. Abayateye'),
        ('Abongo, Albert', ('Abongo', 'Albert', '', ''),
            'Albert Abongo'),
        ('Abdul-Karim, Iddrisu (Alhaji)', 
            ('Abdul-Karim', 'Iddrisu', '', 'Alhaji'),
            'Iddrisu Abdul-Karim'),
        ('Abdul-Rahman, Masoud Baba', 
            ('Abdul-Rahman', 'Masoud', 'Baba', ''),
            'Masoud Baba Abdul-Rahman'),
        ('Abubakari, Ibrahim Dey (Alhaji)', 
            ('Abubakari', 'Ibrahim', 'Dey', 'Alhaji'),
            'Ibrahim Dey Abubakari'),
        ('Ameyaw-Akumfi, Christopher (Prof)', 
            ('Ameyaw-Akumfi', 'Christopher', '', 'Prof'),
            'Christopher Ameyaw-Akumfi'),
        ('Alhassan, Ahmed Yakubu (Dr)', 
            ('Alhassan', 'Ahmed', 'Yakubu', 'Dr'),
            'Ahmed Yakubu Alhassan'),
        ('Ahmed, Mustapha (Maj [rtd]) (Dr) (Alh)', 
            ('Ahmed', 'Mustapha', '', 'Maj (rtd) Dr Alh'),
            'Mustapha Ahmed')
    )

    def test_split_name(self):
        for name, split, legal in self.NAMES:
            self.assertEqual(split, split_name(name))
            last_name, first_name, middle_name, title = split
            self.assertEqual(legal, 
                    legal_name(last_name, first_name, middle_name))


class GhanaParserTest(unittest.TestCase):
    basedir = os.path.abspath(os.path.dirname( __file__ ))
    sample = os.path.join(basedir, 'data', 'hansard-sample.txt')
    
    entries = None
    head = None


    @classmethod
    def setUpClass(cls):
        cls.head, cls.entries = parse(open(cls.sample, 'r').read())

    @classmethod
    def tearDownClass(cls):
        pass

    def test_parse_time_string(self):
        
        data = {
            '1.00 p.m.':  datetime.time(13),
            '1.00 a.m.':  datetime.time(1),
            '12.00 p.m.': datetime.time(12), # am and pm make no sense at noon or midnight - but define what we want to happen
            '12.30 p.m.': datetime.time(12, 30)
        }
        
        for s, t in data.items():
            self.assertEqual(parse_time(s), t)

        self.assertIsNone(parse_time('foo.bar'))
        

    def test_header(self):
        self.assertEqual(4, self.head['series'])
        self.assertEqual(76, self.head['volume'])
        self.assertEqual(13, self.head['number'])
        self.assertEqual(datetime.date(2012, 2, 14), self.head['date'])
        self.assertEqual(datetime.time(10, 40), self.head['time'])

    def test_entries(self):
        t = datetime.time(10, 40)

        x = self.entries[0]
        self.assertEqual(x['chair'], 'MADAM SPEAKER')
        self.assertEqual(t, x['time'])

        x = self.entries[1]
        self.assertEqual('PRAYERS', x['heading'])
        self.assertEqual(t, x['time'])

        topic = 'Votes and Proceedings and the Official Report'
        

        
    @unittest.skipIf( True, "Skipped for now, should be fixed instead")
    def test_need_to_be_completed(self):

        # This is brittle and keeps changing as the parser is worked on. Skip
        # it until parser is stable.
        speeches = [x for x in self.entries if x['kind'] is 'speech']
        self.assertEqual(124, len(speeches))

        # There does not appear to be any code in the parser that relates to this test.
        x = self.entries[0]

        self.assertEqual(topic, x['topic'])
        self.assertEqual('Madam Speaker', x['name'])


        x = self.entries[-1]
        self.assertEqual('ADJOURNMENT', x['original'])
        self.assertEqual(datetime.time(13, 20), x['time'])
        self.assertEqual(datetime.datetime(2012, 2, 15, 10), x['next'])

    def test_page_order(self):
        pass
    

class GhanaParserRegressionTest(unittest.TestCase):

    def convert_parsed_data_to_json(self, parsed):
        # Can't jsonify dates and times - use the default to covert to iso format
        def dthandler(obj):
            if isinstance(obj, datetime.time) or isinstance(obj, datetime.date):
                return obj.isoformat()
            return None

        return json.dumps(parsed, sort_keys=True, indent=4, default=dthandler)

    def test_entire_output(self):
        """
        For the sample files that we have parse them and then compare the
        results to those stored in JSON, and to the normalised line breaks. This
        will allow us to quickly spot changes that are not individually tested.

        Note that there is a flag that can be used to write the new output to
        disk. This can be used to update the test data and, and also to make it
        possible to use a diff tool to see the changes more clearly than is
        possible in the failing test output.
        """
        
        # change to True to update the test json files.
        overwrite_known_good_files = False
        
        # list of all the files that we should parse and compare (path should
        # be relative to this test file).
        transcript_files = [
            'data/hansard-sample.txt',
            'data/hansards/hansard_0025.txt',
            'data/hansards/hansard_0026.txt',
            'data/hansards/hansard_0028.txt',
            'data/hansards/hansard_0029.txt',
            'data/hansards/hansard_0030.txt',
            'data/hansards/hansard_0031.txt',
            'data/hansards/hansard_0032.txt',
            'data/hansards/hansard_0034.txt',
            'data/hansards/hansard_0038.txt',
            'data/hansards/hansard_0051.txt',
            'data/hansards/hansard_0075.txt',
            'data/hansards/hansard_0077.txt',
            'data/hansards/hansard_0078.txt',
        ] 
        
        for transcript_file in transcript_files:
            transcript_abs_path = os.path.join(os.path.dirname(__file__), transcript_file)
            normalised_abs_path = os.path.splitext(transcript_abs_path)[0] + '-normalised.txt'
            data_abs_path       = os.path.splitext(transcript_abs_path)[0] + '.json'

            # Read the sample content
            sample_content = open(transcript_abs_path, 'r').read()

            # normalise the line breaks
            normalised_sample_content = normalise_line_breaks( sample_content )

            # parse sample content, store in data structure
            head, entries = parse(sample_content)
            parsed_data = { 'head': head, 'entries': entries }
            parsed_data_as_json = self.convert_parsed_data_to_json( parsed_data )
            
            # Write this parsed data out to disk if desired - this should
            # normally not happen, but is convenient to do during development
            if overwrite_known_good_files:
                print "** WARNING - overwriting known good files for '%s' ***" % transcript_abs_path
                open(data_abs_path,       'w').write( parsed_data_as_json )
                open(normalised_abs_path, 'w').write( normalised_sample_content )
            
            # check that the line splitting works as expected
            self.assertEqual(
                open(normalised_abs_path, 'r').read(),
                normalised_sample_content
            )

            # Read in the expected data and compare to what we got from parsing
            expected_data = json.loads( open( data_abs_path, 'r').read() )
            self.assertEqual(
                json.loads( parsed_data_as_json ), # so datetimes are iso formatted
                expected_data
                # "Correctly parsed %s" % transcript_file
            )
            



if __name__ == "__main__":
    unittest.main()