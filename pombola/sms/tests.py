# coding=utf-8
from django.test import TestCase
from .api import APIClient
import requests_mock
from datetime import datetime, timedelta


class APIClientTest(TestCase):
    def setUp(self):
        now = datetime.now()
        self.tomorrow = (now + timedelta(days=1)).date()
        self.one_week_ago = (now - timedelta(weeks=1)).date()
        self.client = APIClient(
            base_url='http://example.org/sms',
            api_key='123'
        )

    def test_api_url_with_defaults(self):
        self.assertEqual(
            self.client.api_url(),
            'http://example.org/sms?api_key=123&start_date={}&end_date={}'.format(
                self.one_week_ago,
                self.tomorrow
            )
        )

    def test_api_url_with_start_date_specified(self):
        self.assertEqual(
            self.client.api_url(start_date='2019-01-01'),
            'http://example.org/sms?api_key=123&start_date=2019-01-01&end_date={}'.format(self.tomorrow)
        )

    def test_api_url_with_end_date_specified(self):
        self.assertEqual(
            self.client.api_url(end_date='2019-03-15'),
            'http://example.org/sms?api_key=123&start_date={}&end_date=2019-03-15'.format(self.one_week_ago)
        )

    def test_api_url_with_start_and_end_date_specified(self):
        self.assertEqual(
            self.client.api_url(start_date='2019-01-01', end_date='2019-03-15'),
            'http://example.org/sms?api_key=123&start_date=2019-01-01&end_date=2019-03-15'
        )

    def test_get_messages(self):
        with requests_mock.Mocker() as m:
            m.get(
                self.client.api_url(),
                json={
                    'fetched_messages': [
                        {
                            'id': 1,
                            'msisdn': '0987654321',
                            'message': 'Hello!',
                            'date': '2018-09-30 19:48:19',
                            'short_code': '123',
                        },
                        {
                            'id': 2,
                            'msisdn': '0987654323',
                            'message': 'This is a multi-word test',
                            'date': '2018-09-30 17:23:34',
                            'short_code': '123',
                        }
                    ]
                }
            )
            messages = self.client.get_messages()
            self.assertEqual(len(messages), 2)

            message1 = messages[0]
            self.assertEqual(message1.msisdn, '0987654321')
            self.assertEqual(message1.message, 'Hello!')
            self.assertEqual(
                message1.datetime,
                datetime(2018, 9, 30, 19, 48, 19)
            )

            message2 = messages[1]
            self.assertEqual(message2.msisdn, '0987654323')
            self.assertEqual(message2.message, 'This is a multi-word test')
            self.assertEqual(
                message2.datetime,
                datetime(2018, 9, 30, 17, 23, 34)
            )
