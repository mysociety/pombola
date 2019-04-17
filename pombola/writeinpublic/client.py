import requests

from django.utils.dateparse import parse_datetime


class RecipientMixin(object):
    def parse_id(self, resource_uri):
        return resource_uri.split('#')[-1].split('-', 1)[-1]


class Message(RecipientMixin, object):
    def __init__(self, params, adapter):
        self.id = params['id']
        self.author_name = params['author_name']
        self.subject = params['subject']
        self.content = params['content']
        self.created_at = parse_datetime(params['created'])
        self._params = params
        self.adapter = adapter

    def people(self):
        return self.adapter.filter(ids=self._recipient_ids())

    def _recipient_ids(self):
        return [self.parse_id(p['resource_uri']) for p in self._params['people']]

    def answers(self):
        return [Answer(a, person=self.adapter.get(self.parse_id(a['person']['resource_uri']))) for a in self._params['answers']]


class Answer(RecipientMixin, object):
    def __init__(self, params, person):
        self.content = params['content']
        self.created_at = parse_datetime(params['created'])
        self.person = person


class WriteInPublic(object):
    class WriteInPublicException(Exception):
        pass

    def __init__(self, url, username, api_key, instance_id, person_uuid_prefix, adapter):
        self.url = url
        self.username = username
        self.api_key = api_key
        self.instance_id = instance_id
        self.person_uuid_prefix = person_uuid_prefix
        self.adapter = adapter

    def create_message(self, author_name, author_email, subject, content, persons):
        url = '{url}/api/v1/message/'.format(url=self.url)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
        }
        person_uris = [self.person_uuid_prefix.format(uuid) for uuid in persons]
        payload = {
            'author_name': author_name,
            'author_email': author_email,
            'subject': subject,
            'content': content,
            'writeitinstance': "/api/v1/instance/{}/".format(self.instance_id),
            'persons': person_uris,
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
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return Message(response.json(), adapter=self.adapter)
        except requests.exceptions.RequestException as err:
            raise self.WriteInPublicException(unicode(err))

    def get_messages(self, person_popolo_uri):
        url = '{url}/api/v1/instance/{instance_id}/messages/'.format(url=self.url, instance_id=self.instance_id)
        params = {
            'format': 'json',
            'username': self.username,
            'api_key': self.api_key,
            'person__popolo_uri': person_popolo_uri,
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            messages = response.json()['objects']
            return [Message(m, adapter=self.adapter) for m in messages]
        except requests.exceptions.RequestException as err:
            raise self.WriteInPublicException(unicode(err))
