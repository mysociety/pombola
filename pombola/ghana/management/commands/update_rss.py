from django.core.management.base import BaseCommand, CommandError

from pombola.ghana.management.aggregate_rss import aggregate_articles


class Command(BaseCommand):
    """Generate html for article feed and store in file"""

    help = 'Aggregates news feeds related to Parliament'
    args = '<file>'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) != 1:
            raise CommandError
        
        path = args[0]
        outfile = open(path, 'w')
        content = aggregate_articles()
        outfile.write(content)
        outfile.close()
