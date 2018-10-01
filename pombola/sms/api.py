import requests
from urllib import urlencode
from datetime import datetime


class APIMessage(object):
    def __init__(self, attrs):
        self.attrs = attrs

    def msisdn(self):
        return self.attrs.get('MSISDN', '')

    def message(self):
        return self.attrs.get('message', '')

    def time_in(self):
        time_str = self.attrs.get('time_in', '')
        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')


class APIClient(object):
    def __init__(self, base_url, short_code):
        self.base_url = base_url
        self.short_code = short_code

    # Get a list of the latest messages from the API.
    def latest_messages(self, limit=10):
        response = requests.get(
            self.api_url(limit=limit)
        )
        messages = response.json()['latest_messages']
        return [
            APIMessage(m[1])
            # Need to sort messages using dict key
            for m in sorted(messages.items(), key=lambda m: int(m[0]))
        ]

    def api_url(self, **kwargs):
        kwargs['short_code'] = self.short_code
        params = urlencode(kwargs)
        return "{base_url}?{params}".format(
            base_url=self.base_url,
            params=params
        )
