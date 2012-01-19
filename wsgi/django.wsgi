#!/usr/bin/env python 

import os, sys

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))

sys.path.insert(
    0, # insert at the very start
    os.path.normpath(file_dir + "/../mzalendo")
)



import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

