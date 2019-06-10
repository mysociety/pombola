import os
import re

from .apps import *  # noqa

from django.template.defaultfilters import slugify

from pombola.config import config
from pombola.core.logging_filters import skip_unreadable_post
from pombola.hansard.constants import NAME_SET_INTERSECTION_MATCH

IN_TEST_MODE = False

# Work out where we are to set up the paths correctly and load config
base_dir = os.path.abspath( os.path.join( os.path.split(__file__)[0], '..', '..' ) )

# data_dir. If it's specified absolutely, respect it.
# Otherwise assume it's relative to base_dir
conf_data_dir = config.get( 'DATA_DIR', 'data' )
if os.path.isabs(conf_data_dir):
    data_dir = conf_data_dir
else:
    data_dir = os.path.abspath( os.path.join( base_dir, conf_data_dir ) )

if int(config.get('STAGING')):
    STAGING = True
else:
    STAGING = False

# switch on all debug when staging
DEBUG          = STAGING

template_loaders = [
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
    # 'django.template.loaders.eggs.Loader',
]

if not STAGING:
    template_loaders = [
        (
            'django.template.loaders.cached.Loader',
            template_loaders,
        )
    ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            os.path.join(base_dir, "pombola/templates"),
        ],
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.core.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "pombola.core.context_processors.add_settings",
                "pombola.core.context_processors.site_processor",
            ],
            'debug': STAGING,
            # List of callables that know how to import templates from various sources.
            'loaders': template_loaders,
        },
    }
]

ADMINS = (
    (config.get('ERRORS_NAME'), config.get('ERRORS_EMAIL')),
)

SLUGGABLE_SLUGIFY_FUNCTION = slugify

DEFAULT_FROM_EMAIL = config.get('FROM_EMAIL')

# This is the From: address used for error emails to ADMINS
SERVER_EMAIL = DEFAULT_FROM_EMAIL

MANAGERS = (
    (config.get('MANAGERS_NAME'), config.get('MANAGERS_EMAIL')),
)

DATABASES = {
    'default': {
        'ENGINE':   'django.contrib.gis.db.backends.postgis',
        'NAME':     config.get('POMBOLA_DB_NAME'),
        'USER':     config.get('POMBOLA_DB_USER'),
        'PASSWORD': config.get('POMBOLA_DB_PASS'),
        'HOST':     config.get('POMBOLA_DB_HOST'),
        'PORT':     config.get('POMBOLA_DB_PORT'),
    }
}

# Numberof seconds to keep a database connection open for
# in case it can be reused
CONN_MAX_AGE = 0 if STAGING else 300

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = config.get('ALLOWED_HOSTS', [])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = config.get('TIME_ZONE')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-GB'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.normpath( os.path.join( data_dir, "media_root/") )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media_root/'

# Use django-pipeline for handling static files
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.normpath( os.path.join( data_dir, "collected_static/") )

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join( base_dir, "web/static/" ),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'pipeline.finders.FileSystemFinder',
    # 'pipeline.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
    'pipeline.finders.CachedFileFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('DJANGO_SECRET_KEY')

