import re

from .base import *
from .ghana_base import *

INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

PIPELINE_CSS.update(COUNTRY_CSS)
PIPELINE_JS.update(COUNTRY_JS)
