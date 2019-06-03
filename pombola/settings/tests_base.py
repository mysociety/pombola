import os
import shutil
from pombola.config import config

IN_TEST_MODE = True

base_dir = os.path.abspath( os.path.join( os.path.split(__file__)[0], '..', '..' ) )
# Change the data dir in testing, and delete it to ensure that we have a clean
# slate. Also print out a little warning - adds clutter to the test output but
# better than letting a site go live and not notice that the test mode has been
# detected by mistake
conf_data_dir = config.get( 'DATA_DIR', 'data' )
if os.path.isabs(conf_data_dir):
    data_dir = os.path.join( conf_data_dir, 'testing' )
else:
    data_dir = os.path.abspath( os.path.join( base_dir, conf_data_dir, 'testing' ) )

if os.path.exists( data_dir ):
    shutil.rmtree( data_dir )

print("Running in test mode! (testing data_dir is '%s')" % data_dir)

# For tests we've change the value of data_dir, so have to reset
# these settings variables:

MEDIA_ROOT = os.path.normpath( os.path.join( data_dir, "media_root/") )
STATIC_ROOT = os.path.normpath( os.path.join( data_dir, "collected_static/") )
HTTPLIB2_CACHE_DIR = os.path.join( data_dir, 'httplib2_cache' )
HANSARD_CACHE = os.path.join( data_dir, 'hansard_cache' )

MAP_BOUNDING_BOX_NORTH = None
MAP_BOUNDING_BOX_SOUTH = None
MAP_BOUNDING_BOX_EAST = None
MAP_BOUNDING_BOX_WEST = None

# A workaround so that functional tests don't fail with missing
# assets, as suggested here:
#   https://github.com/cyberdelia/django-pipeline/issues/277
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
