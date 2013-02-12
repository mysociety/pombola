import re

from django.core.management.base import NoArgsCommand, CommandError

from django.template.defaultfilters import slugify

from optparse import make_option

from core.models import PlaceKind, Place

class Command(NoArgsCommand):
    help = 'Standardize the form of ward names with regard to / and - separators'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        for ward in Place.objects.filter(kind=PlaceKind.objects.get(slug='ward')):
            # print "ward is:", ward
            new_version = re.sub(r'(\w) *([/-]) *(\w)', '\\1 \\2 \\3', ward.name)
            if new_version != ward.name:
                if options['commit']:
                    print "changing:", ward.name, "to", new_version
                    ward.name = new_version
                    ward.slug = 'ward-' + slugify(ward.name)
                    ward.save()
                else:
                    print "would change:", ward.name, "to", new_version, "if --commit were specified"

