'''
Checks whether parties in a CSV file exist in the database and adds them
if necessary.
'''

import os
import sys
import unicodecsv
import urllib2
import json
import string
from optparse import make_option
from pombola.core.models import (Organisation, OrganisationKind, Identifier,
                         PlaceKind, Person, Contact, ContactKind, Position,
                         PositionTitle, Place, PlaceKind, AlternativePersonName)
from django.core.management import call_command
from django.core.management.base import NoArgsCommand, CommandError
from django.utils import encoding

from django.core.exceptions import ObjectDoesNotExist

from django_date_extensions.fields import ApproximateDateField, ApproximateDate

class Command(NoArgsCommand):

    help = 'Import csv file of South African political parties'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--parties', '-c',
            help="The parties csv file"),)

    def handle_noargs(self, **options):

        if not os.path.exists(options['parties']):
            print >> sys.stderr, "The parties file doesn't exist",
            sys.exit(1)

        #get the party kind object
        partykind = OrganisationKind.objects.get(slug='party')

        #check each party by checking against slug
        with open(options['parties'], 'rb') as csvfile:
            parties = unicodecsv.reader(csvfile)
            lastmissingparty = ''
            for row in parties:
                try:
                    party = Organisation.objects.get(slug=row[0])
                    if party.name != row[1]:
                        party.name = row[1]
                        party.save()
                except ObjectDoesNotExist:
                    #we need to add the party
                        Organisation.objects.get_or_create(
                            name = row[1],
                            slug = row[0],
                            kind = partykind)

