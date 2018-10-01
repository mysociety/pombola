from django.test import TestCase
from .api import APIClient
import requests_mock
from datetime import datetime


class APIClientTest(TestCase):
    def setUp(self):
        self.client = APIClient(
            base_url='http://example.org/sms',
            short_code='123'
        )

    def test_api_url(self):
        self.assertEqual(
            self.client.api_url(limit=42),
            'http://example.org/sms?short_code=123&limit=42'
        )

    def test_latest_messages(self):
        with requests_mock.Mocker() as m:
            m.get(
                self.client.api_url(limit=3),
                json={
                    'latest_messages': {
                        '1': {
                            'MSISDN': '0987654321',
                            'message': 'Hello!',
                            'time_in': '2018-09-30 19:48:19',
                            'short_code': '123',
                        },
                        '2': {
                            'MSISDN': '0987654322',
                            'message': 'Testing',
                            'time_in': '2018-09-30 18:35:03',
                            'short_code': '123',
                        },
                        '3': {
                            'MSISDN': '0987654323',
                            'message': 'This is a multi-word test',
                            'time_in': '2018-09-30 17:23:34',
                            'short_code': '123',
                        }
                    }
                }
            )
            messages = self.client.latest_messages(limit=3)
            self.assertEqual(len(messages), 3)

            message1 = messages[0]
            self.assertEqual(message1.msisdn(), '0987654321')
            self.assertEqual(message1.message(), 'Hello!')
            self.assertEqual(
                message1.time_in(),
                datetime(2018, 9, 30, 19, 48, 19)
            )

            message2 = messages[1]
            self.assertEqual(message2.msisdn(), '0987654322')
            self.assertEqual(message2.message(), 'Testing')
            self.assertEqual(
                message2.time_in(),
                datetime(2018, 9, 30, 18, 35, 3)
            )

            message3 = messages[2]
            self.assertEqual(message3.msisdn(), '0987654323')
            self.assertEqual(message3.message(), 'This is a multi-word test')
            self.assertEqual(
                message3.time_in(),
                datetime(2018, 9, 30, 17, 23, 34)
            )
