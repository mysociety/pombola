import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pombola.core.utils import mkdir_p
from wordcloud.wordcloud import popular_words


class Command(BaseCommand):
    """Generate json file for wordcloud.

    A single argument, a file path, can be passed in. This will
    be appended to settings.WORDCLOUD_CACHE_DIR to produce the location
    to store the json. If no argument is passed, it defaults to
    'wordcloud.json'. If the file path is absolute it will just be used
    as is.
    """

    help = 'Generate wordcloud data'
    args = '<file>'

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError(
                "Usage: python manage.py generate_wordcloud [filepath]")

        cache_dir = settings.WORDCLOUD_CACHE_DIR
        mkdir_p(cache_dir)

        cache_path = os.path.join(cache_dir, args[0]) if args else settings.WORDCLOUD_CACHE_PATH

        with open(cache_path, 'w') as cache_file:
            json.dump(popular_words(max_entries=30), cache_file)
