import requests

from django.utils.dateparse import parse_datetime

from pombola.core.models import Person


class Message(object):
    def __init__(self, params):
        self.id = params['id']
        self.author_name = params['author_name']
        self.subject = params['subject']
        self.content = params['content']
        self.created_at = parse_datetime(params['created'])
        self._params = params

    def people(self):
        return Person.objects.filter(
            identifiers__scheme='everypolitician',
            identifiers__identifier__in=self._recipient_ids(),
        )

    def _recipient_ids(self):
        return [p['resource_uri'].split('#')[-1].split('-', 1)[-1] for p in self._params['people']]


class WriteInPublic(object):
    def __init__(self, url, username, api_key, instance_id):
        self.url = url
        self.username = username
        self.api_key = api_key
        self.instance_id = instance_id

    def create_message(self, author_name, author_email, subject, content, writeitinstance, persons):
        url = '{url}/api/v1/message/'.format(url=self.url)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
        }
        payload = {
            'author_name': author_name,
            'author_email': author_email,
            'subject': subject,
            'content': content,
            'writeitinstance': writeitinstance,
            'persons': persons,
        }
        return requests.post(url, json=payload, params=params)

    def get_message(self, message_id):
        url = '{url}/api/v1/message/{message_id}/'.format(url=self.url, message_id=message_id)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
        }
        r = requests.get(url, params=params)
        return Message(r.json())

    def get_messages(self, person_id):
        url = '{url}/api/v1/instance/{instance_id}/messages/'.format(url=self.url, instance_id=self.instance_id)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
            'person__popolo_id': person_id,
        }
        response = requests.get(url, params=params)
        messages = response.json()['objects']
        return [Message(m) for m in messages]
