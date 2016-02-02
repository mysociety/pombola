import json
from mock import patch
import re
import urllib
import urlparse

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from django_date_extensions.fields import ApproximateDate

from pombola.experiments.models import Event, Experiment
from pombola.feedback.models import Feedback
from pombola.core.models import (
    Person,
    Place,
    PlaceKind,
    Position,
    PositionTitle,
    Organisation,
    OrganisationKind,
    )
from pombola.kenya.views import KEPersonDetail

from .views import EXPERIMENT_DATA, CountyPerformanceView


from django_webtest import WebTest

from nose.plugins.attrib import attr

@attr(country='kenya')
class CountyPerformancePageTests(WebTest):

    def setUp(self):
        experiment_slug = 'mit-county-larger'
        self.data = EXPERIMENT_DATA[experiment_slug]
        self.url = '/' + self.data['base_view_name']
        self.sid = self.data['qualtrics_sid']
        self.experiment = Experiment.objects.create(
            slug=experiment_slug,
            name='MIT County Performance experiment')

    def tearDown(self):
        self.experiment.delete()
        Feedback.objects.all().delete()

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'n')
    def test_page_view(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.html.get('a', {'id': 'share-facebook'}))
        self.assertTrue(response.html.get('a', {'id': 'share-twitter'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'surveyPromoBanner'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 't')
    def test_threat_variant(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'threat'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'social-context'}))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'o')
    def test_opportunity_variant(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'opportunity'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'social-context'}))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'n')
    def test_neither_variant(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'social-context'}))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'ts')
    def test_threat_variant_with_social_context(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'threat'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'social-context'})))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'os')
    def test_opportunity_variant_with_social_context(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'opportunity'})))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'social-context'})))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'ns')
    def test_neither_variant_with_social_context(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.html.findAll('div', {'id': 'opportunity'}))
        self.assertFalse(
            response.html.findAll('div', {'id': 'threat'}))
        self.assertEqual(
            1, len(response.html.findAll('div', {'id': 'social-context'})))

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'o')
    def test_petition_submission(self):
        Event.objects.all().delete()
        response = self.app.get(self.url + '?g=f&agroup=over')
        event = Event.objects.get(
            variant='o',
            category='page',
            action='view',
            label=self.data['pageview_label'])
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

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 't')
    def test_senate_submission(self):
        Event.objects.all().delete()
        test_comment = "Some comment to submit"
        response = self.app.get(self.url + '?g=m&agroup=over')
        event = Event.objects.get(
            variant='t',
            category='page',
            action='view',
            label=self.data['pageview_label'])
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

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'n')
    def test_survey_link(self):
        Event.objects.all().delete()
        response = self.app.get(self.url + '?g=f&agroup=under')
        event = Event.objects.get(
            variant='n',
            category='page',
            action='view',
            label=self.data['pageview_label'])
        user_key = re.search(r'^\d+$', event.user_key).group()
        extra_data = json.loads(event.extra_data)
        self.assertEqual('f', extra_data['g'])
        self.assertEqual('under', extra_data['agroup'])
        survey_url = response.html.find('a', {'id': 'take-survey'})['href']
        parsed_url = urlparse.urlparse(survey_url)
        self.assertEqual(parsed_url.path,
                         reverse(self.data['base_view_name'] + '-survey'))
        # Follow that link, but don't follow the redirect:
        response = self.app.get(survey_url)
        self.assertEqual(response.status_code, 302)
        redirect_url = response.location
        parsed_redirect_url = urlparse.urlparse(redirect_url)
        self.assertEqual(parsed_redirect_url.netloc, 'survey.az1.qualtrics.com')
        self.assertEqual(parsed_redirect_url.path, '/SE/')
        parsed_redirect_qs = urlparse.parse_qs(parsed_redirect_url.query)
        self.assertEqual(parsed_redirect_qs['SID'], [self.sid])
        self.assertEqual(parsed_redirect_qs['user_key'], [user_key])
        self.assertEqual(parsed_redirect_qs['variant'], ['n'])

    @patch.object(CountyPerformanceView, 'get_random_variant', lambda self, local_random: 'n')
    def test_share_link(self):
        Event.objects.all().delete()
        response = self.app.get(self.url + '?g=f&agroup=over')
        event = Event.objects.get(
            variant='n',
            category='page',
            action='view',
            label=self.data['pageview_label'])
        user_key = re.search(r'^\d+$', event.user_key).group()
        extra_data = json.loads(event.extra_data)
        self.assertEqual('f', extra_data['g'])
        self.assertEqual('over', extra_data['agroup'])
        # Try the Facebook link first:
        share_url = response.html.find('a', {'id': 'share-facebook'})['href']
        parsed_url = urlparse.urlparse(share_url)
        self.assertEqual(parsed_url.path,
                         reverse(self.data['base_view_name'] + '-share'))
        self.assertEqual(parsed_url.query,
                         'n=facebook')
        # Now follow that link to find the redirect:
        response = self.app.get(share_url)
        self.assertEqual(response.status_code, 302)
        redirect_url = response.location
        parsed_redirect_url = urlparse.urlparse(redirect_url)
        self.assertEqual(parsed_redirect_url.netloc, 'www.facebook.com')
        self.assertEqual(parsed_redirect_url.path, '/sharer/sharer.php')
        parsed_redirect_qs = urlparse.parse_qs(parsed_redirect_url.query)

        facebook_url = urllib.unquote(parsed_redirect_qs['u'][0])
        parsed_facebook_url = urlparse.urlparse(facebook_url)
        self.assertEqual(parsed_facebook_url.path, self.url)
        self.assertTrue(re.search(r'^via=[a-f0-9]+$', parsed_facebook_url.query))


