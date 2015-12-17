import re

from django.core.management.base import NoArgsCommand

from django.utils.text import slugify

from optparse import make_option

from pombola.core.models import PlaceKind, Place


def slugify_place_name(place_name):
    return 'ward-' + slugify(place_name)

class Command(NoArgsCommand):
    help = 'Standardize the form of ward names with regard to / and - separators'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        for ward in Place.objects.filter(kind=PlaceKind.objects.get(slug='ward')):
            # print "ward is:", ward
            new_version = re.sub(r'(\w) *([/-]) *(\w)', '\\1 \\2 \\3', ward.name)
            new_version_slug = slugify_place_name(new_version)
            if (new_version != ward.name) or (new_version_slug != ward.slug):
                if options['commit']:
                    print "changing:", ward.name, "to", new_version
                    ward.name = new_version
                    ward.slug = new_version_slug
                    ward.save()
                else:
                    print "would change:", ward.name, "to", new_version, "if --commit were specified"

