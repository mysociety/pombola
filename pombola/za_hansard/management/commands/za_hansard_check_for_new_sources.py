import re
import datetime

import requests
from optparse import make_option
from bs4 import BeautifulSoup

from django.conf import settings


from django.core.management.base import BaseCommand, CommandError

from za_hansard.models import Source

HTTPLIB2_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/601.4.4 (KHTML, like Gecko) Version/9.0.3 Safari/601.4.4'
}

class FailedToRetrieveSourceException (Exception):
    pass

class Command(BaseCommand):
    help = 'Check for new sources'
    option_list = BaseCommand.option_list + (
        make_option('--historical-limit',
            default='2009-04-22',
            type='str',
            help='Limit earliest historical entry to check (in yyyy-mm-dd format, default 2009-04-22)',
        ),
        make_option('--delete-existing',
            default=False,
            action='store_true',
            help='Delete existing sources (implies --check-all)',
        ),
    )

    def handle(self, *args, **options):
        self.verbose = int(options['verbosity']) > 1
        historical_limit = options['historical_limit']

        if options['delete_existing']:
            Source.objects.all().delete()

        sources = []
        new_sources = []
        start_offset = 0
        while True:
            new_sources = self.retrieve_sources(start_offset, options)
            sources += new_sources
            start_offset = len(sources)
            if len(new_sources) == 0:
                break

        sources = [s for s in sources if s['defaults']['date'] >= historical_limit]
        sources.reverse()
        sources_db = [Source.objects.get_or_create(**source) for source in sources]
        if self.verbose:
            sources_count = len(sources)
            created_count = sum([1 for (_,created) in sources_db if created])
            self.stdout.write('Sources found: %d\nSources created: %d\n' % (
                sources_count, created_count))

    def retrieve_sources(self, start, options):
        url = 'https://www.parliament.gov.za/docsjson?queries%5Btype%5D=hansard&sorts%5Bdate%5D=-1&perPage=1000&offset={}'.format((start or 0))

        if self.verbose:
            self.stdout.write("Retrieving %s\n" % url)
        response = requests.get(url)
        response.raise_for_status()

        records = response.json()['records']
        return [
            {
                'document_name': r['name'],
                'document_number': r['id'],
                'defaults':
                {
                    'url': r['file_location'],
                    'title': r['type'],
                    'language': r['language'] or 'English',
                    'house': r['house'],
                    'date': r['date'],
                }
            }
            for r in records
        ]
