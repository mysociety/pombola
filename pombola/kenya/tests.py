import json
import re

from django.core.urlresolvers import reverse

from pombola.experiments.models import Event, Experiment
from pombola.feedback.models import Feedback

from django_webtest import WebTest

from nose.plugins.attrib import attr

@attr(country='kenya')
class CountyPerformancePageTests(WebTest):

    def setUp(self):
        self.experiment = Experiment.objects.create(
            slug='mit-county',
            name='MIT County Performance experiment')

    def tearDown(self):
        self.experiment.delete()
        Feedback.objects.all().delete()

    def test_page_view(self):
        response = self.app.get('/county-performance')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.html.get('a', {'id': 'share-facebook'}))
        self.assertTrue(response.html.get('a', {'id': 'share-twitter'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'surveyPromoBanner'}))

    def test_threat_variant(self):
        response = self.app.get('/county-performance?variant=t')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'threat'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))

    def test_threat_opportunity(self):
        response = self.app.get('/county-performance?variant=o')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'opportunity'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))

    def test_threat_neither(self):
        response = self.app.get('/county-performance?variant=n')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))

    def test_petition_submission(self):
        Event.objects.all().delete()
        response = self.app.get('/county-performance?variant=o&g=f&agroup=over&utm_expid=1234')
        event = Event.objects.get(
            variant='o',
            category='page',
            action='view',
            label='county-performance')
        user_key = re.search(r'^\d+$', event.user_key).group()
        extra_data = json.loads(event.extra_data)
        self.assertEqual('f', extra_data['g'])
        self.assertEqual('over', extra_data['agroup'])
        form = response.forms.get('petition')
        form['name'] = 'Joe Bloggs'
        form['email'] = 'hello@example.org'
        form.submit()
        self.assertEqual(
            Feedback.objects.filter(
               status='non-actionable',
                email='hello@example.org',
                comment__contains='Joe Bloggs').count(),
            1)
        event = Event.objects.get(
            variant='o',
            category='form',
            action='submit',
            label='petition')
        self.assertEqual(user_key, event.user_key)
        extra_data = json.loads(event.extra_data)
        self.assertEqual('f', extra_data['g'])

    def test_senate_submission(self):
        Event.objects.all().delete()
        test_comment = "Some comment to submit"
        response = self.app.get('/county-performance?variant=t&g=m&agroup=over&utm_expid=1234')
        event = Event.objects.get(
            variant='t',
            category='page',
            action='view',
            label='county-performance')
        user_key = re.search(r'^\d+$', event.user_key).group()
        extra_data = json.loads(event.extra_data)
        self.assertEqual('m', extra_data['g'])
        self.assertEqual('over', extra_data['agroup'])
        form = response.forms.get('senate')
        form['comments'] = test_comment
        form.submit()
        self.assertEqual(
            Feedback.objects.filter(
               status='non-actionable',
                comment__contains=test_comment).count(),
            1)
        event = Event.objects.get(
            variant='t',
            category='form',
            action='submit',
            label='senate')
        self.assertEqual(user_key, event.user_key)
        extra_data = json.loads(event.extra_data)
        self.assertEqual('m', extra_data['g'])
