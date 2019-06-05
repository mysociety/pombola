"""
WSGI config for Pombola project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.
"""

import os
import sys

# Add the path to the project root manually here. Ideally it could be added via
# python-path in the httpd.conf WSGI config, but I'm not changing that due to
# the large number of sites running under that config (although it shouldn't
# make a difference, as we just be duplicating the entry for older code that
# does not have this change in).
file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
sys.path.insert(
    0, # insert at the very start
    os.path.normpath(file_dir + "/..")
)

from pombola.config import config, config_path

if int(config.get('STAGING')) and sys.argv[1:2] != ['runserver']:
    import pombola.wsgi_monitor
    pombola.wsgi_monitor.start(interval=1.0)
    if config_path:
        pombola.wsgi_monitor.track(config_path)

country = config.get('COUNTRY_APP', 'no_country')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pombola.settings." + country)

gems_directory = config.get('GEMS_DIRECTORY')
if gems_directory:
    if os.path.exists(gems_directory):
        # If there's a gems directory in the virtualenv, set the GEM_HOME
        # and PATH so that django-pipeline can use compass from there:
        os.environ['GEM_HOME'] = gems_directory
        os.environ['GEM_PATH'] = ''
        os.environ['PATH'] = os.path.join(gems_directory, 'bin') + \
            ':' + os.environ['PATH']

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
