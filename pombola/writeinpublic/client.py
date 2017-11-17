import requests


class WriteInPublic(object):
    def __init__(self, url, username, api_key):
        self.url = url
        self.username = username
        self.api_key = api_key

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
        return requests.get(url, params=params)
