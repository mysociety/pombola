import requests

from django.core.management.base import BaseCommand

from pombola.za_hansard.models import Source


class Command(BaseCommand):
    help = 'Check for new sources from the PMG API'

    def add_arguments(self, parser):
        parser.add_argument('--delete-existing', action='store_true', default=False, help='Delete all existing sources')

    def handle(self, *args, **options):
        if options['delete_existing']:
            Source.objects.all().delete()

        hansard_url = 'https://api.pmg.org.za/hansard/'
        while True:
            if options['verbosity'] > 1:
                self.stdout.write(u"Fetching {}\n".format(hansard_url))
            response = requests.get(hansard_url)
            response.raise_for_status()
            response_json = response.json()
            hansards = response_json['results']
            urls = [h['url'] for h in hansards]
            for url in urls:
                if options['verbosity'] > 1:
                    self.stdout.write(u"Fetching {}\n".format(url))
                response = requests.get(url)
                response.raise_for_status()
                hansard = response.json()
                if not hansard.get('files', []):
                    continue
                attached_file = hansard['files'][0]
                title = attached_file['title'] or ''
                db_source, created = Source.objects.get_or_create(**{
                    'document_name': title[:200],
                    'document_number': str(attached_file['id']),
                    'defaults':
                    {
                        'url': attached_file['url'],
                        'title': hansard['type'],
                        'language': 'English',
                        'house': hansard['house']['name_short'],
                        'date': hansard['date'].split('T')[0],
                    }
                })
                if options['verbosity'] > 1:
                    if created:
                        self.stdout.write(u"Created one new source: {}\n".format(db_source))
                    else:
                        self.stdout.write(u"Existing source found: {}\n".format(db_source))
            if not response_json['next']:
                break
            hansard_url = response_json['next']

