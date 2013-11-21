# this is a one-off script to push the contents of 
# pombola/south_africa/data/south-africa-popolo.json
# to popit

import json
from optparse import make_option
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import sys

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

class Command (BaseCommand):

    help = "Prepare json for import into popit"
    option_list = BaseCommand.option_list + (
        make_option("--user", type="string",
                    help="The username for the popit instance"),
        make_option("--pass", type="string",
                    help="The password for the popit instance")
        )

    def handle(self, *args, **options):

        data = json.load( open('pombola/south_africa/data/south-africa-popolo.json', 'r') )

        persons       = data['persons']
        organizations = data['organizations']
        memberships   = []

        for person in persons:
            memberships += person.pop('memberships', [])

        json.dump( persons,       open('persons.json', 'w') )
        json.dump( organizations, open('organizations.json', 'w') )
        json.dump( memberships,   open('memberships.json', 'w') )

        user     = options['user']
        password = options['pass']
        auth=HTTPBasicAuth(user, password)

        self.update_popit(organizations, 'organizations', auth)
        self.update_popit(persons,       'persons',       auth)
        self.update_popit(memberships,   'memberships',   auth)

    def update_popit(self, collection, collection_name, auth):
        for item in collection:
            print >> sys.stderr, json.dumps(item)
            r = requests.post(
                'http://za-peoples-assembly.popit.mysociety.org/api/v0.1/%s'
                    % collection_name, 
                data=json.dumps(item),
                auth=auth,
                headers={
                    'Content-Type': 'application/json; charset=utf8',
                },
                )
            if not r.status_code == 200:
                raise Exception("Error %d (%s)" % (r.status_code, r.text) )
