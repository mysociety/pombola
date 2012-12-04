from django.core.management.base import BaseCommand, CommandError

from odekro import management


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
        content = management.generate_tagcloud()
        outfile.write(content)
        outfile.close()
