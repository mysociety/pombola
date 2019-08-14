from datetime import datetime

import requests_mock
from nose.plugins.attrib import attr
from mock import Mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from django.forms import ModelMultipleChoiceField, ModelChoiceField

from pombola.core.models import Person, Organisation, OrganisationKind, ContactKind

from . import client
from .models import Configuration
from .views import PersonAdapter, CommitteeAdapter
from .forms import RecipientForm


@requests_mock.Mocker()
class ClientTest(TestCase):
    def setUp(self):
        self.adapter_mock = Mock()
        self.writeinpublic = client.WriteInPublic(
            'https://example.com',
            'test',
            '123',
            '42',
            'https://example.net/p.json#person-{}',
            adapter=self.adapter_mock
        )

    def test_create_message(self, m):
        m.post('/api/v1/message/')
        self.writeinpublic.create_message(
            author_name='Alice',
            author_email='alice@example.org',
            subject='Test subject',
            content='Hello, testing.',
            persons=['1'],
        )
        expected_json = {
            'writeitinstance': '/api/v1/instance/42/',
            'author_email': 'alice@example.org',
            'author_name': 'Alice',
            'content': 'Hello, testing.',
            'persons': ['https://example.net/p.json#person-1'],
            'subject': 'Test subject',
        }
        expected_url = 'https://example.com/api/v1/message/?username=test&api_key=123&format=json'
        last_request = m._adapter.last_request
        self.assertEqual(last_request.json(), expected_json)
        self.assertEqual(last_request.url, expected_url)

    def test_get_message(self, m):
        message_json = {
            'id': '1',
            'author_name': 'Alice',
            'subject': 'Test message',
            'content': 'Test content',
            'created': '2017-11-14T04:01:05.799658',
            'people': [
                {
                    'resource_uri': 'http://example.com/popolo.json#person-123',
                }
            ],
            'answers': [
                {
                    'content': 'Test',
                    'created': '2017-12-01T10:27:30.825490',
                    'person': {
                        'resource_uri': 'http://example.com/popolo.json#person-456',
                    },
                },
            ],
        }
        m.get('/api/v1/message/1/', json=message_json)
        message = self.writeinpublic.get_message(1)
        self.assertEqual(message.id, '1')
        self.assertEqual(message.author_name, 'Alice')
        self.assertEqual(message.subject, 'Test message')
        self.assertEqual(message.content, 'Test content')
        self.assertEqual(message.created_at, parse_datetime(message_json['created']))

        message.people()
        self.adapter_mock.filter.assert_called_once_with(ids=['123'])

        answers = message.answers()
        self.adapter_mock.get.assert_called_once_with('456')
        answer = answers[0]
        self.assertEqual('Test', answer.content)
        self.assertEqual(datetime(2017, 12, 1, 10, 27, 30, 825490), answer.created_at)


    def test_get_messages(self, m):
        messages_json = {
            'objects': [
                {
                    'id': '1',
                    'author_name': 'Alice',
                    'subject': 'Test message',
                    'content': 'Test content',
                    'created': '2017-11-14T04:01:05.799658',
                },
                {
                    'id': '2',
                    'author_name': 'Bob',
                    'subject': 'Another test message',
                    'content': 'More test content',
                    'created': '2017-11-15T05:05:04.345258',
                },
            ],
        }
        m.get('/api/v1/instance/42/messages/', json=messages_json)
        popolo_uri = 'https://example.net/p.json#person-1'
        messages = self.writeinpublic.get_messages(popolo_uri)
        last_request = m._adapter.last_request
        expected_qs = {
            'username': ['test'],
            'api_key': ['123'],
            'format': ['json'],
            'person__popolo_uri': [popolo_uri],
        }
        self.assertEqual(last_request.qs, expected_qs)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subject, 'Test message')
        self.assertEqual(messages[1].subject, 'Another test message')