CACHES = {

    # by default use memcached locally. This is what get used by
    # django.core.cache.cache
    'default': {
        'BACKEND':    'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION':   '127.0.0.1:11211',
        'KEY_PREFIX': config.get('POMBOLA_DB_NAME'),
    },

    # we also have a dummy cache that is used for all the page requests - we want
    # the cache framework to auto-add all the caching headers, but we don't actually
    # want to do the caching ourselves - rather we leave that to Varnish on the
    # servers.
    'dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

CACHE_MIDDLEWARE_ALIAS='dummy'
if DEBUG:
    CACHE_MIDDLEWARE_SECONDS = 0
else:
    CACHE_MIDDLEWARE_SECONDS = 60 * 20 # twenty minutes
CACHE_MIDDLEWARE_KEY_PREFIX = config.get('POMBOLA_DB_NAME')

# Always use the TemporaryFileUploadHandler as it allows us to access the
# uploaded file on disk more easily. Currently used by the CSV upload in
# scorecards admin.
FILE_UPLOAD_HANDLERS = (
    # "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware', # first in list so it is able to act last on response
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'mapit.middleware.ViewExceptionMiddleware',
    'django.middleware.security.SecurityMiddleware',
)
if config.get('DEBUG_TOOLBAR', True):
    MIDDLEWARE_CLASSES += ( 'debug_toolbar.middleware.DebugToolbarMiddleware', )

ROOT_URLCONF = 'pombola.urls'

MAPIT_AREA_SRID = 4326
MAPIT_RATE_LIMIT = ['127.0.0.1']
# MAPIT_COUNTRY should be set in the country-specific file

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_unreadable_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_unreadable_post,
        },
     },
    'handlers': {
        'mail_admins': {
            'filters': ['require_debug_false', 'skip_unreadable_posts'],
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream_to_stderr': {
            'level': 'WARN',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['stream_to_stderr'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'elasticsearch': {
            'handlers': ['stream_to_stderr'],
            'level': 'INFO',
            'propagate': True,
        },
        'elasticsearch.trace': {
            'handlers': ['stream_to_stderr'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# Configure the Hansard app
HANSARD_CACHE = os.path.join( base_dir, "../hansard_cache" )
KENYA_PARSER_PDF_TO_HTML_HOST = config.get('KENYA_PARSER_PDF_TO_HTML_HOST')

# The name of a Twitter account related to this website. This will be used to
# pull in the latest tweets on the homepage and in the share on twitter links.
TWITTER_USERNAME = config.get('TWITTER_USERNAME')
# The widget ID is used for displaying tweets on the homepage.
TWITTER_WIDGET_ID = config.get('TWITTER_WIDGET_ID')

# pagination related settings
PAGINATION_DEFAULT_PAGINATION      = 10
PAGINATION_DEFAULT_WINDOW          = 2
PAGINATION_DEFAULT_ORPHANS         = 2
PAGINATION_INVALID_PAGE_RAISES_404 = True

# haystack config - interface to search engine
HAYSTACK_CONNECTIONS = {
    #'default': {
    #    'ENGINE': 'xapian_backend.XapianEngine',
    #    'PATH': os.path.join( data_dir, "pombola_xapian" ),
        #'PATH': os.path.join(os.path.dirname(__file__), 'xapian_index'),
    #},
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'localhost:9200',
        'INDEX_NAME': config.get('POMBOLA_DB_NAME'),
        'EXCLUDED_INDEXES': [],
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# Admin autocomplete
AJAX_LOOKUP_CHANNELS = {
    'person_name'       : ('pombola.core.lookups', 'PersonLookup'),
    'organisation_name' : dict(model='core.organisation',  search_field='name'),
    'place_name'        : dict(model='core.place',         search_field='name'),
    'title_name'        : dict(model='core.positiontitle', search_field='name'),
}

# misc settings
HTTPLIB2_CACHE_DIR = os.path.join( data_dir, 'httplib2_cache' )
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')
COUNTY_PERFORMANCE_EXPERIMENT_KEY = config.get('COUNTY_PERFORMANCE_EXPERIMENT_KEY')
YOUTH_EMPLOYMENT_BILL_EXPERIMENT_KEY = config.get('YOUTH_EMPLOYMENT_BILL_EXPERIMENT_KEY')
GOOGLE_SITE_VERIFICATION = config.get('GOOGLE_SITE_VERIFICATION', None)

IEBC_API_ID = config.get('IEBC_API_ID')
IEBC_API_SECRET = config.get('IEBC_API_SECRET')

# Markitup settings
MARKITUP_FILTER = ('markdown.markdown', {'safe_mode': True, 'extensions':['tables']})
MARKITUP_SET = 'markitup/sets/markdown'
JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js'

# Use nose as the test runner
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--with-doctest', '--with-yanc']

# For the disqus comments
DISQUS_SHORTNAME       = config.get( 'DISQUS_SHORTNAME', None )
# At some point we should deprecate this. For now it defaults to true so that
# no entry in the config does the right thing.
DISQUS_USE_IDENTIFIERS = config.get( 'DISQUS_USE_IDENTIFIERS', True )
FACEBOOK_APP_ID = config.get('FACEBOOK_APP_ID')


# Polldaddy widget ID - from http://polldaddy.com/
# Use the widget rather than embedding a poll direct as it will allow the poll
# to be changed without having to alter the settings or HTML. If left blank
# then no poll will be shown.
POLLDADDY_WIDGET_ID = config.get( 'POLLDADDY_WIDGET_ID', None );


# RSS feed to the blog related to this site. If present will cause the 'Latest
# News' to appear on the homepage.
BLOG_RSS_FEED = config.get( 'BLOG_RSS_FEED', None )

THUMBNAIL_DEBUG = True

# ZA Hansard settings
HANSARD_CACHE   = os.path.join( data_dir, 'hansard_cache' )
COMMITTEE_CACHE = os.path.join( HANSARD_CACHE, 'committee' )
ANSWER_CACHE    = os.path.join( HANSARD_CACHE, 'answers' )
QUESTION_CACHE  = os.path.join( HANSARD_CACHE, 'questions' )
ANSWER_JSON_CACHE  = os.path.join( HANSARD_CACHE, 'answers_json' )
QUESTION_JSON_CACHE  = os.path.join( HANSARD_CACHE, 'questions_json' )

PMG_COMMITTEE_USER = config.get('PMG_COMMITTEE_USER', '')
PMG_COMMITTEE_PASS = config.get('PMG_COMMITTEE_PASS', '')
PMG_API_KEY = config.get('PMG_API_KEY', '')

# Algorithm to use for matching names when scraping hansard
# NAME_SUBSTRING_MATCH
# - strips the title from the name and then searches for current politicians
#   with names containing that string (used by Kenya).
# NAME_SET_INTERSECTION_MATCH
# - splits the name, including title, into words, and then compares the
#   set of these words with similar sets from current politicians,
#   looking for the largest intersection.
HANSARD_NAME_MATCHING_ALGORITHM = NAME_SET_INTERSECTION_MATCH

# Which popit instance to use
POPIT_API_URL = config.get('POPIT_API_URL')

BREADCRUMB_URL_NAME_MAPPINGS = {
    'info'   : ('Information', '/info/'),
    'organisation' : ('Organisations', '/organisation/all/'),
    'person' : ('Politicians', '/person/all/'),
    'place' : ('Places', '/place/all/'),
    'search' : ('Search', '/search/')
}

# Info page settings
INFO_POSTS_PER_LIST_PAGE = 10

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.gis',

    'pombola.admin_additions',
    'autocomplete_light',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'ajax_select',
    'markitup',

    'pipeline',

    'mapit',

    'popolo',

    'images',
    'sorl.thumbnail',
    # easy_thumbnails is required by SayIt; it needs to be in
    # INSTALLED_APPS so that its table is created so that we can
    # create SayIt speakers. It should be after sorl.thumbnails so
    # that sorl.thumbnails (used by Pombola) is what's loaded when
    # Pombola templates do {% load thumbnail %}
    'easy_thumbnails',

    'haystack',

    'slug_helpers',
    'info',

    'pombola.tasks',
    'pombola.core',
    'pombola.feedback',
    'pombola.scorecards',
    'pombola.search',
    'file_archive',
    'pombola.map',
    'pombola.experiments',
    'pombola.budgets',

    'pagination',
    'django_nose',
    'django_extensions',

    'rest_framework',
)
if config.get('DEBUG_TOOLBAR', True):
     INSTALLED_APPS += ('debug_toolbar',)

def insert_after(sequence, existing_item, item_to_put_after):
    """A helper method for inserting an item after another in a sequence

    This returns a new list with 'item_to_put_after' inserted after
    'existing_item' in 'sequence'; this is useful for putting items
    into the expected position in INSTALLED_APPS.  Note that this will
    return a list even if sequence is a tuple, but Django doesn't mind
    if INSTALLED_APPS is a list."""
    l = list(sequence)
    i = l.index(existing_item)
    l.insert(i + 1, item_to_put_after)
    return l

def make_enabled_features(installed_apps, all_optional_apps):
    result = {}
    for key in all_optional_apps:
        key = re.sub(r'^pombola\.', '', key)
        result[key] = ('pombola.' + key in installed_apps) or (key in installed_apps)
    return result

# Set up the core CSS and JS files:

PIPELINE_CSS = {
    'countdown': {
        'source_filenames': (
            'css/jquery.countdown-v1.6.0.css',
            'sass/countdown.scss',
        ),
        'output_filename': 'css/countdown.css',
    },
    'admin': {
        'source_filenames': (
            # .scss files from core:
            'sass/admin.scss',
        ),
        'output_filename': 'css/admin.css',
    },
}

PIPELINE_JS = {
   'base': {
        'source_filenames': (
            'js/libs/jquery-ui.js',
            'js/libs/jquery.form-v2.94.js',
            'js/functions.js',
            'js/hover-dropdown.js',
            'js/twitter-embed.js',
            'js/analytics.js',
        ),
        'output_filename': 'js/base.js',
    },
    'load-appearances': {
        'source_filenames': (
            'js/load-appearances.html',
        ),
        'output_filename': 'js/load-appearances.js',
    },
    'feeds': {
        'source_filenames': (
            'js/feeds.js',
        ),
        'output_filename': 'js/feeds.js',
    },
    'responsive-carousel': {
        'source_filenames': (
            'js/libs/responsive-carousel.js',
        ),
        'output_filename': 'js/responsive-carousel.js',
    },
    'map': {
        'source_filenames': (
            'js/map-drilldown.js',
        ),
        'output_filename': 'js/base-map-drilldown.js',
    },
    'ui-test': {
        'source_filenames': (
            'js/ui-test.js',
        ),
        'output_filename': 'js/ui-test.js',
    },
    'google-map': {
        'source_filenames': (
            'js/map.js',
        ),
        'output_filename': 'js/google-map.js',
    },
    'modernizr': {
        'source_filenames': (
            'js/libs/modernizr.js',
        ),
        'output_filename': 'js/modernizr.js',
    },
    'respond': {
        'source_filenames': (
            'js/libs/respond.1.4.2.js',
        ),
        'output_filename': 'js/respond.js',
    },
    'hide-reveal': {
        'source_filenames': (
            'js/hide-reveal.js',
        ),
        'output_filename': 'js/hide-reveal.js',
    },
    'survey': {
        'source_filenames': (
            'js/survey.js',
        ),
        'output_filename': 'js/survey.js',
    },
}

# Only for debugging compression (the default is: 'not DEBUG' which is
# fine when not experimenting with compression)
# PIPELINE_ENABLED = True

PIPELINE_COMPILERS = (
  'pipeline_compass.compass.CompassCompiler',
)
PIPELINE_COMPASS_BINARY = os.path.join(data_dir, 'gem-bin', 'compass')


PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'


PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'

PIPELINE_DISABLE_WRAPPER = True

EXCLUDE_FROM_SEARCH = ()

# Settings for bleach, used by sayit to determine what html is allowed
BLEACH_ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'i', 'u', 'span', 'sub', 'sup', 'br',
    'p',
    'ol', 'ul', 'li',
    'table', 'caption', 'tr', 'th', 'td',
]

BLEACH_ALLOWED_ATTRIBUTES = {
    '*': [ 'id', 'title' ], # class, style
    'a': [ 'href' ],
    'li': [ 'value' ],
}

BLEACH_STRIP_TAGS = True

INFO_PAGES_ALLOW_RAW_HTML = False

if config.get('EMAIL_SETTINGS', None):
    EMAIL_HOST = config.get('EMAIL_HOST', '')
    EMAIL_HOST_USER = config.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = config.get('EMAIL_HOST_PASSWORD', '')
    port = config.get('EMAIL_PORT', None)
    if port:
        EMAIL_PORT = port
    EMAIL_USE_TLS = config.get('EMAIL_USE_TLS', False)

# Django Rest Framework settings:
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('pombola.api.permissions.ReadOnly',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'PAGE_SIZE': 10,
}

# The feature of the ./manage.py shell_plus command in
# django-extensions that automatically imports the models from your
# django applications is very useful, but there are some name
# conflicts.  e.g. Person unhelpfully is the django-popolo Person
# model, not the Pombola core person model. This setting allows you to
# specify a prefix for all the models imported from a particular
# app. For example, this means that the django-popolo Person model is
# now available under the 'popolo_Person' alias, and 'Person' refers
# to the Pombola core person.

SHELL_PLUS_APP_PREFIXES = {
    'popolo': 'popolo',
    'speeches': 'speeches',
    'scorecards': 'scorecards',
    'interests_register': 'interests',
    'place_data': 'place_data',
}

GOOGLE_MAPS_GEOCODING_API_KEY = config.get('GOOGLE_MAPS_GEOCODING_API_KEY', '')

KENYA_SMS_API_URL = config.get('KENYA_SMS_API_URL')
KENYA_SMS_API_SHORT_CODE = config.get('KENYA_SMS_API_SHORT_CODE')
KENYA_SMS_API_KEY = config.get('KENYA_SMS_API_KEY')
