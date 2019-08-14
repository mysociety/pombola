# -*- coding: utf-8 -*-

from mock import patch
import os
import re
import requests
import datetime
import json
import lxml.etree
from itertools import izip

from django.test import TestCase
from django.template.defaultfilters import slugify
from django.utils.unittest import skipUnless

from .. import question_scraper
from ..management.commands.za_hansard_q_and_a_scraper import Command as QAScraperCommand
from ..models import Question, QuestionPaper

def sample_file(filename):
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tests_dir, 'test_inputs', 'questions', filename)


class ZAAnswerTests(TestCase):

    def test_answer_parsing(self):
        input_doc_file       = sample_file('answer_1.doc')
        expected_output_file = sample_file('answer_1_expected.txt')

        text = question_scraper.extract_answer_text_from_word_document(input_doc_file)
        expected = open(expected_output_file).read().decode('UTF-8')

        # Handy for updating the expected data.
        # out = open(expected_output_file, 'w+')
        # out.write(text.encode('UTF-8'))
        # out.close()

        self.assertEqual(text, expected)



class ZAIteratorBaseMixin(object):

    def setUp(self):
        # These tests should use cached data so that they are not subject to changes
        # to the HTML on the server. This cached data is committed to the repo. If you
        # delete the cache files they'll be regenerated on the next run, allowing you to
        # diff any changes to the server.

        # To delete all the cache files uncomment this line
        # shutil.rmtree(self.cache_file(''))

        pass

    def cache_file(self, name):
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(tests_dir, 'test_inputs', self.cache_dir_name)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return os.path.join(cache_dir, name)

    # create a method to retrieve url contents from file
    def get_from_file_or_network(self, url):

        # Reduce the url into something more manageable as a filename
        filename = slugify( re.sub( r'\W+', '-', re.sub(r'^.*/','', url))) + ".html"
        full_path = self.cache_file(filename)

        # Check for the file on disk. If found return it, else fetch and cache it
        if os.path.exists(full_path):
            with open(full_path) as read_from:
                return read_from.read()
        else:
            print "Retrieving and caching " + url
            response = requests.get( url )
            with open(full_path, 'w') as write_to:
                write_to.write(response.text)
            return response.text

    def fetch_details(self, details, number):
        retrieved_details = []

        with patch.object(details, "url_get", new=self.get_from_file_or_network):
            # Get the first number_to_retrieve questions
            for detail in details:
                retrieved_details.append( detail )
                if len(retrieved_details) >= number: break

        return retrieved_details

    def test_question_detail_iterator(self):

        details = self.iterator_model(self.start_url)
        number_to_retrieve = 50

        retrieved_details = self.fetch_details(details, number_to_retrieve)

        self.assertEqual(len(retrieved_details), number_to_retrieve)

        # Test that selected results are as we expect. 'expected_details' is a list of
        # tuples where the first item is the index in the expected details and the
        # second is what is expected. This allows interesting or edge case results to be
        # tested, skipping the dull or repeated ones.
        for index, expected in self.expected_details:
            self.assertEqual(retrieved_details[index], expected)


    def test_question_detail_iterator_stops_at_end(self):

        # Note that these tests rely on the cached html being as expected. If you update
        # that then please change the settings for the penultimate page of results, and
        # the number of questions expected after scraping.

        details = self.iterator_model(self.penultimate_url)
        number_to_retrieve = self.penultimate_expected_number + 20

        retrieved_details = self.fetch_details(details, number_to_retrieve)

        self.assertEqual(len(retrieved_details), self.penultimate_expected_number)




class ZAQuestionIteratorTests(ZAIteratorBaseMixin, TestCase):

    cache_dir_name = 'questions_cache'
    iterator_model = question_scraper.QuestionDetailIterator

    start_url = "http://www.parliament.gov.za/live/content.php?Category_ID=236"
    expected_details = (
        (0, {
            'date': u'20 September 2013',
            'house': u'National Council of Provinces',
            'language': u'Afrikaans',
            'name': u'QC130920.i28A',
            'type': 'pdf',
            'url': 'http://www.parliament.gov.za/live/commonrepository/Processed/20130926/541835_1.pdf',
            'document_number': 541835,
        }),
    )

    penultimate_url = start_url + "&DocumentStart=830"
    penultimate_expected_number = 19


class ZAAnswerIteratorTests(ZAIteratorBaseMixin, TestCase):

    cache_dir_name = 'answers_cache'
    iterator_model = question_scraper.AnswerDetailIterator

    start_url = "http://www.parliament.gov.za/live/content.php?Category_ID=248"
    expected_details = (
        (0, {
            'date': datetime.date(2013, 10, 3),
            'date_published': datetime.date(2013, 10, 3),
            'year': 2013,
            'house': u'N',
            'language': u'English',
            'document_name': u'RNW2356-131003',
            'oral_number': None,
            'written_number': u'2356',
            'type': 'doc',
            'url': 'http://www.parliament.gov.za/live/commonrepository/Processed/20131007/543139_1.doc',
        }),
    )

    penultimate_url = start_url + "&DocumentStart=5310"
    penultimate_expected_number = 6


