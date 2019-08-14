# -*- coding: utf-8 -*-
import distutils.spawn
import hashlib
import os
import sys
import re
import requests
import subprocess
import tempfile
import warnings
import datetime
import lxml.etree

import parslepy

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from za_hansard.models import Question, QuestionPaper

# from https://github.com/scraperwiki/scraperwiki-python/blob/a96582f6c20cc1897f410d522e2a5bf37d301220/scraperwiki/utils.py#L38-L54
# Copied rather than included as the scraperwiki __init__.py was having trouble
# loading the sqlite code, which is something we don't actually need.

def ensure_executable_found(name):
    if not distutils.spawn.find_executable(name):
        raise ImproperlyConfigured("Can't find executable '{0}' which is needed by this code".format(name))

ensure_executable_found("pdftohtml")
def pdftoxml(pdfdata):
    """converts pdf file to xml file"""
    pdffout = tempfile.NamedTemporaryFile(suffix='.pdf')
    pdffout.write(pdfdata)
    pdffout.flush()

    xmlin = tempfile.NamedTemporaryFile(mode='r', suffix='.xml')
    tmpxml = xmlin.name # "temph.xml"
    cmd = 'pdftohtml -xml -nodrm -zoom 1.5 -enc UTF-8 -noframes "%s" "%s"' % (pdffout.name, os.path.splitext(tmpxml)[0])
    cmd = cmd + " >/dev/null 2>&1" # can't turn off output, so throw away even stderr yeuch
    os.system(cmd)

    pdffout.close()
    #xmlfin = open(tmpxml)
    xmldata = xmlin.read()
    xmlin.close()

    # pdftohtml version 0.18.4 occasionally produces bad markup of the form <b>...<i>...</b> </i>
    # Since ee don't actually need <i> tags, we may as well get rid of them all now, which will fix this.
    # Note that we're working with a byte string version of utf-8 encoded data here.

    xmldata = re.sub(r'</?i>', '', xmldata)

    return xmldata


ensure_executable_found("antiword")
def extract_answer_text_from_word_document(filename):
    text = check_output_wrapper(['antiword', filename]).decode('unicode-escape')

    # strip out lines that are just '________'
    bar_regex = re.compile(r'^_+$', re.MULTILINE)
    text = bar_regex.sub('', text)

    return text

