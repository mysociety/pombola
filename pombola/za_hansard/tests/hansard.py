from __future__ import with_statement

from datetime import datetime, date
import pytz

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from instances.models import Instance

from za_hansard.models import Source

from za_hansard.parse import ZAHansardParser
from lxml import etree

import os

class ZAHansardParsingTests(TestCase):

    docnames = ['502914_1', 'NA290307', 'EPC110512', 'NA210212', 'NA200912']
    xml = {}

    @classmethod
    def setUpClass(cls):
        if 'popolo_name_resolver' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured("popolo_name_resolver is not in INSTALLED_APPS")

        tests_dir = os.path.dirname(os.path.abspath(__file__))
        cls._in_fixtures = os.path.join(tests_dir, 'test_inputs','hansard')
        super(ZAHansardParsingTests, cls).setUpClass()

        def process(docname):
            filename = os.path.join( cls._in_fixtures, '%s.%s' % (docname, 'doc') )
            obj = ZAHansardParser.parse(filename)
            xml = obj.akomaNtoso
            xml_string = etree.tostring(xml, pretty_print=True)
            today = datetime.now().strftime('%Y-%m-%d')
            xml_string = xml_string.replace('"%s"' % today, '"3000-01-01"')
            return (docname, (xml, xml_string))

        cls.xml = dict([process(dn) for dn in cls.docnames])

    def test_basic_parse(self):
        for docname in iter(self.xml):
            (xml, xml_string) = self.xml.get(docname)

            xml_path = os.path.join( self._in_fixtures, '%s.%s' % (docname, 'xml') )
            xml_expected = open( xml_path ).read()

            if xml_string != xml_expected:
                outname = './%s.%s' % (docname, 'xml')
                open( outname, 'w').write(xml_string)
                self.assertTrue( xml_string == xml_expected, "XML not correct.  Please diff %s %s (and update latter if required!)" % (outname, xml_path) )

    def test_xsd(self):
        xsd_path = os.path.join( self._in_fixtures, 'release-23.xsd')
        xsd_parser = etree.XMLParser(dtd_validation=False)

        xsd = etree.XMLSchema(
                etree.parse(xsd_path, xsd_parser))

        for docname in iter(self.xml):
            (xml, xml_string) = self.xml.get(docname)

            parser = etree.XMLParser(schema = xsd)
            try:
                xml = etree.fromstring(xml_string, parser)
                self.assertEqual(xml.tag, '{http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03}akomaNtoso', 'Validated ok')
            except etree.XMLSyntaxError as e:
                self.assertTrue(False, 'Document %s failed: %s' % (docname, str(e)) )

    def test_properties(self):
        (xml, _) = self.xml.get('502914_1')

        self.assertEqual(xml.tag, '{http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03}akomaNtoso')

        preface_p = xml.debate.preface.p
        self.assertEqual(preface_p.text, 'Thursday, ')
        docDate = preface_p.docDate
        self.assertEqual(docDate.text, '14 February 2013')
        self.assertEqual(docDate.get('date'), '2013-02-14')

        debateBody = xml.debate.debateBody
        mainSection = debateBody.debateSection
        self.assertEqual(mainSection.get('id'), 'db0')
        self.assertEqual(mainSection.get('name'), 'proceedings-at-joint-sitting')
        self.assertEqual(mainSection.heading.text, 'PROCEEDINGS AT JOINT SITTING')
        self.assertEqual(mainSection.p.text, 'Members of the National Assembly and the National Council of Provinces assembled in the Chamber of the National Assembly at ')
        recordedTime = mainSection.p.recordedTime
        self.assertEqual(recordedTime.text, '19:01')
        self.assertEqual(recordedTime.get('time'), '19:01:00')
        self.assertEqual(mainSection.prayers.p.text, 'The Speaker took the Chair and requested members to observe a moment of silence for prayers or meditation.')

        subSections = mainSection.findall('{*}debateSection')
        #for s in subSections:
            # print >> sys.stderr, s.get('id')
        self.assertEqual(len(subSections), 3)

        dbs1 = subSections[0]
        self.assertEqual(dbs1.get('id'), 'dbs1')
        self.assertEqual(dbs1.heading.text, 'CALLING OF JOINT SITTING')
        speech = dbs1.speech
        self.assertEqual(speech.get('by'), '#the-speaker')
        self.assertEqual(speech['from'].text, 'The SPEAKER')
        self.assertEqual(speech.p.text, 'Hon members, the President has called this Joint Sitting of the National Assembly and the National Council of Provinces in terms of section 84(2)(d) of the Constitution of the Republic of South Africa, read with Joint Rule 7(1)(a), to enable him to deliver his state of the nation address to Parliament. I now invite the honourable the President to address the Joint Sitting. [Applause.]')

        dbs2 = subSections[1]
        self.assertEqual(dbs2.get('id'), 'dbs2')
        self.assertEqual(dbs2.heading.text, 'ADDRESS BY PRESIDENT OF THE REPUBLIC')
        speech = dbs2.speech
        self.assertEqual(speech.get('by'), '#the-president-of-the-republic')
        self.assertEqual(speech['from'].text, 'The PRESIDENT OF THE REPUBLIC')
        ps = speech.findall('{*}p')
        self.assertEqual(len(ps), 141)
        self.assertEqual(ps[1], '... anizukusho ukuthi hayi iyaziqhenya le nsizwa bo. Ikhuluma, ikhulume bese isula ngeduku. [... that you will not label me as somebody who is very proud, who speaks for a while and then wipes his face with a handkerchief.]')

        dbs3 = subSections[2]
        self.assertEqual(dbs3.get('id'), 'dbs3')
        speeches = dbs3.findall('{*}speech')
        self.assertEqual(len(speeches), 2)

        self.assertEqual(len(speeches[1].findall('{*}p')), 2)

        adjournment = dbs3.adjournment
        self.assertEqual(adjournment.p.text, 'The Joint Sitting rose at ')
        recordedTime = adjournment.p.recordedTime
        self.assertEqual(recordedTime.text, '20:28')
        self.assertEqual(recordedTime.get('time'), '20:28:00')

        # TEST that references have been gathered correctly
        tlcpersons = xml.debate.meta.references.findall('{*}TLCPerson')
        self.assertEqual( len(tlcpersons), 3 )
        speeches_by_speaker = filter(
                lambda s: s.get('by') == '#the-speaker',
                mainSection.findall('.//{*}speech'))
        self.assertEqual( len(speeches_by_speaker), 2 )
        for speech in speeches_by_speaker:
            self.assertEqual( speech['from'].text, 'The SPEAKER' )

    def test_second_parse(self):
        (xml, _) = self.xml.get('NA290307')
        self.assertTrue(xml is not None)
        debateBody = xml.debate.debateBody
        mainSection = debateBody.debateSection
        subSections = mainSection.findall('{*}debateSection')
        self.assertEqual(len(subSections), 16)

