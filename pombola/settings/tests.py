import re

from .base import *

from .tests_base import *

# Make sure that FakeInstanceMiddleware is present since we'll add
# speeches to INSTALLED_APPS for testing:
middleware_to_ensure_present = 'pombola.middleware.FakeInstanceMiddleware'
if middleware_to_ensure_present not in MIDDLEWARE_CLASSES:
    MIDDLEWARE_CLASSES += (middleware_to_ensure_present,)

# Use a different elasticsearch index since we're running tests:
HAYSTACK_CONNECTIONS['default']['INDEX_NAME'] = config.get('POMBOLA_DB_NAME') + '_test'

INSTALLED_APPS += ALL_OPTIONAL_APPS + APPS_REQUIRED_BY_SPEECHES

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

NOSE_ARGS += ['-a', '!country']

COUNTRY_APP = None

MAPIT_COUNTRY = 'Global'
