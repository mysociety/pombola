from django.core.management.base import BaseCommand, CommandError
from django.utils import simplejson

from wordcloud.wordcloud import popular_words


class Command(BaseCommand):
    """Generate json file for wordcloud and store in file"""

    help = 'Generate wordcloud data'
    args = '<file>'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) != 1:
            raise CommandError

        path = args[0]
        with open(path, 'w') as outfile:
            simplejson.dump(popular_words(), outfile)
