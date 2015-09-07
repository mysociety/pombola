import os
from django.core.management.base import BaseCommand, CommandError

from pombola.ghana.management.hansard_parser import parse
from pombola.ghana.management.commands import add_infopage

class Command(BaseCommand):
    """Import Hansard"""

    help = 'Import Hansard'

    def handle(self, *args, **options):
        PAGES = (
            # About
            ('odekro-overview.md', 'Odekro Overview'),
            ('faqs.md', 'FAQs'),
            ('policies.md', 'Policies'),
            ('partners.md', 'Partners'),
            ('contact-us.md', 'Contact Information for Odekro.org'),
            # Places
            ('places-overview.md', 'Overview'),
            # Parliament
            ('parliament-overview.md', 'Parliament'),
            ('bills-overview.md', 'Bills'),
            ('committee-overview.md', 'Committees'),
        )

        basedir = os.path.abspath(os.path.dirname( __file__ ))
        datadir = os.path.join(basedir, '..', '..', 'data')

        print '>>>>>>>>> DATA: ', datadir

        cmd = add_infopage.Command()

        for fname, title in PAGES:
            cmd.handle(*(os.path.join(datadir, fname), title))

