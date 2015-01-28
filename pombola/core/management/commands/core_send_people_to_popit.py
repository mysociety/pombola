# This command creates a new PopIt instance based on the Person,
# Position and Organisation models in Pombola.

import json
from optparse import make_option
import slumber
import sys
import urlparse

from pombola.core.popolo_helpers import get_popolo_data, create_organisations, create_people

from django.core.management.base import BaseCommand, CommandError

from popit_api import PopIt

class Command(BaseCommand):
    args = 'MZALENDO-URL'
    help = 'Take all people in Pombola and import them into a PopIt instance'
    option_list = BaseCommand.option_list + (
            make_option("--instance", dest="instance",
                        help="The name of the PopIt instance (e.g. ukcabinet)",
                        metavar="INSTANCE"),
            make_option("--hostname", dest="hostname",
                        default="popit.mysociety.org",
                        help="The PopIt hostname (default: popit.mysociety.org)",
                        metavar="HOSTNAME"),
            make_option("--user", dest="user",
                        help="Your username", metavar="USERNAME"),
            make_option("--password", dest="password",
                        help="Your password", metavar="PASSWORD"),
            make_option("--port", dest="port",
                        help="port (default: 80)", metavar="PORT"),
            make_option("--test", dest="test", action="store_true",
                        help="run doctests", metavar="PORT"),
            )

    def handle(self, *args, **options):

        popit_option_keys = ('instance', 'hostname', 'user', 'password', 'port')
        popit_options = dict((k, options[k]) for k in popit_option_keys if options[k] is not None)
        popit_options['api_version'] = 'v0.1'

        if len(args) != 1:
            raise CommandError, "You must provide the base URL of the public Pombola site"

        try:
            popit = PopIt(**popit_options)

            base_url = args[0]
            parsed_url = urlparse.urlparse(base_url)

            primary_id_scheme = '.'.join(reversed(parsed_url.netloc.split('.')))

            message = "WARNING: this script will delete everything in the PopIt instance %s on %s.\n"
            message += "If you want to continue with this, type 'Yes': "

            response = raw_input(message % (popit.instance, popit.hostname))
            if response != 'Yes':
                print >> sys.stderr, "Aborting."
                sys.exit(1)

            if parsed_url.path or parsed_url.params or parsed_url.query or parsed_url.fragment:
                raise CommandError, "You must only provide the base URL"

            # Remove all the "person", "organization" and "membership"
            # objects from PopIt.  Currently there's no command to
            # delete all in one go, so we have to do it one-by-one.

            for schema_singular in ('person', 'organization', 'membership'):
                while True:
                    plural = schema_singular + 's'
                    response = getattr(popit, plural).get()
                    for o in response['result']:
                        print >> sys.stderr, "deleting the {0}: {1}".format(
                            schema_singular, o)
                        getattr(popit, plural)(o['id']).delete()
                    if not response.get('has_more', False):
                        break

            # Create all the organisations found in Pombola:
            create_organisations(popit, primary_id_scheme, base_url)

            # Create a person in PopIt for each Person in Pombola:
            create_people(popit, primary_id_scheme, base_url)

        except slumber.exceptions.HttpClientError, e:
            print "Exception is:", e
            print "Error response content is", e.content
            sys.exit(1)
