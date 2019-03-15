import requests
from urllib import urlencode
from datetime import datetime, timedelta


class APIMessage(object):
    def __init__(self, attrs):
        self.attrs = attrs

    @property
    def msisdn(self):
        return self.attrs.get('msisdn', '')

    @property
    def message(self):
        return self.attrs.get('message', '')

    @property
    def datetime(self):
        time_str = self.attrs.get('date', '')
        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')


class APIClient(object):
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    # Get a list of the latest messages from the API.
    def get_messages(self, **kwargs):
        response = requests.get(
            self.api_url(**kwargs)
        )
        messages = response.json()['fetched_messages']
        return [APIMessage(m) for m in messages]

    def api_url(self, **kwargs):
        kwargs['api_key'] = self.api_key
        # Default start date to one week ago
        kwargs['start_date'] = kwargs.get('start_date') or (datetime.now() - timedelta(weeks=1)).date()
        # Default end date to tomorrow
        kwargs['end_date'] = kwargs.get('end_date') or (datetime.now() + timedelta(days=1)).date()

        params = urlencode(kwargs)
        return "{base_url}?{params}".format(
            base_url=self.base_url,
            params=params
        )
