# import os
# import datetime
# 
# from datetime import date, time
# 
from django.test import TestCase
from hansard.models import Alias

class HansardAliasTest(TestCase):

    def test_alias_cleanup(self):
        """Check that the name is cleaned up as we'd expect"""

        tests = [
            # ('from', 'to'),
            ('   Mr. Foo  ', 'Mr. Foo' ),
            ('Mr. Foo,',     'Mr. Foo' ),
            ('Mr.Foo,',      'Mr. Foo' ),
            ('Mr.   Foo,',   'Mr. Foo' ),
            ('(Mr. Foo)',    'Mr. Foo' ),
            ('[Mr. Foo]',    'Mr. Foo' ),

            ( 'Mr A.N. Other', 'Mr. A. N. Other' ),

        ]

        for dirty, clean in tests:
            self.assertEqual( Alias.clean_up_name(dirty), clean )

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
            "(ii) Local Authorities Committee",
            "(iii) Transport, Public Works and Housing Committee",
            "(iv) Committee on Implementation",
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
            result = Alias.can_ignore_name( name ) 
            if not result:
                print "Got True for Alias.can_ignore_name( '%s' ), expecting False" % name
                false_count += 1

        self.assertEqual( false_count, 0 )