@attr(country='kenya')
class PersonDetailPageTest(TestCase):
    """The membership data we have has a tendency to gradually move
    away from the ideal of the only positions associated with NA
    constituencies being being those linking assembly members with their
    constituencies.

    While we work out how to keep the data tidier, we're going to handle
    this problem by only displaying the memberships we actually want to
    see.
    """
    def setUp(self):
        county_kind = PlaceKind.objects.create(name='County', slug='county')
        constituency_kind = PlaceKind.objects.create(name='Constituency', slug='constituency')

        self.county = Place.objects.create(kind=county_kind, name='Test County', slug='test-county')
        self.constituency = Place.objects.create(kind=constituency_kind, name='Test Constituency', slug='test-constituency')
        self.constituency2 = Place.objects.create(kind=constituency_kind, name='Test Constituency2', slug='test-constituency2')

        self.na_member_title = PositionTitle.objects.create(name='NA Member', slug='member-national-assembly')
        self.senator_title = PositionTitle.objects.create(name='Senator', slug='senator')
        self.party_member_title = PositionTitle.objects.create(name='Party Member', slug='party-member')

        self.governmental = OrganisationKind.objects.create(name='Governmental', slug='governmental')
        self.party_orgkind = OrganisationKind.objects.create(name='Political Party', slug='party')

        self.na = Organisation.objects.create(kind=self.governmental, name='National Assembly', slug='national-assembly')
        self.senate = Organisation.objects.create(kind=self.governmental, name='Senate', slug='senate')

        self.party = Organisation.objects.create(kind=self.party_orgkind, name='Test Party', slug='test-party')

        self.person = Person.objects.create(legal_name='Test Person', slug='test-person')

    def test_mp_with_county(self):
        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency,
            organisation=self.na,
            title=self.na_member_title,
            )

        Position.objects.create(
            category='political',
            person=self.person,
            place=self.county,
            )

        request = RequestFactory().get('/person/test-person/')
        request.user = AnonymousUser()
        response = KEPersonDetail.as_view()(request, slug='test-person')

        self.assertEqual(len(response.context_data['constituencies']), 1)
        self.assertEqual(response.context_data['constituencies'][0], self.constituency)

    def test_mp_with_party_membership_linked_to_constituency(self):
        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency,
            organisation=self.na,
            title=self.na_member_title,
            )

        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency,
            organisation=self.party,
            title=self.party_member_title,
            )

        request = RequestFactory().get('/person/test-person/')
        request.user = AnonymousUser()
        response = KEPersonDetail.as_view()(request, slug='test-person')

        self.assertEqual(len(response.context_data['constituencies']), 1)
        self.assertEqual(response.context_data['constituencies'][0], self.constituency)

    def test_senator_with_party_membership_linked_to_constituency(self):
        Position.objects.create(
            category='political',
            person=self.person,
            place=self.county,
            organisation=self.senate,
            title=self.senator_title,
            )

        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency,
            organisation=self.party,
            title=self.party_member_title,
            )

        request = RequestFactory().get('/person/test-person/')
        request.user = AnonymousUser()
        response = KEPersonDetail.as_view()(request, slug='test-person')

        self.assertEqual(len(response.context_data['constituencies']), 1)
        self.assertEqual(response.context_data['constituencies'][0], self.county)

    def test_mp_with_two_constituencies(self):
        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency,
            organisation=self.na,
            title=self.na_member_title,
            start_date=ApproximateDate(2015, 1, 1),
            )

        Position.objects.create(
            category='political',
            person=self.person,
            place=self.constituency2,
            organisation=self.na,
            title=self.na_member_title,
            start_date=ApproximateDate(2015, 1, 2),
            )

        request = RequestFactory().get('/person/test-person/')
        request.user = AnonymousUser()
        response = KEPersonDetail.as_view()(request, slug='test-person')

        self.assertEqual(len(response.context_data['constituencies']), 1)
        self.assertEqual(response.context_data['constituencies'][0], self.constituency2)

        # Check that admins got mailed.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            '[Django] ERROR: test-person - Too many NA memberships (2)',
            )
