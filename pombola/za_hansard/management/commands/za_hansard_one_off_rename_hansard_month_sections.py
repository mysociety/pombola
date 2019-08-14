# This is a one-off script that will rename the Hansard sections so that the month section is not '05' but rather 'May'.

import calendar

from speeches.models import Section
from za_hansard.models import Source

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Rename the Hansard month sections'

    def handle(self, *args, **options):

        # Find the hansard section. Don't catch exception if not found.
        hansard_section = Section.objects.get(title="Hansard", parent=None)

        for year_section in hansard_section.children.all():
            for month_section in year_section.children.all():

                try:
                    month_name = calendar.month_name[int(month_section.title)]
                except ValueError:
                    print "skipping %s (%s)" % (month_section.title, month_section.id)
                    continue # Probably already renamed.

                print "renaming %s (%s) to %s" % (month_section.title, month_section.id, month_name)
                month_section.title = month_name
                month_section.save()
