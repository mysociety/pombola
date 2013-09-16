#!/usr/bin/env python 

import os, sys

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
sys.path.insert(
    0, # insert at the very start
    os.path.normpath(file_dir + "/..")
)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pombola.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
