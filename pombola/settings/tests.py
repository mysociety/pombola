from .base import *

COUNTRY_APP = None

INSTALLED_APPS = INSTALLED_APPS + \
                 ('pombola.hansard',
                  'pombola.projects',
                  'pombola.place_data',
                  'pombola.votematch',
                  'speeches',
                  'pombola.spinner' ) + \
                 APPS_REQUIRED_BY_SPEECHES

# create the ENABLED_FEATURES hash that is used to toggle features on and off.
ENABLED_FEATURES = {}
for key in ALL_OPTIONAL_APPS: # add in the optional apps
    ENABLED_FEATURES[key] = ('pombola.' + key in INSTALLED_APPS) or (key in INSTALLED_APPS)

BREADCRUMB_URL_NAME_MAPPINGS = {
    'organisation' : ('Organisations', '/organisation/all/'),
}
