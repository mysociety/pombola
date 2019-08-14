import httplib
import urllib2
import sys
import re, os
import dateutil.parser
import string
import parslepy
import json
import time

import subprocess

from datetime import datetime, date, timedelta

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned

import requests

from za_hansard.models import Question, Answer, QuestionPaper
from za_hansard.importers.import_json import ImportJson
from instances.models import Instance

from speeches.models import Section, Speaker, Speech
from django.contrib.contenttypes.models import ContentType

# ideally almost all of the parsing code would be removed from this management
# command and put into a module where it can be more easily tested and
# separated. This is the start of that process.
from ... import question_scraper

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/601.4.4 (KHTML, like Gecko) Version/9.0.3 Safari/601.4.4'

CODE_RE_STRING = r'R?(?P<house>[NC])(?P<answer_type>[WO])(?P<id_number>\d+)(?P<lang>[AEX])?'

def strip_dict(d):
    """
    Return a new dictionary, like d, but with any string value stripped

    >>> d = {'a': ' foo   ', 'b': 3, 'c': '   bar'}
    >>> result = strip_dict(d)
    >>> type(result)
    <type 'dict'>
    >>> sorted(result.items())
    [('a', 'foo'), ('b', 3), ('c', 'bar')]
    """
    return dict((k, v.strip() if 'strip' in dir(v) else v) for k, v in d.items())

def all_from_api(start_url):
    next_url = start_url
    while next_url:
        r = requests.get(next_url)
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException:
            print "Error while fetching", next_url
            raise
        data = r.json()
        for member in data['results']:
            yield member
        next_url = data['next']

def get_identifier_for_title(question_or_answer):
    if question_or_answer.identifier:
        return str(question_or_answer.identifier)
    # If there's no correct identifer (as with those from the PMG
    # API), synthesize one from the written_number (etc.) and the
    # year:
    if question_or_answer.written_number:
        number = 'w' + str(question_or_answer.written_number)
    elif question_or_answer.oral_number:
        number = 'o' + str(question_or_answer.oral_number)
    elif question_or_answer.president_number:
        number = 'p' + str(question_or_answer.president_number)
    elif question_or_answer.dp_number:
        number = 'd' + str(question_or_answer.dp_number)
    return "{0}-{1}".format(question_or_answer.year, number)

def convert_url_to_https(url):
    return re.sub(r'^http:', 'https:', url)


