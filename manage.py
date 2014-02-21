#!/usr/bin/env python
import os
import sys
import yaml

with open(os.path.join(os.path.dirname(__file__),
                       'conf',
                       'general.yml')) as f:
    config = yaml.load(f)

country = config.get('COUNTRY_APP', 'no_country')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pombola.settings." + country)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