def check_output_wrapper(*args, **kwargs):

    # Python 2.7
    if hasattr(subprocess, 'check_output'):
        return subprocess.check_output(*args)

    # Backport to 2.6 from https://gist.github.com/edufelipe/1027906
    else:
        process = subprocess.Popen(stdout=subprocess.PIPE, *args, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get('args', args[0])
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
        return output

class BaseDetailIterator(object):

    base_url = 'http://www.parliament.gov.za/live/'

    def __init__(self, start_list_url):

        self.details = []  # Question URLs that we have collected from tha list
        self.next_list_url = start_list_url  # The next list page to fetch urls from

    def __iter__(self):
        return self

    def next(self):
            # If needed and possible try to fetch more urls from the next list page
        while len(self.details) == 0 and self.next_list_url:
            self.get_details()

        # Return a url if we can.
        if len(self.details):
            return self.details.pop(0)
        else:
            raise StopIteration

    def url_get(self, url):
        """Super simple method to retrieve url and return content. Intended to be easily mocked in tests"""
        r = requests.get(url)
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException:
            print "Error while fetching", url
            raise
        return r.text

class QuestionDetailIterator(BaseDetailIterator):

    question_parsing_rules = {
        "papers(table.tableOrange_sep tr)":
            [{"cell(td)":[{"contents":".","url(a)":"@href"}]}],
        "next(table.tableOrange_sep table table td a)":
            [{"contents":".","url":"@href"}]
    }

    def get_details(self):
        print 'Questions (%s)' % self.next_list_url

        contents = self.url_get(self.next_list_url)

        p = parslepy.Parselet(self.question_parsing_rules)
        page = p.parse_fromstring(contents)

        for row in page['papers']:
            if len(row['cell']) == 11:
                url = row['cell'][8]['url']
                root, ext = os.path.splitext(os.path.split(url)[1])
                self.details.append({
                    "name": row['cell'][0]['contents'],
                    "language": row['cell'][6]['contents'],
                    "url": self.base_url + url,
                    "house": row['cell'][4]['contents'],
                    "date": row['cell'][2]['contents'],
                    "type": ext[1:],

                    # This is also in the pdf's metadata, but it's easier to
                    # get it from here
                    "document_number": int(root.split('_')[0]),
                    })

        # check for next page of links (or None if not found)
        self.next_list_url = None
        for cell in page['next']:
            if cell['contents'] == 'Next':
                next_url = self.base_url + cell['url']
                if self.next_list_url == next_url:
                    raise Exception("Possible url loop detected, next url '{0}' has not changed.".format(next_url))
                self.next_list_url = next_url
                break

class AnswerDetailIterator(BaseDetailIterator):
    answer_parsing_rules = {
        "papers(table.tableOrange_sep tr)" : [{"cell(td)":[{"contents":".","url(a)":"@href"}]}],
        "next(table.tableOrange_sep table table td a)": [{"contents":".","url":"@href"}]
    }

    # RNW2562-131119
    # RNW1120A-130820
    # RNO11W1497-130923
    # RNO204-130822
    # RNW1836-130917.Annexure
    # RNOP13-131107
    # RNW1143B-131127
    # RNW3153--131202
    # RNw2116-130822
    # RNo203-130822
    # RNW41-130326 AMENDED
    # RNO130314
    # RNW3148-121219 LAPSED
    # RNW2680-1212114

    # FIXME Cope with written and oral in the opposite order
    # RNW855O134-091015
    # Cope with spaces around the -
    # RNW26 - 090224

    # DP? Deputy President?
    # RNODP05-130424

    known_bad_document_names = (
    # Bad Dates
    'RNW2949-1311114',
    'RNW1920-13823',
    )

    document_name_regex = re.compile(r'^R(?P<house>[NC])(?:O(?P<president>D?P)?(?P<oral_number>\d+))?(?:W(?P<written_number>\d+))?-+(?P<date_string>\d{6})$')

    def get_details(self):
        sys.stdout.write('Answers {0}\n'.format(self.next_list_url))

        contents = self.url_get(self.next_list_url)
        page = parslepy.Parselet(self.answer_parsing_rules).parse_fromstring(contents)

        for row in page['papers']:
            if len(row['cell']) == 11:
                url = row['cell'][8]['url']
                types = url.partition(".")
                date_published = row['cell'][2]['contents'].strip()
                try:
                    date_published = datetime.datetime.strptime(date_published, '%d %B %Y').date()
                except:
                    warnings.warn("Failed to parse date (%s)" % date_published)
                    date_published = None
                    continue

                document_name = row['cell'][0]['contents'].strip().upper()

                try:
                    document_data = self.document_name_regex.match(document_name).groupdict()
                except:
                    if document_name not in self.known_bad_document_names:
                        sys.stdout.write('SKIPPING bad document_name {0}\n'
                                         .format(document_name))
                    continue

                # FIXME - Temporary fix for launch
                # drop anything which doesn't have a written_number
                if not document_data['written_number']:
                    continue

                # The President and vice Deputy President have their own
                # oral question sequences.
                president = document_data.pop('president')

                if president == 'P':
                    document_data['president_number'] = document_data.pop('oral_number')
                if president == 'DP':
                    document_data['dp_number'] = document_data.pop('oral_number')

                document_data.update(dict(
                    document_name=document_name,
                    date_published=date_published,
                    language=row['cell'][6]['contents'],
                    url=self.base_url + url,
                    type=types[2],
                    ))

                try:
                    document_data['date'] = datetime.datetime.strptime(
                        document_data.pop('date_string'),
                        '%y%m%d',
                        ).date()
                except:
                    sys.stdout.write(
                        "BAILING on {0} - problem converting date\n"
                        .format(document_name)
                        )
                    continue

                # We don't want anything from before the 2009 election.
                if document_data['date'] < datetime.date(2009, 4, 22):
                    continue

                document_data['year'] = document_data['date'].year

                self.details.append(document_data)

        # check for next page of links (or None if not found)
        self.next_list_url = None
        for cell in page['next']:
            if cell['contents'] == 'Next':
                next_url = self.base_url + cell['url']

                if self.next_list_url == next_url:
                    raise Exception("Possible url loop detected, next url '{0}' has not changed.".format(next_url))

                self.next_list_url = next_url
                break


page_header_regex = re.compile(ur"\s*(?:{0}|{1})\s*".format(
        ur'(?:\d+ \[)?[A-Z][a-z]+day, \d+ [A-Z][a-z]+ \d{4}(?:\] \d+)? INTERNAL QUESTION PAPER: (?:NATIONAL ASSEMBLY|NATIONAL COUNCIL OF PROVINCES) NO \d+[─-]\d{4}',
        ur'[A-Z][a-z]+day, \d+ [A-Z][a-z]+ \d{4} INTERNAL QUESTION PAPER: (?:NATIONAL ASSEMBLY|NATIONAL COUNCIL OF PROVINCES) NO \d+\s*[─-]\s*\d{4} \d+',
        )
                               )

def remove_headers_from_page(page):
    ur"""Remove unwanted headers at top of page.
    page must be a page element from the lxml etree of a
    question paper generated by pdftoxml.
    This function modifies page in place by removing

    1) The page number
    2) The date bit
    3) The title

    of the document which are are in the <text> elements at the at the top of
    every page.

    Note that the page number referred to here is the one in a text element
    from the original PDF, and not the one added in by pdftoxml as an attribute
    of each <page> element.

    For example, 559662_1.xml has a page which starts

    # <page number="2" position="absolute" top="0" left="0" height="1263" width="892">
    # <text top="80" left="85" width="750" height="16" font="1"> 273 </text>
    # <text top="80" left="607" width="205" height="16" font="1">[<i>Friday, 13 December 2013 </i></text>
    # <text top="1197" left="364" width="447" height="11" font="2">INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 37─2013 </text>

    We would like to get rid of these three text elements.

    # Check page_header_regex works
    >>> page_header_regex.match(u'Friday, 13 December 2013] 272 INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 37─2013 ') is not None
    True
    >>> page_header_regex.match(u' 273 [Friday, 13 December 2013 INTERNAL QUESTION PAPER: NATIONAL COUNCIL OF PROVINCES NO 37─2013 ') is not None
    True
    >>> page_header_regex.match(u'239 [Friday, 19 April 2013 INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 12─2013 ') is not None
    True
    >>> page_header_regex.match(u' Friday, 9 October 2009 INTERNAL QUESTION PAPER: NATIONAL ASSEMBLY NO 20 - 2009 533') is not None
    True

    """

    accumulated = ''

    # 10 text elements should be enough to catch all
    # the headers, and few enough to prevent us interfering
    # with more than one question if it all goes wrong.
    for text_el in page.xpath('text[position()<=10]'):
        accumulated += re.match(ur'(?s)<text.*?>(.*?)</text>', lxml.etree.tostring(text_el, encoding='unicode')).group(1)
        accumulated = re.sub(ur'(?u)<i>(.*?)</i>', ur'\1', accumulated)
        accumulated = re.sub(ur'(?u)</i>(.*?)<i>', ur'\1', accumulated)
        accumulated = re.sub(ur'(?u)(\s+)', ur' ', accumulated)

        if page_header_regex.match(accumulated):
            for to_remove in text_el.itersiblings(preceding=True):
                page.remove(to_remove)

            page.remove(text_el)
            break


class QuestionPaperParser(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_questions(self):
        url = self.kwargs['url']

        pdfdata = self.get_question_pdf_from_url(url)

        if not pdfdata:
            return

        xmldata = self.get_question_xml_from_pdf(pdfdata)

        if not xmldata:
            sys.stdout.write(' SKIPPING - Got no XML data\n')
            return

        #self.stderr.write("URL %s\n" % url)
        #self.stderr.write("PDF len %d\n" % len(pdfdata))
        #self.stderr.write("XML %s\n" % xmldata)

        self.create_questions_from_xml(xmldata, url)

    def get_question_pdf_from_url(self, url):
        # FIXME - Cope with an HTTP error, etc here.
        contents_filename = os.path.join(
            settings.QUESTION_CACHE,
            hashlib.md5(url).hexdigest(),
            )

        if os.path.exists(contents_filename):
            with open(contents_filename) as f:
                contents = f.read()
        else:
            response = requests.get(url)

            if response.status_code == requests.codes.ok:
                contents = response.content
            else:
                sys.stdout.write(' SKIPPING - Bad response\n')
                return

            with open(contents_filename, 'wb') as f:
                f.write(contents)

        return contents

    def get_question_xml_from_pdf(self, pdfdata):
        return pdftoxml(pdfdata)


    session_re = re.compile(
        ur"\[No\s*(?P<issue_number>\d+)\s*[\u2013\u2014]\s*(?P<year>\d{4})\]\s+(?P<session>[a-zA-Z]+)\s+SESSION,\s+(?P<parliament>[a-zA-Z]+)\s+PARLIAMENT",
        re.UNICODE | re.IGNORECASE)

    def get_question_paper(self, chunk):
        """
        # Checks for session_re
        >>> session_string = u'[No 37\u20142013] FIFTH SESSION, FOURTH PARLIAMENT'
        >>> match = QuestionPaperParser.session_re.match(session_string)
        >>> match.groups()
        (u'37', u'2013', u'FIFTH', u'FOURTH')
        >>> session_string = u'[No 20 \u2013 2009] First Session, Fourth Parliament'
        >>> match = QuestionPaperParser.session_re.match(session_string)
        >>> match.groups()
        (u'20', u'2009', u'First', u'Fourth')
        """

        text_to_int = {
            'FIRST': 1,
            'SECOND': 2,
            'THIRD': 3,
            'FOURTH': 4,
            'FOURH': 4, # Yes, really.
            'FIFTH': 5,
            'SIXTH': 6,
            'SEVENTH': 7,
            'EIGHTH': 8,
            'NINTH': 9,
            'TENTH': 10,
            }

        house = self.kwargs['house']
        date_published = datetime.datetime.strptime(self.kwargs['date'], '%d %B %Y').date()

        question_paper = QuestionPaper(
            document_name=self.kwargs['name'],
            date_published=date_published,
            house=house,
            language=self.kwargs['language'],
            document_number=self.kwargs['document_number'],
            source_url=self.kwargs['url'],
            text='', #lxml.etree.tostring(chunk, pretty_print=True),
            )

        session_match = self.session_re.search(chunk)

        if session_match:
            question_paper.session_number = text_to_int.get(session_match.group('session').upper())
            parliament_number = question_paper.parliament_number = text_to_int.get(session_match.group('parliament').upper())
            question_paper.issue_number = int(session_match.group('issue_number'))
            question_paper.year = int(session_match.group('year'))

            if parliament_number < 4:
                sys.stdout.write(
                    '\nBAILING OUT: Parliament {0} is too long ago\n'
                    .format(parliament_number)
                    )
                return

        else:
            sys.stdout.write("\nBAILING OUT: Failed to find session, etc.\n")
            # Bail out without saving any questions so that we at least continue and work
            # on other question papers.
            return

        try:
            old_qp = QuestionPaper.objects.get(
                year=question_paper.year,
                issue_number=question_paper.issue_number,
                house=question_paper.house,
                parliament_number=parliament_number,
                )
            # FIXME - We need to be able to cope with reprints of question papers.
            sys.stdout.write("\nBAILING OUT: Question Paper {0} too similar to\n".format(question_paper.source_url))
            sys.stdout.write("                            {0}\n".format(old_qp.source_url))
        except QuestionPaper.DoesNotExist:
            question_paper.save()
            return question_paper

    question_re = re.compile(
        ur"""
          (?P<intro>
            (?P<number1>\d+)\.?\s+ # Question number
            [-a-zA-z]+\s+(?P<askedby>[-\w\s]+?) # Name of question asker, dropping the title
            \s*\((?P<party>[-\w\s]+)\)?
            \s+to\s+ask\s+the\s+
            (?P<questionto>[-\w\s(),:.]+)[:.]
            [-\u2013\w\s(),\[\]/]*?
          ) # Intro
          (?P<translated>\u2020)?\s*</b>\s*
          (?P<question>.*?)\s* # The question itself.
          (?P<identifier>(?P<house>[NC])(?P<answer_type>[WO])(?P<id_number>\d+)E) # Number 2
        """,
        re.UNICODE | re.VERBOSE)

    def get_questions_from_chunk(self, date, chunk):
        """
        # Checks for question_re

        # Shows the need for - in the party
        >>> qn = u'144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans: </b>Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details? CW187E'
        >>> match = QuestionPaperParser.question_re.match(qn)
        >>> match.groups()
        (u'144. Mr D B Feldman (COPE-Gauteng) to ask the Minister of Defence and Military Veterans:', u'144', u'D B Feldman', u'COPE-Gauteng', u'Minister of Defence and Military Veterans', None, u'Whether the deployment of the SA National Defence Force soldiers to the Central African Republic and the Democratic Republic of Congo is in line with our international policy with regard to (a) upholding international peace, (b) the promotion of constitutional democracy and (c) the respect for parliamentary democracy; if not, why not; if so, what are the (i) policies which underpin South African foreign policy and (ii) further relevant details?', u'CW187E', u'C', u'W', u'187')

        # Shows the need for \u2013 (en-dash) and / (in the date) in latter part of the intro
        >>> qn = u'409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11) </b>(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery? CW603E'
        >>> match = QuestionPaperParser.question_re.match(qn)
        >>> match.groups()
        (u'409. Mr M J R de Villiers (DA-WC) to ask the Minister of Public Works: [215] (Interdepartmental transfer \u2013 01/11)', u'409', u'M J R de Villiers', u'DA-WC', u'Minister of Public Works', None, u'(a) What were the reasons for a cut back on the allocation for the Expanded Public Works Programme to municipalities in the 2013-14 financial year and (b) what effect will this have on (i) job creation and (ii) service delivery?', u'CW603E', u'C', u'W', u'603')

        # Cope with missing close bracket
        >>> qn = u'1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:</b> Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009? NW1922E'
        >>> match = QuestionPaperParser.question_re.match(qn)
        >>> match.groups()
        (u'1517. Mr W P Doman (DA to ask the Minister of Cooperative Governance and Traditional Affairs:', u'1517', u'W P Doman', u'DA', u'Minister of Cooperative Governance and Traditional Affairs', None, u'Which approximately 31 municipalities experienced service delivery protests as referred to in his reply to oral question 57 on 10 September 2009?', u'NW1922E', u'N', u'W', u'1922')

        # Check we cope with no space before party in parentheses
        >>> qn = u'1569. Mr M Swart(DA) to ask the Minister of Finance: </b>Test question? NW1975E'
        >>> match = QuestionPaperParser.question_re.match(qn)
        >>> match.groups()
        (u'1569. Mr M Swart(DA) to ask the Minister of Finance:', u'1569', u'M Swart', u'DA', u'Minister of Finance', None, u'Test question?', u'NW1975E', u'N', u'W', u'1975')

        # Check we cope with a dot after the askee instead of a colon.
        >>> qn = u'1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning </b>Test question? NW2224E'
        >>> match = QuestionPaperParser.question_re.match(qn)
        >>> match.groups()
        (u'1875. Mr G G Hill-Lewis (DA) to ask the Minister in the Presidency. National Planning', u'1875', u'G G Hill-Lewis', u'DA', u'Minister in the Presidency', None, u'Test question?', u'NW2224E', u'N', u'W', u'2224')
        """
        questions = []

        for match in self.question_re.finditer(chunk):
            match_dict = match.groupdict()

            answer_type = match_dict[u'answer_type']
            number1 = match_dict.pop('number1')

            if answer_type == 'O':
                if re.search('(?i)to ask the Deputy President', match_dict['intro']):
                    match_dict[u'dp_number'] = number1
                elif re.search('(?i)to ask the President', match_dict['intro']):
                    match_dict[u'president_number'] = number1
                else:
                    match_dict[u'oral_number'] = number1
            elif answer_type == 'W':
                match_dict[u'written_number'] = number1
            else:
                sys.stdout.write("SKIPPING: Unrecognised answer type for {0}\n".format(match_dict['identifier']))
                continue

            match_dict[u'paper'] = self.question_paper

            match_dict[u'translated'] = bool(match_dict[u'translated'])
            match_dict[u'questionto'] = match_dict[u'questionto'].replace(':', '')

            match_dict[u'date'] = date
            match_dict[u'year'] = date.year

            # Party isn't actually stored in the question, so drop it before saving
            # Perhaps we can eventually use it to make sure we have the right person.
            # (and to tidy up the missing parenthesis.)
            match_dict.pop(u'party')

            questions.append(Question(**match_dict))

        return questions


    # FIXME - can this be replaced with a call to dateutil?
    date_re = re.compile(ur"\s*<b>\s*(?P<day_of_week>MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY),\s*(?P<day>\d{1,2})\s*(?P<month>JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s*(?P<year>\d{4})\s*</b>\s*")

    def chunkify(self, root):
        """
        >>> date_str = ur'<b>FRIDAY, 2 AUGUST 2013 </b>'
        >>> match = QuestionPaperParser.date_re.match(date_str)
        >>> match.groups()
        (u'FRIDAY', u'2', u'AUGUST', u'2013')

        """
        text_bits = [
            re.match(ur'(?s)<text.*?>(.*?)</text>', lxml.etree.tostring(el, encoding='unicode')).group(1)
            for el in root.iterfind('.//text')
            ]

        # Let's split text_bits up by dates
        chunk = []
        date = None

        chunks = []

        while text_bits:
            text_bit = text_bits.pop(0)
            date_match = self.date_re.match(text_bit)

            if not date_match:
                chunk.append(text_bit)

            if date_match or not text_bits:
                text = u''.join(chunk)

                # We may as well git rid of bolding or unbolding around whitespace.
                text = re.sub(ur'</b>(\s*)<b>', ur'\1', text)
                text = re.sub(ur'<b>(\s*)</b>', ur'\1', text)

                # Replace all whitespace with single spaces.
                text = re.sub(r'\s+', ' ', text)

                # As we're using the </b> to tell us when the intro is over, it would be
                # helpful if we could always have the colon on the same side of it.
                text = text.replace('</b>:', ':</b>')

                chunks.append((date, text))

                if text_bits:
                    chunk = []
                    date_str = "{day_of_week}, {day} {month} {year}".format(**date_match.groupdict())
                    date = datetime.datetime.strptime(date_str, "%A, %d %B %Y").date()

        intro_chunk = chunks.pop(0)[1]

        return intro_chunk, chunks


    def create_questions_from_xml(self, xmldata, url):
        # Sanity check on number of questions
        expected_question_count = len(re.findall(r'[NC][OW]\d+E', xmldata))

        text = lxml.etree.fromstring(xmldata)

        pages = text.iter('page')

        for page in pages:
            remove_headers_from_page(page)

        intro_chunk, chunks = self.chunkify(text)

        self.question_paper = self.get_question_paper(intro_chunk)

        # Bail out if we didn't get a question paper
        if not self.question_paper:
            return

        questions = []

        for date, chunk in chunks:
            questions.extend(self.get_questions_from_chunk(date, chunk))

        sys.stdout.write(' found {0} questions'.format(len(questions)))

        if len(questions) != expected_question_count:
            sys.stdout.write(" expected {0} - SUSPICIOUS".format(expected_question_count))

        sys.stdout.write('\n')

        # Question.objects.bulk_create(questions)
        for question in questions:
            # FIXME - As a temporary fix, let's ignore any questions which aren't for written
            # answer.
            if not question.written_number:
                continue

            # FIXME - Another temporary fix - disregard any question which was written and is
            # becoming oral
            if re.search(r'\[Written Question No', question.intro, re.IGNORECASE):
                continue

            try:
                existing_question = Question.objects.get(
                    id_number=question.id_number,
                    house=question.house,
                    year=question.year,
                )
                if existing_question.paper.date_published > question.paper.date_published:
                    # FIXME - in future real life, these duplicates will be bad.
                    # we need to be able to cope with a revised question or a question
                    # changing from oral to written, etc.
                    if question.identifier != existing_question.identifier:
                        sys.stdout.write("IDENTIFIER CHANGE: {0} already exists as {1} - keeping original version\n".format(question.identifier, existing_question.identifier))
                    else:
                        sys.stdout.write("DUPLICATE: {0} already exists - keeping original version\n".format(question.identifier))

                else:
                    sys.stdout.write("BAD DUPLICATE: {0} already exists as {1} - keeping OLD VERSION\n".format(question.identifier, existing_question.identifier))
            except Question.DoesNotExist:
                if Question.objects.filter(
                    written_number=question.written_number,
                    house=question.house,
                    year=question.year,
                    ).exists():
                    sys.stdout.write(
                        "DUPLICATE written_number {0} {1} {2} - SKIPPING\n"
                        .format(question.written_number, question.house, question.year)
                        )

                    # Interesting failures here:
                    # 998 - a typo, should have been 898
                    # 3641 - number repeated for questions with two identifiers by the same person NW4421E NW4422E
                    continue

                question.save()

