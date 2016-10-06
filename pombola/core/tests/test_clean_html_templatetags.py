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
