import requests_mock

from django.test import TestCase
from django.utils.dateparse import parse_datetime

from . import client


@requests_mock.Mocker()
class ClientTest(TestCase):
    def setUp(self):
        self.writeinpublic = client.WriteInPublic('https://example.com', 'test', '123', '42')

    def test_create_message(self, m):
        m.post('/api/v1/message/')
        self.writeinpublic.create_message(
            author_name='Alice',
            author_email='alice@example.org',
            subject='Test subject',
            content='Hello, testing.',
            persons='https://example.net/p.json#person-1',
        )
        expected_json = {
            'writeitinstance': '/api/v1/instance/42/',
            'author_email': 'alice@example.org',
            'author_name': 'Alice',
            'content': 'Hello, testing.',
            'persons': 'https://example.net/p.json#person-1',
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
        }
        m.get('/api/v1/message/1/', json=message_json)
        message = self.writeinpublic.get_message(1)
        self.assertEqual(message.id, '1')
        self.assertEqual(message.author_name, 'Alice')
        self.assertEqual(message.subject, 'Test message')
        self.assertEqual(message.content, 'Test content')
        self.assertEqual(message.created_at, parse_datetime(message_json['created']))

        # TODO: Add tests for message.people() and message.answers() methods

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
