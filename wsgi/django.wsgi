#!/usr/bin/env python 

import os, sys

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))

# TODO - resolve the way that we refer to our own code and then remove this
# line. Needed (I think) because we do 'from mzalendo.foo import bar' rather
# than the more correct 'from foo inmport bar'.
sys.path.insert(
    0, # insert at the very start
    os.path.normpath(file_dir + "/..")
)

sys.path.insert(
    0, # insert at the very start
    os.path.normpath(file_dir + "/../mzalendo")
)

# check to see if the DJANGO_SETTINGS_MODULE env is set
if not os.environ.get('DJANGO_SETTINGS_MODULE', None):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# check to see if the DJANGO_SETTINGS_MODULE env is set
if not os.environ.get('DJANGO_SETTINGS_MODULE', None):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
