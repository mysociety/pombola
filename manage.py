#!/usr/bin/env python
import os
import sys
import yaml

from django import get_version
from django.core.management import LaxOptionParser, BaseCommand

# Make the default settings file one that corresponds to the country
# specified in general.yml

with open(os.path.join(os.path.dirname(__file__),
                       'conf',
                       'general.yml')) as f:
    config = yaml.load(f)

country = config.get('COUNTRY_APP', 'no_country')

# However, it's nice if "./manage.py test" works out-of-the-box, so
# work out if "test" is the subcommand and the user hasn't specified a
# settings module with --settings.  If so, use the settings module for
# non-country-specific tests that we know has the right INSTALLED_APPS
# and tests are expected to pass with. This won't help confusion if
# someone uses "django-admin.py test" instead, but it's some help...
# (Note that if someone's set the DJANGO_SETTINGS_MODULE environment
# variable, this default won't be used either.)

parser = LaxOptionParser(option_list=BaseCommand.option_list)
try:
    options, args = parser.parse_args(sys.argv)
except:
    # Ignore any errors at this point; the arguments will be parsed
    # again shortly anyway.
    args = None

run_default_tests = (args and args[1] == 'test' and not options.settings)

if __name__ == "__main__":

    if run_default_tests:
        settings_module = 'pombola.settings.tests'
        print "Warning: we recommend running tests with ./run-tests instead"
    else:
        settings_module = "pombola.settings." + country

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
