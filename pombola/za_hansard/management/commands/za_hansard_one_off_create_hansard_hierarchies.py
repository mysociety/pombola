# This is a one-off script that will search for any sections that appear to be
# from Hansard and that are not a sub-section of something else. This will
# change the database to match what would have been the case had the changes in
# https://github.com/mysociety/za-hansard/commit/aa8dd4df31062049b33304a1a7c3011
# 13505773d been in place when the processing was first done. As the processing
# is so slow it is much easier to alter the database than to re-run the
# scraping.


from speeches.models import Section
from za_hansard.models import Source

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Restructure the hansard section hierarchy'

    def handle(self, *args, **options):

        # The sections we are interested in are linked to the sources table, and
        # have no parent.
        sources = Source.objects.filter(sayit_section__isnull=False, sayit_section__parent__isnull=True)

        for source in sources:
            section = source.sayit_section
            print section

            # create the parents
            parent = Section.objects.get_or_create_with_parents(instance=section.instance, headings=source.section_parent_headings)

            # assign to the new section
            section.parent = parent
            section.save()
