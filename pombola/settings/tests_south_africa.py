from .base import *  # noqa
from .tests_base import *  # noqa
from .south_africa_base import *  # noqa


HAYSTACK_CONNECTIONS['default']['EXCLUDED_INDEXES'] = [
    'pombola.search.search_indexes.PlaceIndex',
    'speeches.search_indexes.SpeechIndex',
]

INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

# This is needed by the speeches application
MIDDLEWARE_CLASSES += ( 'pombola.middleware.FakeInstanceMiddleware', )

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

NOSE_ARGS += ['-a', 'country=south_africa']

# For testing purposes we need a cache that we can put stuff in
# to avoid external calls, and generally to avoid polluting the
# cache proper.
CACHES['pmg_api'] = {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'pmg_api_test',
    }
