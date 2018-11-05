import os
import yaml

from pombola.config import config

from .base import *  # noqa
from .ghana_base import *  # noqa


if config.get('EMAIL_SETTINGS', None):
    EMAIL_HOST = config.get('EMAIL_HOST', '')
    EMAIL_HOST_USER = config.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = config.get('EMAIL_HOST_PASSWORD', '')
    port = config.get('EMAIL_PORT', None)
    if port:
        EMAIL_PORT = port
    EMAIL_USE_TLS = config.get('EMAIL_USE_TLS', False)


INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

PIPELINE['STYLESHEETS'].update(COUNTRY_CSS)
PIPELINE['JAVASCRIPT'].update(COUNTRY_JS)

#need this for funky reversematch error in prod
DEBUG_TOOLBAR_PATCH_SETTINGS=False
