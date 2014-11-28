from django.core.management.base import BaseCommand, CommandError

from pombola.ghana.management.tagcloud import tagcloud


class Command(BaseCommand):
    """Generate json file for tagcloud and store in file"""

    help = 'Generate tagcloud data'
    args = '<file>'

    def handle(self, *args, **options):
        # file = open(args[])
        if len(args) != 1:
            raise CommandError
        
        path = args[0]
        outfile = open(path, 'w')
        content = tagcloud()
        outfile.write(content)
        outfile.close()
