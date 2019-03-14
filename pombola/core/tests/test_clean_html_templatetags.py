from django.template import Context, Template
from django.test import TestCase


class CleanHTMLTest(TestCase):

    def test_plain_text_works(self):
        template = Template(
            '{% load clean_html %}{{ answer_text|as_clean_html|safe }}')
        self.assertEqual(
            template.render(
                Context({'answer_text': 'Mary had a little lamb'})),
            '<p>Mary had a little lamb</p>')

    def test_script_removed(self):
        template = Template(
            '{% load clean_html %}{{ answer_text|as_clean_html|safe }}')
        self.assertEqual(
            template.render(
                Context({
                    'answer_text':
                    'Hello and <script>alert("Bad!");</script> goodbye'
                })),
            '<p>Hello and  goodbye</p>')

    def test_empty_string_should_not_error(self):
        template = Template(
            '{% load clean_html %}{{ answer_text|as_clean_html|safe }}')
        self.assertEqual(
            template.render(Context({'answer_text': ''})),
            '<p></p>')

    def test_all_whitespace_string_should_not_error(self):
        template = Template(
            '{% load clean_html %}{{ answer_text|as_clean_html|safe }}')
        self.assertEqual(
            template.render(Context({'answer_text': '  '})),
            '<p></p>')

    def test_string_with_all_closing_tags_should_not_error(self):
        template = Template(
            '{% load clean_html %}{{ answer_text|as_clean_html|safe }}')
        self.assertEqual(
            template.render(Context({'answer_text': '</strong></a></p>'})),
            '<p></p>')
