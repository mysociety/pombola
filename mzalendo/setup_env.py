"""
Setup all the python paths correctly.

Also set the DJANGO_SETTINGS_MODULE correctly 
"""

import os
import sys

# Work out where we are to set up the paths correctly and load config
base_dir = os.path.abspath( os.path.split(__file__)[0] + '/..' )

# specify the paths we want to add
paths = (
    os.path.normpath( base_dir + "/commonlib/pylib"),
    os.path.normpath( base_dir ),
    os.path.normpath( base_dir + "/mzalendo"),
)

# remove the paths if they are already there (so we don't repeat)
sys.path = [ i for i in sys.path if i not in paths ]

# Insert the new paths at start
for path in paths:
    sys.path.insert( 0, path )

# check to see if the DJANGO_SETTINGS_MODULE env is set
if not os.environ.get('DJANGO_SETTINGS_MODULE', None):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'