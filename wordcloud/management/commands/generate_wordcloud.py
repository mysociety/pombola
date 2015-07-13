import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pombola.core.utils import mkdir_p
from wordcloud.wordcloud import popular_words


class Command(BaseCommand):
    """Generate json file for wordcloud.

    A single argument, a file path, can be passed in. This will be
    appended to the 'wordcloud_cache' directory in the media root to
    produce the location to store the json. If no argument is passed,
    it defaults to 'wordcloud.json'. If the file path is
    absolute it will just be used as is.
    """

    help = 'Generate wordcloud data'
    args = '<file>'

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError(
                "Usage: python manage.py generate_wordcloud [filepath]")

        wordcloud_dir = os.path.join(settings.MEDIA_ROOT, 'wordcloud_cache')
        mkdir_p(wordcloud_dir)
        leaf_name = args[0] if args else 'wordcloud.json'
        wordcloud_path = os.path.join(wordcloud_dir, leaf_name)

        with open(wordcloud_path, 'w') as cache_file:
            json.dump(popular_words(max_entries=30), cache_file)
