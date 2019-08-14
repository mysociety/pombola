# -*- coding: utf-8 -*-

from datetime import date
from mock import patch

from django.core.management import call_command
from django.test import TestCase

from za_hansard.models import Answer, Question

EXAMPLE_QUESTION = {
    'question': 'Why did the chicken cross the road?',
    'answer': 'To get to the other side',
    'asked_by_member': {
        'name': 'Groucho Marx',
        'pa_url': 'http://www.pa.org.za/person/groucho-marx/',
     },
    'source_file': {
        'url': 'http://example.org/chicken-joke.docx',
        'file_path': 'chicken-joke.docx',
    },
    'house': {
        'name': 'National Assembly',
    },
    'answer_type': 'written',
    'date': '2016-09-06',
    'year': '2016',
    'written_number': 12345,
    'oral_number': None,
    'president_number': None,
    'deputy_president_number': None,
    'url': 'http://api.pmg.org.za/example-question/5678/',
    'question_to_name': 'Minister of Arts and Culture',
    'intro': 'Groucho Marx to ask the Minister of Arts and Culture',
    'translated': False,
}


class PMGAPITests(TestCase):

    @patch('za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_new_q_and_a_created(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        # Assertions about the question first:
        self.assertEqual(
            question.question, 'Why did the chicken cross the road?')
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.identifier, '')
        self.assertEqual(question.id_number, -1)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date, date(2016, 9, 6))
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.askedby, 'Groucho Marx')
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url, 'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url, 'http://example.org/chicken-joke.docx')
        # Then asertions about the answer:
        self.assertEqual(answer.text, 'To get to the other side')
        self.assertEqual(answer.document_name, 'chicken-joke')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.oral_number, None)
        self.assertEqual(answer.president_number, None)
        self.assertEqual(answer.dp_number, None)
        self.assertEqual(answer.date, date(2016,9,6))
        self.assertEqual(answer.year, 2016)
        self.assertEqual(answer.house, 'N')
        self.assertEqual(answer.processed_code, Answer.PROCESSED_OK)
        self.assertEqual(answer.name, '')
        self.assertEqual(answer.language, 'English')
        self.assertEqual(answer.url, 'http://example.org/chicken-joke.docx')
        self.assertEqual(answer.date_published, date(2016,9,6))
        self.assertEqual(answer.type, 'docx')
        self.assertEqual(answer.sayit_section, None)
        self.assertEqual(answer.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')

    @patch('za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_only_new_answer_if_question_exists(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing question with the right year and
        # written_number; this test makes sure that a duplicate
        # question isn't created in that circumstance.
        Question.objects.create(
            question=u'Forsooth, why hath the chicken crossèd the road?',
            written_number=12345,
            date=date(2016, 1, 27),
            house='N',
            answer_type='W',
            year=2016,
            identifier='NW9876543E',
            id_number='9876543',
            askedby='G Marx',
            translated=False,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        # It should have the old question text, identifier and askedby
        # still, in particular:
        self.assertEqual(
            question.question,
            u'Forsooth, why hath the chicken crossèd the road?')
        self.assertEqual(question.askedby, 'G Marx')
        self.assertEqual(question.identifier, 'NW9876543E')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 1, 27))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url, 'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url, 'http://example.org/chicken-joke.docx')

    @patch('za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_nothing_created_if_both_exist(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing question and answer with the right year
        # and written_number; this test makes sure neither a new
        # question nor a new answer is created in this case:
        existing_answer = Answer.objects.create(
            text='For to arrive unto the other side',
            written_number=12345,
            date=date(2016, 9, 1),
            date_published=date(2016,9,6),
            year=2016,
            house='N',
            processed_code=Answer.PROCESSED_OK,
        )
        Question.objects.create(
            question=u'Forsooth, why hath the chicken crossèd the road?',
            answer=existing_answer,
            written_number=12345,
            date=date(2016, 1, 27),
            house='N',
            answer_type='W',
            year=2016,
            identifier='NW9876543E',
            id_number='9876543',
            askedby='G Marx',
            translated=False,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        self.assertEqual(question.answer, answer)
        # It should have the old question text, identifier and askedby
        # still, in particular:
        self.assertEqual(
            question.question,
            u'Forsooth, why hath the chicken crossèd the road?')
        self.assertEqual(question.askedby, 'G Marx')
        self.assertEqual(question.identifier, 'NW9876543E')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 1, 27))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url, 'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url, 'http://example.org/chicken-joke.docx')
        # Now check that the answer still has some old values:
        self.assertEqual(answer.text, 'For to arrive unto the other side')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.date, date(2016, 9, 1))
        self.assertEqual(answer.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')

    @patch('za_hansard.management.commands.za_hansard_q_and_a_scraper.all_from_api')
    def test_question_created_if_answer_exists(self, fake_all_from_api):
        def api_one_question_and_answer(url):
            if url == 'https://api.pmg.org.za/minister/':
                yield {
                    'questions_url': "http://api.pmg.org.za/minister/2/questions/",
                }
                return
            elif url == 'https://api.pmg.org.za/member/':
                return
            elif url == 'http://api.pmg.org.za/minister/2/questions/':
                yield EXAMPLE_QUESTION
            else:
                raise Exception("Unfaked URL '{0}'".format(url))
        fake_all_from_api.side_effect = api_one_question_and_answer
        # Create an existing answer with the right year and
        # written_number, but no corresponding existing question.
        Answer.objects.create(
            text='For to arrive unto the other side',
            written_number=12345,
            date=date(2016, 9, 1),
            date_published=date(2016,9,6),
            year=2016,
            house='N',
            processed_code=Answer.PROCESSED_OK,
        )
        # Run the command:
        call_command('za_hansard_q_and_a_scraper', scrape_from_pmg=True)
        # Check that what we expect has been created: one new answer,
        # but there's still just the existing question:
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        answer = Answer.objects.get()
        question = Question.objects.get()
        self.assertEqual(question.answer, answer)
        # It should have the new question text
        self.assertEqual(
            question.question,
            u'Why did the chicken cross the road?')
        self.assertEqual(question.askedby, 'Groucho Marx')
        self.assertEqual(question.identifier, '')
        self.assertEqual(question.year, 2016)
        self.assertEqual(question.date, date(2016, 9, 6))
        # These fields of question should be as it would
        # if this were a new import.:
        self.assertEqual(question.answer, answer)
        self.assertEqual(question.written_number, 12345)
        self.assertEqual(question.oral_number, None)
        self.assertEqual(question.dp_number, None)
        self.assertEqual(question.president_number, None)
        self.assertEqual(question.house, 'N')
        self.assertEqual(question.answer_type, 'W')
        self.assertEqual(question.date_transferred, None)
        self.assertEqual(question.translated, False)
        self.assertEqual(question.last_sayit_import, None)
        self.assertEqual(question.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')
        self.assertEqual(question.pmg_api_member_pa_url, 'http://www.pa.org.za/person/groucho-marx/')
        self.assertEqual(question.pmg_api_source_file_url, 'http://example.org/chicken-joke.docx')
        # Now check that the answer still has some old values:
        self.assertEqual(answer.text, 'For to arrive unto the other side')
        self.assertEqual(answer.written_number, 12345)
        self.assertEqual(answer.date, date(2016, 9, 1))
        self.assertEqual(answer.pmg_api_url, 'http://api.pmg.org.za/example-question/5678/')
