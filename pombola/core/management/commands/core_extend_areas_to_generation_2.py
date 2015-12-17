# The import of data into Kenyan MapIt had the constituencies in
# generation 2, while all the other area types were in generation 1.
# This is unfortunate since it makes it appear to later import scripts
# that the district type disappeared between generation 1 and 3.
#
# This script just extends the generation_high to generation 2 for
# every area where it was set to generation 2.

from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation


class Command(NoArgsCommand):
    help = 'Change all genertion_high=1 to generation_high=2'
    def handle_noargs(self, **options):
        g1 = Generation.objects.get(id=1)
        g2 = Generation.objects.get(id=2)
        for area in Area.objects.filter(generation_high=g1):
            area.generation_high = g2
            area.save()
