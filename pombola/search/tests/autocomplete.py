import json
import re

from django.conf import settings
from django.test.client import Client
from django.utils import unittest
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.core.management import call_command

from pombola.core.models import PopoloPerson

class AutocompleteTest(unittest.TestCase):

    longMessage = True

    def setUp(self):

        # create a load of test people in the database
        names_and_hidden = [
            (u'Adam Ant', False),
            (u'Bobby Smith', False),
            (u'Fred Jones', False),
            (u'Joe Bloggs', False),
            (u'Joe Smith', False),
            (u'Josepth Smyth', True),
        ]
        for name, hidden in names_and_hidden:
            Person(
                slug=slugify(name),
                legal_name=name,
                gender='m',
                hidden=hidden,
            ).save()

        # Haystack indexes are not touched when fixtures are dumped. Run this
        # so that other changes cannot affect these tests. Have added a note to
        # a HayStack issue regarding this:
        #   https://github.com/toastdriven/django-haystack/issues/226
        call_command('rebuild_index', interactive=False, verbosity=0)


    def test_autocomplete_requests(self):
        c = Client()

        tests = {
            # input : expected names in response

            # test full first and partial last
            'bob':         [ 'Bobby Smith', ],
            'bob sm':      [ 'Bobby Smith', ],
            'bobby sm':    [ 'Bobby Smith', ],
            'bob smith':   [ 'Bobby Smith', ],
            'bobby smith': [ 'Bobby Smith', ],

            # full names
            'joe':   [ 'Joe Bloggs', 'Joe Smith' ],
            'jones': [ 'Fred Jones' ],

            # partial names
            'jo': [ 'Fred Jones', 'Joe Bloggs', 'Joe Smith' ],
            'sm': [ 'Bobby Smith', 'Joe Smith' ],

            # no matches
            'foo': [],
        }


        # The returned labels now include an image to indicate
        # the type of the object returned, so strip that out before
        # checking that the names match:
        def strip_leading_image(s):
            return re.sub(r'(?ims)^\s*<img [^>]*>\s*', '', s)

        autocomplete_url = reverse('autocomplete')

        for test_input, expected_output in tests.items():
            response = c.get( autocomplete_url, { 'term': test_input } )

            self.assertEqual( response.status_code, 200 )

            actual_output = json.loads( response.content )
            actual_names = [ strip_leading_image(i['label'])
                             for i in actual_output ]

            self.assertEqual(
                set(actual_names),
                set(expected_output),
                msg="\n\nTesting input: '%s'" % test_input
            )
