#!/usr/bin/env python
import os
import sys
import yaml

from django.core.management.base import (
    BaseCommand, CommandParser, CommandError
)

# This manage.py file is a bit more complex than you might expect, for
# two reasons:
#
#  1. There are different settings modules for each country, but it's
#     a pain to have to specify the one to use all the time.  We'd
#     like to use the settings module that corresponds to the
#     COUNTRY_APP in conf/general.yml by default.
#
#  2.  It's nice if "./manage.py test" works out-of-the-box, so work
#      out if "test" is the subcommand and the user hasn't specified a
#      settings module manually with --settings.  If so, use the
#      settings module for non-country-specific tests that we know has
#      the right INSTALLED_APPS and tests are expected to pass
#      with. This won't help confusion if someone uses
#      "django-admin.py test" instead, but it's some help...  (Note
#      that if someone's set the DJANGO_SETTINGS_MODULE environment
#      variable, this default won't be used either.)

def get_country():
    with open(os.path.join(os.path.dirname(__file__),
                           'conf',
                           'general.yml')) as f:
        config = yaml.load(f)
    return config.get('COUNTRY_APP', 'no_country')

def run_default_tests(command_line_args):
    # This reproduces the logic used by execute_from_command_line to
    # extra whether the subcommand is "test" and whether a settings
    # module has been manually specified.
    try:
        subcommand = command_line_args[1]
    except IndexError:
        return False

    parser = CommandParser(None, usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('--settings')
    parser.add_argument('--pythonpath')
    parser.add_argument('args', nargs='*')
    try:
        options, args = parser.parse_known_args(command_line_args[2:])
    except CommandError:
        # Ignore any errors, we just wanted to extract any settings option
        # that might have been specified.
        options = {'settings': None}

    return subcommand == 'test' and not options.settings


if __name__ == "__main__":

    if run_default_tests(sys.argv):
        settings_module = 'pombola.settings.tests'
        print "Warning: we recommend running tests with ./run-tests instead"
    else:
        # Make the default settings file one that corresponds to the
        # country specified in general.yml
        settings_module = "pombola.settings." + get_country()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