class ZAHansardSayitLoadingTests(TestCase):

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    test_hansard_cache_dir = os.path.join(tests_dir, 'test_inputs','hansard')

    def setUp(self):
        Instance.objects.get_or_create(label='default')

        # create a source to test with
        self.source = Source.objects.create(
            id                      = 10, # Needed to create the correct path in cache_file_path
            title                   = 'HANSARD',
            document_name           = 'NA080513',
            document_number         = '539685',
            date                    = date(2013, 5, 8),
            url                     = 'commonrepository/Processed/20130910/539685_1.doc',
            house                   = 'National Assembly',
            language                = 'English',
            last_processing_attempt = datetime(2013, 10, 15, 23, 0, 0, tzinfo=pytz.utc),
            last_processing_success = datetime(2013, 10, 15, 23, 0, 0, tzinfo=pytz.utc),
        )

    def test_source_section_parent_headings(self):
        self.assertEqual(
            self.source.section_parent_headings,
            [
                "Hansard",
                "2013",
                "May",
                "08"
            ]
        )

    @override_settings(HANSARD_CACHE=test_hansard_cache_dir)
    def test_za_hansard_load_into_sayit(self):
        source = self.source

        call_command('za_hansard_load_into_sayit')

        # Reload the source from db
        source = Source.objects.get(pk=source.id)

        # Test section created as expected
        sayit_section = source.sayit_section
        self.assertTrue(sayit_section)
        self.assertEqual(sayit_section.parent.heading, "08") # Hansards -> 2013 -> 05 -> *08* -> sayit_section

        # Test that speeches are tagged
        speech = sayit_section.descendant_speeches().all()[0]
        self.assertEqual(speech.tags.count(), 1)
        self.assertEqual(speech.tags.all()[0].name, 'hansard')
