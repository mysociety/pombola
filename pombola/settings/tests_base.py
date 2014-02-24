import os
import shutil

IN_TEST_MODE = True

base_dir = os.path.abspath( os.path.join( os.path.split(__file__)[0], '..', '..' ) )
# Change the root dir in testing, and delete it to ensure that we have a clean
# slate. Also print out a little warning - adds clutter to the test output but
# better than letting a site go live and not notice that the test mode has been
# detected by mistake
root_dir = os.path.abspath( os.path.join( base_dir, '..', 'testing' ) )
if os.path.exists( root_dir ):
    shutil.rmtree( root_dir )
print "Running in test mode! (testing root_dir is '%s')" % root_dir

# For tests we've change the value of root_dir, so have to reset
# these settings variables:

MEDIA_ROOT = os.path.normpath( os.path.join( root_dir, "media_root/") )
STATIC_ROOT = os.path.normpath( os.path.join( root_dir, "collected_static/") )
HTTPLIB2_CACHE_DIR = os.path.join( root_dir, 'httplib2_cache' )
HANSARD_CACHE = os.path.join( root_dir, 'hansard_cache' )

MAP_BOUNDING_BOX_NORTH = None
MAP_BOUNDING_BOX_SOUTH = None
MAP_BOUNDING_BOX_EAST = None
MAP_BOUNDING_BOX_WEST = None
