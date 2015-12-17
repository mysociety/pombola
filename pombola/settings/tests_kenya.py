from .base import *  # noqa
from .tests_base import *  # noqa
from .kenya_base import *  # noqa


INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

NOSE_ARGS += ['-a', 'country=kenya']
