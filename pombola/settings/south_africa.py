import errno
import os

from .base import *  # noqa
from .south_africa_base import *  # noqa

HAYSTACK_CONNECTIONS['default']['EXCLUDED_INDEXES'] = [
    'pombola.search.search_indexes.PlaceIndex',
    'speeches.search_indexes.SpeechIndex',
]

HAYSTACK_CONNECTIONS['default']['ENGINE'] = 'pombola.south_africa.search.ZAElasticSearchEngine'


INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

# This is needed by the speeches application
MIDDLEWARE_CLASSES += ( 'pombola.middleware.FakeInstanceMiddleware', )

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

PIPELINE_CSS.update(COUNTRY_CSS)
PIPELINE_JS.update(COUNTRY_JS)

EXCLUDE_FROM_SEARCH = ('places', 'info_pages');

PMG_API_CACHE_PATH = os.path.join(data_dir, 'pmg_api_cache')

try:
    os.makedirs(PMG_API_CACHE_PATH)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
CACHES['pmg_api'] = {
    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    'LOCATION': PMG_API_CACHE_PATH,
    'OPTIONS': {
        'MAX_ENTRIES': 10000,
        },
    'TIMEOUT': 60*60*24,
}
