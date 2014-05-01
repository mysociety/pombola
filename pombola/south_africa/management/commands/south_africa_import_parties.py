'''
Checks whether parties in a CSV file exist in the database and adds them
if necessary.
'''

import os
import sys
import unicodecsv
from pombola.core.models import Organisation, OrganisationKind
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = 'Import csv file of South African political parties'

    def handle_label(self, label, **options):
        verbosity = int(options['verbosity'])

        if not os.path.exists(label):
            print >> sys.stderr, "The parties file doesn't exist",
            sys.exit(1)

        #get the party kind object
        partykind = OrganisationKind.objects.get(slug='party')

        #check each party by checking against slug
        with open(label, 'rb') as csvfile:
            parties = unicodecsv.reader(csvfile)
            for slug, name in parties:
                try:
                    party = Organisation.objects.get(slug=slug)
                    if party.name != name:
                        if verbosity >= 1:
                            print 'Updating party %s from %s to %s' % (slug, party.name, name)
                        party.name = name
                        party.save()
                except Organisation.DoesNotExist:
                    #we need to add the party
                    if verbosity >= 1:
                        print 'Adding party %s' % name
                    Organisation.objects.create(
                        name = name,
                        slug = slug,
                        kind = partykind)
