import errno
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils import simplejson
from django.conf import settings

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
        try:
            os.mkdir(cache_dir)
        except OSError as exc:
            # Probably the directory exists already
            if exc.errno == errno.EEXIST and os.path.isdir(cache_dir):
                pass
            else:
                raise

        cache_path = os.path.join(cache_dir, args[0]) if args else settings.WORDCLOUD_CACHE_PATH

        with open(cache_path, 'w') as cache_file:
            simplejson.dump(popular_words(max_entries=30), cache_file)