class ZAQuestionParsing(TestCase):
    test_data = (
        ('559662_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20140113/559662_1.pdf', 'National Council of Provinces', '13 December 2013'),
        ('517147_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20130529/517147_1.pdf', 'National Assembly', '19 April 2013'),
        ('548302_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20131107/548302_1.pdf', 'National Council of Provinces', '1 November 2013'),

        # Interesting because of the pdftohtml bad xml problem.
        ('529998_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20130812/529998_1.pdf', 'National Assembly', '8 August 2013'),
        ('458606_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20130507/458606_1.pdf', 'National Council of Provinces', '14 September 2012'),

        ('184530_1', 'http://www.parliament.gov.za/live/commonrepository/Processed/20130507/184530_1.pdf', 'National Assembly', '9 October 2009'),
        )

    # FIXME - Oral questions which are transferred could collect their oral question number.

    # The exact form of the XML returned depends on the version of pdftohtml
    # used. Use the version installed onto travis as the common ground (as of
    # this writing 0.18.4). Also run if we have this version locally.
    # FIXME - Note that the version currently on our servers is 0.12.4 (as of 2014-02-02)
    pdftohtml_version = os.popen('pdftohtml -v 2>&1 | head -n 1').read().strip()
    wanted_version = '0.18.4'
    @skipUnless(
        os.environ.get('TRAVIS') or wanted_version in pdftohtml_version,
        "Not on TRAVIS, or versions don't watch ('%s' != '%s')" % (wanted_version, pdftohtml_version)
    )
    def test_pdf_to_xml(self):
        for filename_root, source_url, house, date_published in self.test_data:
            pdfdata = open(sample_file(filename_root + ".pdf")).read()
            expected_xml = open(sample_file(filename_root + ".xml")).read()

            qp_parser = question_scraper.QuestionPaperParser(
                name='TEST NAME',
                date=date_published,
                house=house,
                language='TEST LANGUAGE',
                url=source_url,
                document_number=int(filename_root.split('_')[0]),
                )
            actual_xml = qp_parser.get_question_xml_from_pdf(pdfdata)

            self.assertEqual(actual_xml, expected_xml, "Failed on {0}".format(filename_root))

    def test_xml_to_json(self):
        # Would be nice to test the intermediate step of the data written to the database, but that is not as easy to access as the JSON. As a regression test this will work fine though.

        for filename_root, source_url, house, date_published in self.test_data:
            xmldata = open(sample_file(filename_root + ".xml")).read()

            qp_parser = question_scraper.QuestionPaperParser(
                name='TEST NAME',
                date=date_published,
                house=house,
                language='TEST LANGUAGE',
                url=source_url,
                document_number=int(filename_root.split('_')[0]),
                )
            # Load xml to the database
            qp_parser.create_questions_from_xml(xmldata, source_url)

            command = QAScraperCommand()

            # Turn questions in database into JSON. Order by id as that should
            # reflect the processing order.
            questions = []
            question_paper = QuestionPaper.objects.get(source_url=source_url)

            for question in question_paper.question_set.all():
                question_as_data = command.question_to_json_data(question)
                questions.append(question_as_data)

            expected_file = sample_file('expected_json_data_for_{0}.json'.format(filename_root))
            # Uncomment to write out to the expected JSON file.
            # with open(expected_file, 'w') as writeto:
            #     json_to_write = json.dumps(questions, indent=1, sort_keys=True)
            #     writeto.write(re.sub(r'(?m) +$', '', json_to_write) + "\n")

            expected_json = open(expected_file).read()
            expected_data = json.loads(expected_json)
            expected_data.sort()

            questions.sort()
            questions = json.loads(json.dumps(questions))

            self.maxDiff = None
            for a, b in izip(questions, expected_data):
                self.assertEqual(a, b, "mismatch in %s" % expected_file)

    def test_page_header_removal(self):
        tests = [

        # 559662_1
        (ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="80" left="85" width="522" height="16" font="0"><i>Friday, 13 December 2013</i>] 272 </text>
<text top="1197" left="83" width="447" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 37─2013 </text>
<text top="118" left="85" width="125" height="16" font="1">[No 37—2013] F</text>
</page>""",
         ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="118" left="85" width="125" height="16" font="1">[No 37—2013] F</text>
</page>"""),

        (ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="80" left="85" width="750" height="16" font="1"> 273 </text>
<text top="80" left="607" width="205" height="16" font="1">[<i>Friday, 13 December 2013 </i></text>
<text top="1197" left="364" width="447" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 37─2013 </text>
<text top="119" left="85" width="36" height="16" font="4"><b>152. </b></text>
</page>""",
         ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="119" left="85" width="36" height="16" font="4"><b>152. </b></text>
</page>"""),

        (ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="80" left="85" width="531" height="16" font="0"><i>Friday, 1 November 2013</i>] 248 </text>
<text top="1197" left="85" width="447" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 33─2013 </text>
<text top="118" left="85" width="125" height="16" font="1">[No 33—2013] F</text>
</page>""",
         ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="118" left="85" width="125" height="16" font="1">[No 33—2013] F</text>
</page>"""),

        (ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="80" left="85" width="750" height="16" font="1"> 249 </text>
<text top="80" left="616" width="197" height="16" font="1">[<i>Friday, 1 November 2013 </i></text>
<text top="1197" left="364" width="447" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 33─2013 </text>
<text top="119" left="85" width="36" height="16" font="4"><b>438. </b></text>
</page>""",
         ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="119" left="85" width="36" height="16" font="4"><b>438. </b></text>
</page>"""),

        (ur"""<page number="3" position="absolute" top="0" left="0" height="1263" width="892">
<text top="80" left="446" width="366" height="16" font="0">239 [<i>Friday, 19 April 2013 </i></text>
<text top="1197" left="441" width="369" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 12─2013 </text>
<text top="119" left="86" width="36" height="16" font="4"><b>676. </b></text>
</page>""",
         ur"""<page number="3" position="absolute" top="0" left="0" height="1263" width="892">
<text top="119" left="86" width="36" height="16" font="4"><b>676. </b></text>
</page>"""),

        (ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="108" left="145" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="131" width="128" height="12" font="0"><i>Friday, 9 October 2009 </i></text>
<text top="123" left="447" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="696" width="3" height="12" font="0"><i> </i></text>
<text top="139" left="131" width="4" height="16" font="1"> </text>
<text top="1147" left="378" width="361" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 20 - 2009 </text>
<text top="108" left="742" width="20" height="12" font="3">533</text>
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="131" width="253" height="12" font="3">[No 20 – 2009] First Session, Fourth Parliament</text>
</page>""",
         ur"""<page number="1" position="absolute" top="0" left="0" height="1263" width="892">
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="131" width="253" height="12" font="3">[No 20 – 2009] First Session, Fourth Parliament</text>
</page>"""),

        (ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="108" left="145" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="131" width="128" height="12" font="0"><i>Friday, 9 October 2009 </i></text>
<text top="123" left="447" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="696" width="3" height="12" font="0"><i> </i></text>
<text top="139" left="131" width="4" height="16" font="1"> </text>
<text top="1147" left="378" width="361" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 20 - 2009 </text>
<text top="108" left="742" width="20" height="12" font="3">534</text>
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="184" width="4" height="13" font="7"><b> </b></text>
<text top="199" left="350" width="250" height="13" font="7"><b>QUESTIONS FOR WRITTEN REPLY </b></text>
</page>""",
         ur"""<page number="2" position="absolute" top="0" left="0" height="1263" width="892">
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="184" width="4" height="13" font="7"><b> </b></text>
<text top="199" left="350" width="250" height="13" font="7"><b>QUESTIONS FOR WRITTEN REPLY </b></text>
</page>"""),

        (ur"""<page number="3" position="absolute" top="0" left="0" height="1263" width="892">
<text top="108" left="145" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="131" width="128" height="12" font="0"><i>Friday, 9 October 2009 </i></text>
<text top="123" left="447" width="3" height="12" font="0"><i> </i></text>
<text top="123" left="696" width="3" height="12" font="0"><i> </i></text>
<text top="139" left="131" width="4" height="16" font="1"> </text>
<text top="1147" left="378" width="361" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 20 - 2009 </text>
<text top="108" left="742" width="20" height="12" font="3">535</text>
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="184" width="21" height="13" font="4">(4) </text>
</page>""",
         ur"""<page number="3" position="absolute" top="0" left="0" height="1263" width="892">
<text top="122" left="729" width="4" height="13" font="4"> </text>
<text top="1149" left="131" width="4" height="16" font="1"> </text>
<text top="1169" left="131" width="4" height="16" font="1"> </text>
<text top="162" left="184" width="21" height="13" font="4">(4) </text>
</page>"""),
        ]

        for input, expected in tests:
            page = lxml.etree.fromstring(input)
            question_scraper.remove_headers_from_page(page)

            self.assertEqual(lxml.etree.tostring(page, encoding='unicode'), expected)

# 517147_1

