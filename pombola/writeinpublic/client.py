import requests

from django.utils.dateparse import parse_datetime

from pombola.core.models import Person


class PersonMixin(object):
    def parse_everypolitician_uuid(self, resource_uri):
        return resource_uri.split('#')[-1].split('-', 1)[-1]


class Message(PersonMixin, object):
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
        return [self.parse_everypolitician_uuid(p['resource_uri']) for p in self._params['people']]

    def answers(self):
        return [Answer(a) for a in self._params['answers']]


class Answer(PersonMixin, object):
    def __init__(self, params):
        self.content = params['content']
        self.created_at = parse_datetime(params['created'])
        self.person = Person.objects.get(
            identifiers__scheme='everypolitician',
            identifiers__identifier=self.parse_everypolitician_uuid(params['person']['resource_uri']),
        )


class WriteInPublic(object):
    class WriteInPublicException(Exception):
        pass

    def __init__(self, url, username, api_key, instance_id):
        self.url = url
        self.username = username
        self.api_key = api_key
        self.instance_id = instance_id

    def create_message(self, author_name, author_email, subject, content, persons):
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
            'writeitinstance': "/api/v1/instance/{}/".format(self.instance_id),
            'persons': persons,
        }
        try:
            response = requests.post(url, json=payload, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as err:
            raise self.WriteInPublicException(unicode(err))

    def get_message(self, message_id):
        url = '{url}/api/v1/message/{message_id}/'.format(url=self.url, message_id=message_id)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return Message(response.json())

    def get_messages(self, person_popolo_uri):
        url = '{url}/api/v1/instance/{instance_id}/messages/'.format(url=self.url, instance_id=self.instance_id)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
            'person__popolo_uri': person_popolo_uri,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        messages = response.json()['objects']
        return [Message(m) for m in messages]