class Command(BaseCommand):

    help = 'Check for new sources'
    option_list = BaseCommand.option_list + (
        make_option('--scrape-questions',
            default=False,
            action='store_true',
            help='Scrape questions (step 1)',
        ),
        make_option('--scrape-answers',
            default=False,
            action='store_true',
            help='Scrape answers (step 2)',
        ),
        make_option('--scrape-from-pmg',
            default=False,
            action='store_true',
            help='Scrape questions and answers from PMG (step 2.5)',
        ),
        make_option('--process-answers',
            default=False,
            action='store_true',
            help='Process answers (step 3)',
                    ),
        make_option('--match-answers',
            default=False,
            action='store_true',
            help='Match answers (step 4)',
        ),
        make_option('--save',
            default=False,
            action='store_true',
            help='Save Q&A as json (step 5)',
        ),
        make_option('--import-into-sayit',
            default=False,
            action='store_true',
            help='Import saved json to sayit (step 6)',
        ),
        make_option('--run-all-steps',
            default=False,
            action='store_true',
            help='Run all of the steps',
        ),
        make_option('--correct-existing-sayit-import',
            default=False,
            action='store_true',
            help='Correct the structure of existing data',
        ),
        make_option('--instance',
            type='str',
            default='default',
            help='Instance to import into',
        ),
        make_option('--limit',
            default=0,
            action='store',
            type='int',
            help='How far to go back (not set means all the way)',
        ),
        make_option('--fetch-to-limit',
            default=False,
            action='store_true',
            help="Don't stop when reaching seen questions, continue to --limit",
        ),
        make_option('--commit',
            default=False,
            action='store_true',
            help='Whether to commit SayIt import corrections',
        ),
    )

    start_url_q = ('http://www.parliament.gov.za/live/', 'content.php?Category_ID=236')
    start_url_a_na = ('http://www.parliament.gov.za/live/', 'content.php?Category_ID=248')
    start_url_a_ncop = ('http://www.parliament.gov.za/live/', 'content.php?Category_ID=249')

    def handle(self, *args, **options):
        if options['scrape_questions']:
            self.scrape_questions(*args, **options)
        elif options['scrape_answers']:
            self.scrape_answers(self.art_url_a_na, *args, **options)
            self.scrape_answers(self.start_url_a_ncop, *args, **options)
        elif options['scrape_from_pmg']:
            self.get_qa_from_pmg_api(*args, **options)
        elif options['process_answers']:
            self.process_answers(*args, **options)
        elif options['match_answers']:
            self.match_answers(*args, **options)
        elif options['save']:
            self.qa_to_json(*args, **options)
        elif options['import_into_sayit']:
            self.import_into_sayit(*args, **options)
        elif options['run_all_steps']:
            self.scrape_questions(*args, **options)
            self.scrape_answers(self.start_url_a_na, *args, **options)
            self.scrape_answers(self.start_url_a_ncop, *args, **options)
            self.get_qa_from_pmg_api(*args, **options)
            self.process_answers(*args, **options)
            self.match_answers(*args, **options)
            self.qa_to_json(*args, **options)
            self.import_into_sayit(*args, **options)
        elif options['correct_existing_sayit_import']:
            self.correct_existing_sayit_import(*args, **options)
        else:
            raise CommandError("Please supply a valid option")

    def scrape_questions(self, *args, **options):

        start_url = self.start_url_q[0] + self.start_url_q[1]
        details = question_scraper.QuestionDetailIterator(start_url)

        count = 0
        errors = 0

        # detail here is a dictionary of the form:
        # {
        # "name":     row['cell'][0]['contents'],
        # "language": row['cell'][6]['contents'],
        # "url":      self.base_url + url,
        # "house":    row['cell'][4]['contents'],
        # "date":     row['cell'][2]['contents'],
        # "type":     types[2]
        # }

        for detail in details:
            count+=1

            source_url = detail['url']
            sys.stdout.write(
                "{count:5} {url} ".format(count=count, url=source_url))

            if detail['language'] != 'English':
                print "SKIPPING language is '{0}', not 'English'".format(
                    detail['language'])
            elif detail['type'] != 'pdf':
                print "SKIPPING type is '{0}', not 'pdf'".format(
                    detail['type'])
            else:
                if QuestionPaper.objects.filter(source_url=source_url).exists():
                    self.stdout.write('SKIPPING as file already handled\n')
                    if not options['fetch_to_limit']:
                        self.stdout.write("Stopping as '--fetch-to-limit' not given\n")
                        break
                else:
                    try:
                        self.stdout.write('PROCESSING')
                        question_scraper.QuestionPaperParser(**detail).get_questions()
                    except Exception as e:
                        self.stdout.write('ERROR handling {0}: {1}\n'.format(source_url, str(e)))
                        errors += 1
                        pass

            if options['limit'] and count >= options['limit']:
                break

        self.stdout.write( "Processed %d documents (%d errors)\n" % (count, errors) )


    def scrape_answers(self, start_url_a, *args, **options):
        start_url = start_url_a[0] + start_url_a[1]
        details = question_scraper.AnswerDetailIterator(start_url)

        count = 0

        for detail in details:
            count += 1
            detail = strip_dict(detail)

            url = detail['url']
            if Answer.objects.filter(url=url).exists():
                self.stdout.write('Answer {0} already exists\n'.format(url))
                if not options['fetch_to_limit']:
                    self.stdout.write("Stopping as '--fetch-to-limit' not given\n")
                    break
            else:
                existing_answers = Answer.objects.filter(
                    house=detail['house'],
                    year=detail['year'],
                    )

                if detail['oral_number']:
                    existing_answers = existing_answers.filter(oral_number=detail['oral_number'])
                if detail['written_number']:
                    existing_answers = existing_answers.filter(written_number=detail['written_number'])

                if existing_answers.exists():
                    # import pdb;pdb.set_trace()
                    # FIXME - We should work out which answer to keep rather than
                    # just keeping what we already have.
                    self.stdout.write(
                        'DUPLICATE: answer for {0} O{1} W{2} {3} already exists\n'.format(
                            detail['house'], detail['oral_number'], detail['written_number'], detail['year'],
                            )
                        )
                else:
                    # self.stdout.write('Adding answer for {0}\n'.format(url))
                    answer = Answer.objects.create(**detail)

            if options['limit'] and count >= options['limit']:
                break

    def handle_api_question_and_reply(self, data):
        if 'source_file' not in data:
            print "Skipping {0} due to a missing source_file".format(data['url'])
            return
        house = {
            'National Assembly': 'N'
        }[data['house']['name']]
        answer_type = {
            'written': 'W'
        }[data['answer_type']]
        askedby_name = ''
        askedby_pa_url = ''
        if 'asked_by_member' in data:
            askedby_name = data['asked_by_member']['name']
            if 'pa_url' in data['asked_by_member']:
                askedby_pa_url = data['asked_by_member']['pa_url']
        question_text = data['question']
        # 'code' is one of those like: "NW3847", but in the Code4SA /
        # PMG API data that's just composed (say) of 'NW' + the
        # written_number; they don't match with the NW codes that
        # questions already have in our data. So we can't use the
        # 'code' field for checking if the question already exists, so
        # try to identify a unique question by the number + year +
        # house. (The numbers reset each year.)
        year = data['date'][:4]
        # Add whatever number there is to the query:
        number_q_kwargs = {}
        number_found = False
        for filter_key, api_key in (
                ('written_number', 'written_number'),
                ('oral_number', 'oral_number'),
                ('president_number', 'president_number'),
                ('dp_number', 'deputy_president_number'),
        ):
            if data[api_key]:
                number_found = True
                number_q_kwargs[filter_key] = data[api_key]
        existing_kwargs = {'date__year': year, 'house': house}
        existing_kwargs.update(number_q_kwargs)
        if not number_found:
            # We won't be able to accurately tell whether a question
            # already exists if we don't have one of these number, so
            # ignore the question and answer completely in that
            # case. (This is a rare occurence.)
            print "Skipping {0} because no number was found".format(data['url'])
            return
        try:
            print "Found the existing question for", data['url']
            question = Question.objects.get(**existing_kwargs)
            # It might well be useful to add the corresponding PMG API
            # URL details (e.g. using their PA link to get the PA person)
            question.pmg_api_url = data['url']
            question.pmg_api_member_pa_url = askedby_pa_url
            question.pmg_api_source_file_url = data['source_file']['url']
            question.save()
        except Question.DoesNotExist:
            print "No existing question found; creating a new one for", data['url']
            # In which case, create it:
            question = Question.objects.create(
                # FIXME: I think this is actually the date of the
                # answer, not the date of the question.
                date=data['date'],
                # paper_id= <-- FIXME: not sure what this is
                question=question_text,
                questionto=data['question_to_name'],
                # The 'identifier' is the NW code; the Code4SA API
                # doesn't have this (the one under 'code' isn't
                # right).  The 'id_number' field is the number
                # extracted from 'identifier', so we don't have that
                # either. These fields are NOT NULL, however, so we
                # have to set them to something:
                identifier='',
                id_number=-1,
                intro=data['intro'],
                askedby=askedby_name,
                house=house,
                answer_type=answer_type,
                year=year,
                # date_transferred doesn't seem to be in API data
                translated=data['translated'],
                written_number=data['written_number'],
                oral_number=data['oral_number'],
                president_number=data['president_number'],
                dp_number=data['deputy_president_number'],
                pmg_api_url=data['url'],
                pmg_api_member_pa_url=askedby_pa_url,
                pmg_api_source_file_url=data['source_file']['url'],
            )
        # If there's already an answer, assume it's OK, except record
        # the PMG API URL if it hasn't got one:
        if question.answer:
            print "  That question already had an answer, updating it with API links"
            answer = question.answer
            existing_answer_pmg_api_url = answer.pmg_api_url
            if existing_answer_pmg_api_url:
                if convert_url_to_https(existing_answer_pmg_api_url) != convert_url_to_https(data['url']):
                    msg = "An existing answer's pmg_api_url conflicted "
                    msg += "with another one from the API. In the database, "
                    msg += "the question ID was {0}, the answer ID was {1}, "
                    msg += "and the PMG API URL was {2}. The new PMG API URL "
                    msg += "was {3}.  Check that in this case they're the same "
                    msg += "question and answer, but with two API URLs and "
                    msg += "different dates and source files"
                    print msg.format(
                        question.id,
                        answer.id,
                        existing_answer_pmg_api_url,
                        data['url'])
            else:
                answer.pmg_api_url = data['url']
                answer.save()
            return
        # Also check whether there's an answer that already exists for
        # that number, house and year, but which hasn't been
        # associated with a question. If that's the case, don't try to
        # create the answer (the uniqueness constraint will fail
        # anyway).  If so, then associate it with the question that we
        # will just have created (or already existed).
        existing_answer_qs = Answer.objects.filter(**existing_kwargs)
        if existing_answer_qs.exists():
            print "  Found an existing answer for that question; linking them"
            question.answer = existing_answer_qs.get()
            question.answer.pmg_api_url = data['url']
            question.answer.save()
        else:
            print "  Creating a new answer for that question."
            # Otherwise create the answer from the API data:
            document_name, dot_extension = os.path.splitext(
                data['source_file']['file_path'])
            answer = Answer.objects.create(
                document_name=document_name,
                oral_number=data['oral_number'],
                written_number=data['written_number'],
                president_number=data['president_number'],
                dp_number=data['deputy_president_number'],
                date=data['date'],
                year=data['year'],
                house=house,
                text=data['answer'],
                # Mark this as processed since we've already got the text
                # - the source file doesn't need to be parsed.
                processed_code=Answer.PROCESSED_OK,
                # This always seems to be empty in the existing data:
                name='',
                # FIXME: check that all the answers from the PMG API are
                # in English, or whether there should be metadata for
                # that?
                language='English',
                url=data['source_file']['url'],
                date_published=data['date'],
                type=dot_extension[1:],
                pmg_api_url=data['url']
            )
            question.answer = answer
        question.save()

    def get_qa_from_pmg_api(self, *args, **options):
        # Go through each member and minister looking for questions
        # URLs.
        for url in (
                'https://api.pmg.org.za/minister/',
                'https://api.pmg.org.za/member/',
        ):
            for m in all_from_api(url):
                questions_url = m['questions_url']
                for question in all_from_api(questions_url):
                    with transaction.atomic():
                        self.handle_api_question_and_reply(question)

    def process_answers(self, *args, **options):
        answers = Answer.objects.exclude(url=None)
        unprocessed = answers.exclude(processed_code=Answer.PROCESSED_OK)

        self.stdout.write("Processing %d records" % len(unprocessed))

        for row in unprocessed:
            filename = os.path.join(
                settings.ANSWER_CACHE,
                '%d.%s' % (row.id, row.type))

            if os.path.exists(filename):
                self.stdout.write('-')
            else:
                self.stdout.write('.')

                try:
                    request = urllib2.Request(
                        row.url,
                        headers={
                            'User-Agent': USER_AGENT
                        }
                    )
                    download = urllib2.urlopen(request)

                    with open(filename, 'wb') as save:
                        save.write(download.read())

                except urllib2.HTTPError as e:
                    row.processed_code = Answer.PROCESSED_HTTP_ERROR
                    row.save()
                    self.stderr.write('ERROR HTTPError while processing %d (%s)\n' % (row.id, e))
                    continue

                except urllib2.URLError as e:
                    self.stderr.write('ERROR URLError while processing %d (%s)\n' % (row.id, e))
                    continue

                except httplib.BadStatusLine as e:
                    self.stderr.write('ERROR BadStatusLine while processing %d (%s)\n' % (row.id, e))
                    continue

            try:
                text = question_scraper.extract_answer_text_from_word_document(filename)
                row.processed_code = Answer.PROCESSED_OK
                row.text = text
                row.save()
            except subprocess.CalledProcessError:
                self.stdout.write('ERROR in antiword processing %d\n' % row.id)
            except UnicodeDecodeError:
                self.stdout.write('ERROR in antiword processing (UnicodeDecodeError) %d\n' % row.id)


    def match_answers(self, *args, **options):
        # Only consider answers that aren't already associated with a
        # question. (In particular, we have the question / answer
        # association already for answers that have been fetched from
        # the PMG API.)
        for answer in Answer.objects.filter(question__isnull=True):
            written_q = Q(written_number=answer.written_number)
            oral_q = Q(oral_number=answer.oral_number)

            if answer.written_number and answer.oral_number:
                query = written_q | oral_q
            elif answer.written_number:
                query = written_q
            elif answer.oral_number:
                query = oral_q
            else:
                sys.stdout.write(
                    "Answer {0} {1} has no written or oral number - SKIPPING\n"
                    .format(answer.id, answer.document_name)
                    )
                continue

            try:
                question = Question.objects.get(
                    query,
                    year=answer.year,
                    house=answer.house,
                    )
            except Question.DoesNotExist:
                sys.stdout.write(
                    "No question found for {0} {1}\n"
                    .format(answer.id, answer.document_name)
                    )
                continue

            question.answer = answer
            question.save()

    def qa_to_json(self, *args, **options):
        questions = Question.objects.prefetch_related('answer')

        for question in questions:
            question_as_json = self.question_to_json(question)

            filename = os.path.join(
                settings.QUESTION_JSON_CACHE,
                "%d.json" % question.id)
            with open(filename, 'w') as outfile:
                outfile.write(question_as_json)
            self.stdout.write('Wrote question %s\n' % filename)

            if (question.answer and
                    question.answer.processed_code == Answer.PROCESSED_OK):

                answer_as_json = self.answer_to_json(question)

                filename = os.path.join(
                    settings.ANSWER_JSON_CACHE,
                    "%d.json" % question.answer.id)
                with open(filename, 'w') as outfile:
                    outfile.write(answer_as_json)
                self.stdout.write('Wrote answer %s\n' % filename)

    def question_to_json(self, question):
        question_as_json_data = self.question_to_json_data(question)

        return json.dumps(
            question_as_json_data,
            indent=1,
            sort_keys=True
        )

    def answer_to_json(self, question):
        answer_as_json_data = self.answer_to_json_data(question)

        return json.dumps(
            answer_as_json_data,
            indent=1,
            sort_keys=True
        )

    def question_to_json_data(self, question):
        #{
        # "speeches": [
        #  {
        #   "personname": "M Johnson",
        #   "party": "ANC",
        #   "text": "Mr M Johnson (ANC) chaired the meeting."
        #  },
        #  ...
        #  ],
        # "date": "2013-06-21",
        # "organization": "Agriculture, Forestry and Fisheries",
        # "reporturl": "http://www.pmg.org.za/report/20130621-report-back-from-departments-health-trade-and-industry-and-agriculture-forestry-and-fisheries-meat-inspection",
        # "title": "Report back from Departments of Health, Trade and Industry, and Agriculture, Forestry and Fisheries on meat inspection services and labelling in South Africa",
        ## "committeeurl": "http://www.pmg.org.za/committees/Agriculture,%20Forestry%20and%20Fisheries"

        # As of Python 2.7.3, time.strftime can't be trusted to preserve
        # unicodeness, hence the extra calls to unicode.

        parliament_number = ''
        if question.paper:
            source_url = question.paper.source_url
            parliament_number = question.paper.parliament_number
        elif question.pmg_api_source_file_url:
            source_url = question.pmg_api_source_file_url
        else:
            msg = "No source URL found for question with ID {0}"
            raise Exception, msg.format(question.id)

        question_as_json = {
            u'parent_section_titles': [
                u'Questions',
                u'Questions asked to the ' + self.correct_minister_title(
                    question.questionto),
            ],
            u'questionto': question.questionto,
            u'title': '{0} - {1}'.format(
                get_identifier_for_title(question),
                question.date.strftime(u'%d %B %Y'),
                ),
            u'date': self.format_date_for_json(question.date),
            u'speeches': [
                {
                    u'personname': question.askedby,
                    # party?
                    u'text': question.question,
                    u'tags': [u'question'],
                    u'date': self.format_date_for_json(question.date),
                    u'source_url': source_url,

                    # unused for import
                    u'type': u'question',
                    u'intro': question.intro,
                    u'translated': question.translated,
                },
            ],
            u'pmg_api_member_pa_url': question.pmg_api_member_pa_url,

            # random stuff that is NOT used by the JSON import
            u'oral_number': question.oral_number,
            u'written_number': question.written_number,
            u'identifier': question.identifier,
            u'askedby': question.askedby,
            u'answer_type': question.answer_type,
            u'parliament': parliament_number,
            u'pmg_api_url': question.pmg_api_url,
            u'pmg_api_source_file_url': question.pmg_api_source_file_url,
        }

        return question_as_json

    def answer_to_json_data(self, question):
        answer = question.answer
        parliament_number = ''
        if question.paper:
            parliament_number = question.paper.parliament_number
        answer_as_json = {
            u'parent_section_titles': [
                u'Questions',
                u'Questions asked to the ' + self.correct_minister_title(
                    question.questionto),
            ],
            u'questionto': question.questionto,
            u'title': '{0} - {1}'.format(
                get_identifier_for_title(question),
                question.date.strftime(u'%d %B %Y'),
                ),
            u'date': self.format_date_for_json(question.date),
            u'speeches': [
                {
                    u'personname': question.questionto,
                    # party?
                    u'text': answer.text,
                    u'tags': [u'answer'],
                    u'date': self.format_date_for_json(answer.date),
                    u'source_url': answer.url,

                    # unused for import
                    u'name' : answer.name,
                    u'persontitle': question.questionto,
                    u'type': u'answer',
                },
            ],

            # random stuff that is NOT used by the JSON import
            u'oral_number': question.oral_number,
            u'written_number': question.written_number,
            u'identifier': question.identifier,
            u'askedby': question.askedby,
            u'answer_type': question.answer_type,
            u'parliament': parliament_number,
            u'pmg_api_url': answer.pmg_api_url,
        }

        return answer_as_json

    def format_date_for_json(self, date):
        return unicode(date.strftime(u'%Y-%m-%d'))

    def import_into_sayit(self, *args, **options):
        instance = None
        try:
            instance = Instance.objects.get(label=options['instance'])
        except Instance.DoesNotExist:
            raise CommandError("Instance specified not found (%s)" % options['instance'])

        questions = (Question.objects
                .filter( sayit_section = None ) # not already imported
                )

        section_ids = []
        for question in questions.iterator():
            path = os.path.join(
                settings.QUESTION_JSON_CACHE,
                "%d.json" % question.id)
            if not os.path.exists(path):
                continue

            importer = ImportJson(instance=instance)
            #try:
            self.stderr.write("TRYING %s\n" % path)
            section = importer.import_document(path)
            section_ids.append(section)
            question.sayit_section = section
            question.last_sayit_import = datetime.now().date()
            question.save()
            #except Exception as e:
                #self.stderr.write('WARN: failed to import %d: %s' %
                    #(question.id, str(e)))

        self.stdout.write( 'Questions:\n' )
        self.stdout.write(str(section_ids))
        self.stdout.write( '\n' )
        self.stdout.write('Questions: Imported %d / %d sections\n' %
                (len(section_ids), len(questions)))

        answers = (Answer.objects
                   .filter(sayit_section=None)  # not already imported
                   .filter(processed_code=Answer.PROCESSED_OK)
                   )

        section_ids = []
        for answer in answers.iterator():
            path = os.path.join(
                settings.ANSWER_JSON_CACHE,
                "%d.json" % answer.id)
            if not os.path.exists(path):
                continue

            importer = ImportJson(instance=instance)
            self.stderr.write("TRYING %s\n" % path)
            #limit to 2 speeches per section to avoid duplicating speeches
            #added prior to the addition of the answer sayit_section field
            section = importer.import_document(path, 2)
            section_ids.append(section.id)
            answer.sayit_section = section
            answer.last_sayit_import = datetime.now().date()
            answer.save()

        self.stdout.write('\n')
        self.stdout.write('Answers:\n')
        self.stdout.write(str(section_ids))
        self.stdout.write('\n')
        self.stdout.write('Answers: Imported %d / %d sections\n' %
            (len(section_ids), len(answers)))

    def correct_existing_sayit_import(self, *args, **options):
        from pombola.slug_helpers.models import SlugRedirect
        instance = None
        try:
            instance = Instance.objects.get(label=options['instance'])
        except Instance.DoesNotExist:
            raise CommandError("Instance specified not found (%s)" %
                               options['instance'])

        #check that sections are correctly named
        sections = Section.objects.filter(parent__title='Questions')

        for section in sections:
            minister = section.title.replace('Questions asked to the ', '')
            new_minister = self.correct_minister_title(minister)

            if minister != new_minister:
                #the name needs to be corrected. this is achieved by moving
                #children to the correct section and deleting the current one
                #and by changing the relevant speakers

                if options['commit']:
                    new_section = Section.objects.get_or_create_with_parents(
                        instance=instance,
                        headings=[
                            u'Questions',
                            u'Questions asked to the ' + new_minister,
                        ])

                    new_speaker, created = Speaker.objects.get_or_create(
                        instance=instance,
                        name=new_minister)

                    for child in section.children.all():
                        child.parent = new_section
                        child.save()

                        for speech in child.speech_set.filter(tags__name='answer'):
                            speech.speaker_display = new_minister
                            speech.speaker = new_speaker
                            speech.save()

                    # If this is a top level import, it will break the
                    # za-hansard tests when run in isolation (i.e. not
                    # as part of Pombola)
                    from pombola.slug_helpers.models import SlugRedirect
                    SlugRedirect.objects.create(
                        content_type=ContentType.objects.get_for_model(Section),
                        old_object_slug=section.get_path,
                        new_object_id=new_section.id,
                        new_object=new_section,
                    )

                    section.delete()
                else:
                    self.stdout.write('Correcting %s to %s' % (minister, new_minister))

        #check that answer dates and source urls are correct (previously,
        #answer dates were set to those of their question and source_urls
        #were not set - requiring checking and correction)
        answers = Answer.objects.exclude(sayit_section=None)

        for answer in answers:
            try:
                speech = Speech.objects.get(
                    section_id=answer.sayit_section,
                    tags__name='answer')

                speech_start_date = answer.date_published

                if speech.start_date != speech_start_date:
                    self.stdout.write(
                        'Correcting %s: %s to %s' % (
                            answer.document_name,
                            speech.start_date,
                            speech_start_date
                        ))

                    if options['commit']:
                        speech.start_date = speech_start_date
                        speech.end_date = speech_start_date
                        speech.save()

                if speech.source_url != answer.url:
                    self.stdout.write(
                        'Correcting %s: %s to %s' % (
                            answer.document_name,
                            speech.source_url,
                            answer.url
                        ) )

                    if options['commit']:
                        speech.source_url = answer.url
                        speech.save()

            except MultipleObjectsReturned:
                #only one answer should be returned - requires investigation
                self.stdout.write(
                    'MultipleObjectsReturned %s - id %s' % (
                        answer.document_name,
                        answer.id
                    ) )

        #check that question source_urls are correct
        questions = Question.objects.exclude( sayit_section = None )

        for question in questions:
            try:
                speech = Speech.objects.get(
                    section_id=question.sayit_section,
                    tags__name='question')

                if speech.source_url != question.paper.source_url:
                    self.stdout.write(
                        'Correcting question %s: %s to %s' % (
                            question.identifier,
                            speech.source_url,
                            question.paper.source_url
                        ) )

                    if options['commit']:
                        speech.source_url = question.paper.source_url
                        speech.save()

            except MultipleObjectsReturned:
                #only one answer should be returned - requires investigation
                self.stdout.write(
                    'MultipleObjectsReturned question %s - id %s' % (
                        question.identifier,
                        question.id
                    ) )

        if not options['commit']:
            self.stdout.write('Corrections not saved. Use --commit.')

    def correct_minister_title(self, minister_title):
        corrections = {
            "Minister President of the Republic":
                "President of the Republic",
            "Minister in The Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in the Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Questions asked to the Minister in The Presidency National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in the Presidency. National Planning Commission":
                "Minister in the Presidency: National Planning Commission",
            "Minister in The Presidency": "Minister in the Presidency",
            "Minister in The Presidency Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance , Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Management and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well as Administration":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the Presidency, Performance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister in the PresidencyPerformance Monitoring and Evaluation as well as Administration in the Presidency":
                "Minister in the Presidency: Performance Monitoring and Evaluation as well as Administration in the in the Presidency",
            "Minister of Women in The Presidency":
                "Minister of Women in the Presidency",
            "Minister of Agriculture, Fisheries and Forestry":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Minister of Agriculture, Forestry and Fisheries":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Agriculture, Foresty and Fisheries":
                "Minister of Agriculture, Forestry and Fisheries",
            "Minister of Minister of Basic Education":
                "Minister of Basic Education",
            "Minister of Basic Transport":
                "Minister of Transport",
            "Minister of Communication":
                "Minister of Communications",
            "Minister of Cooperative Government and Traditional Affairs":
                "Minister of Cooperative Governance and Traditional Affairs",
            "Minister of Defence and MilitaryVeterans":
                "Minister of Defence and Military Veterans",
            "Minister of Heath":
                "Minister of Health",
            "Minister of Higher Education":
                "Minister of Higher Education and Training",
            "Minister of Minister of International Relations and Cooperation":
                "Minister of International Relations and Cooperation",
            "Minister of Justice and Constitutional development":
                "Minister of Justice and Constitutional Development",
            "Minister of Justice and Constitutional Developoment":
                "Minister of Justice and Constitutional Development",
            "Minister of Mining":
                "Minister of Mineral Resources",
            "Minister of Public Enterprise":
                "Minister of Public Enterprises",
            "Minister of the Public Service and Administration":
                "Minister of Public Service and Administration",
            "Minister of Public Work":
                "Minister of Public Works",
            "Minister of Rural Development and Land Affairs":
                "Minister of Rural Development and Land Reform",
            "Minister of Minister of Rural Development and Land Reform":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land Reform Question":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land Reforms":
                "Minister of Rural Development and Land Reform",
            "Minister of Rural Development and Land reform":
                "Minister of Rural Development and Land Reform",
            "Minister of Sport and Recreaton":
                "Minister of Sport and Recreation",
            "Minister of Sports and Recreation":
                "Minister of Sport and Recreation",
            "Minister of Water and Enviromental Affairs":
                "Minister of Water and Environmental Affairs",
            "Minister of Women, Children andPeople with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Children en People with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Children and Persons with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Minister of Women, Youth, Children and People with Disabilities":
                "Minister of Women, Children and People with Disabilities",
            "Higher Education and Training":
                "Minister of Higher Education and Training",
            "Minister Basic Education":
                "Minister of Basic Education",
            "Minister Health":
                "Minister of Health",
            "Minister Labour":
                "Minister of Labour",
            "Minister Public Enterprises":
                "Minister of Public Enterprises",
            "Minister Rural Development and Land Reform":
                "Minister of Rural Development and Land Reform",
            "Minister Science and Technology":
                "Minister of Science and Technology",
            "Minister Social Development":
                "Minister of Social Development",
            "Minister Trade and Industry":
                "Minister of Trade and Industry",
            "Minister in Communications":
                "Minister of Communications",
            "Minister of Arts and Culture 102. Mr D J Stubbe (DA) to ask the Minister of Arts and Culture":
                "Minister of Arts and Culture",
        }

        #the most common error is the inclusion of a hyphen (presumably due to
        #line breaks in the original document). No ministers have a hyphen in
        #their title so we can do a simple replace.
        minister_title = minister_title.replace('-', '')

        #correct mispellings of 'minister'
        minister_title = minister_title.replace('Minster', 'Minister')

        #it is also common for a minister to be labelled "minister for" instead
        #of "minister of"
        minister_title = minister_title.replace('Minister for', 'Minister of')

        #remove any whitespace
        minister_title = minister_title.strip()

        #apply manual corrections
        minister_title = corrections.get(minister_title, minister_title)

        return minister_title