@attr(country='south_africa')
@requests_mock.Mocker()
class WriteInPublicNewMessageViewTest(TestCase):
    def test_sending_message_wizard_steps(self, m):
        # Mock the POST response
        m.post('/api/v1/message/', json={
            'id': '42'
        })
        configuration = Configuration.objects.create(
            url='http://example.com',
            username='admin',
            api_key='test',
            instance_id='1',
            slug='south-africa-assembly'
        )
        person = Person.objects.create()
        parliament = OrganisationKind.objects.create(slug='parliament', name='Parliament')
        na = Organisation.objects.create(slug='national-assembly', name='National Assembly', kind=parliament)
        person.position_set.create(organisation=na)
        ck_email, _ = ContactKind.objects.get_or_create(slug='email', name='Email')
        person.contacts.create(kind=ck_email, value='test@example.com', preferred=True)
        response = self.client.get(reverse('writeinpublic:writeinpublic-new-message'))
        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'recipients'}))

        # GET the recipients step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the recipients step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'recipients'}), {
            'write_in_public_new_message-current_step': 'recipients',
            'recipients-persons': person.id,
        })

        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'draft'}))

        # GET the draft step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the draft step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'draft'}), {
            'write_in_public_new_message-current_step': 'draft',
            'draft-subject': 'Test',
            'draft-content': 'Test',
            'draft-author_name': 'Test',
            'draft-author_email': 'test@example.com',
        })
        self.assertRedirects(response, reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'preview'}))

        # GET the preview step
        response = self.client.get(response.url)
        self.assertEquals(response.status_code, 200)

        # POST to the preview step
        response = self.client.post(reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'preview'}), {
            'write_in_public_new_message-current_step': 'preview',
        })
        self.assertRedirects(
            response,
            reverse('writeinpublic:writeinpublic-new-message-step', kwargs={'step': 'done'}),
            fetch_redirect_response=False
        )

        # GET the done step
        response = self.client.get(response.url)

        # Check that we're redirected to the pending message page
        self.assertRedirects(
            response,
            reverse('writeinpublic:writeinpublic-pending'),
            fetch_redirect_response=False
        )


@attr(country='south_africa')
@requests_mock.Mocker()
class WriteToCommitteeMessagesViewTest(TestCase):
    def setUp(self):
        Configuration.objects.create(
            url='http://example.com',
            username='admin',
            api_key='test',
            instance_id='1',
            slug='south-africa-committees',
            person_uuid_prefix='http://example.org/popolo.json#person-{}'
        )
        kind = OrganisationKind.objects.create(name='National Assembly Committee', slug='national-assembly-committee')
        self.committee = Organisation.objects.create(slug='test-committee', kind=kind)

    def test_committee_that_exists_in_writeinpublic(self, m):
        m.get(
            '/api/v1/instance/1/messages/'.format(self.committee.id),
            json={'objects': []}
        )
        response = self.client.get(reverse('organisation_messages', kwargs={'slug': self.committee.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['messages'], [])

    def test_committee_that_doesnt_exist_in_writeinpublic(self, m):
        m.get(
            '/api/v1/instance/1/messages/'.format(self.committee.id),
            status_code=404
        )
        response = self.client.get(reverse('organisation_messages', kwargs={'slug': self.committee.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['messages'], [])



class PersonAdapterTest(TestCase):
    def test_get(self):
        adapter = PersonAdapter()
        person = Person.objects.create()
        self.assertEqual(adapter.get(person.id), person)


class CommitteeAdapterTest(TestCase):
    def test_get_form_initial(self):
        adapter = CommitteeAdapter()

        self.assertEqual(adapter.get_form_initial(step='draft', cleaned_data={}), {})
        self.assertEqual(adapter.get_form_initial(step='draft', cleaned_data={'recipients': None}), {})

        mock_committee = Mock()
        mock_committee.name = 'Test Name'
        self.assertEqual(
            adapter.get_form_initial(
                step='draft',
                cleaned_data={'recipients': {'persons': mock_committee}}
            ),
            {'content': 'Dear Test Name,\n\n'}
        )

    def test_get_form_kwargs_when_committee_has_multiple_emails(self):
        adapter = CommitteeAdapter()

        na_committee_kind = OrganisationKind.objects.create(name='National Assembly Committees', slug='national-assembly-committees')
        email_kind = ContactKind.objects.create(name='Email', slug='email')
        committee = Organisation.objects.create(kind=na_committee_kind)
        committee.contacts.create(kind=email_kind, value='test@example.org', preferred=False)
        committee.contacts.create(kind=email_kind, value='test@example.com', preferred=False)

        form_kwargs = adapter.get_form_kwargs('recipients')
        self.assertEqual(len(form_kwargs['queryset']), 1)
        self.assertEqual(form_kwargs['queryset'][0], committee)


class RecipientFormTest(TestCase):
    def setUp(self):
        self.people = Person.objects.all()

    def test_defaults_to_multiple_choice(self):
        form = RecipientForm(queryset=self.people)
        self.assertEqual(ModelMultipleChoiceField, form.fields['persons'].__class__)
        self.assertEqual(self.people, form.fields['persons'].queryset)

    def test_multiple_choice_kwarg(self):
        form = RecipientForm(queryset=self.people, multiple=False)
        self.assertEqual(ModelChoiceField, form.fields['persons'].__class__)
        self.assertEqual(self.people, form.fields['persons'].queryset)
