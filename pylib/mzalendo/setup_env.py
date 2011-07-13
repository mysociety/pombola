"""
Setup all the python paths correctly.

Also set the DJANGO_SETTINGS_MODULE correctly 
"""

import os
import sys

# Work out where we are to set up the paths correctly and load config
base_dir = os.path.abspath( os.path.split(__file__)[0] + '/../..' )
# print "base_dir: " + base_dir

paths = (
    os.path.normpath( base_dir + "/commonlib/pylib"),
    os.path.normpath( base_dir + "/pylib"),
)

# Insert the new paths at index 1 so that they come after '.'
for path in paths:
    sys.path.insert( 1, path )

# check to see if the DJANGO_SETTINGS_MODULE env is set
if not os.environ.get('DJANGO_SETTINGS_MODULE', None):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'