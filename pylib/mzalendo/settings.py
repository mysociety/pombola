# Django settings for mzalendo project.

import os
import sys
import logging
import setup_env

# Work out where we are to set up the paths correctly and load config
base_dir = os.path.abspath( os.path.split(__file__)[0] + '/../..' )
# print "base_dir: " + base_dir

# load the mySociety config
from mysociety import config
config.set_file( base_dir + "/conf/general.yml" )

if int(config.get('STAGING')):
    STAGING = True
else:
    STAGING = False

# switch on all debug when staging
DEBUG          = STAGING
TEMPLATE_DEBUG = STAGING

# TODO - should we delegate this to web server (issues with admin css etc)?
SERVE_STATIC_FILES = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE':   'django.contrib.gis.db.backends.postgis',
        'NAME':     config.get('MZALENDO_DB_NAME'),
        'USER':     config.get('MZALENDO_DB_USER'),
        'PASSWORD': config.get('MZALENDO_DB_PASS'),
        'HOST':     config.get('MZALENDO_DB_HOST'),
        'PORT':     config.get('MZALENDO_DB_PORT'),
    }
}

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
MEDIA_ROOT = os.path.normpath( os.path.join( base_dir, "../media_root/") )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media_root/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.normpath( os.path.join( base_dir, "../collected_static/") )

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# integer which when updated causes the caches to fetch new content. See note in
# 'base.html' for a better alternative in Django 1.4
STATIC_GENERATION_NUMBER = 3

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

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
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('DJANGO_SECRET_KEY')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
)

ROOT_URLCONF = 'mzalendo.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join( base_dir, "pylib/mzalendo/templates" ),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",    
    "django.contrib.messages.context_processors.messages",
    "mzalendo.core.context_processors.add_settings",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bcrypt',
    
    'registration_defaults',
    'registration',
    
    'django.contrib.admin',
    'django.contrib.admindocs',

    'south',
    'pagination',
    'ajax_select',

    'mz_comments',
    'django.contrib.comments',

    'images',
    'sorl.thumbnail',
    
    'haystack',

    'helpers',
    'info',
    'tasks',
    'hansard',
    'core',
)

COMMENTS_APP = 'mz_comments'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream_to_stderr': {
            'level': 'WARN',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['stream_to_stderr'],
            'level': 'WARN',
            'propagate': True,
        },
    }
}

# configure the bcrypt settings
# Enables bcrypt hashing when ``User.set_password()`` is called.
BCRYPT_ENABLED = True

# Enables bcrypt hashing when running inside Django
# TestCases. Defaults to False, to speed up user creation.
BCRYPT_ENABLED_UNDER_TEST = False

# Number of rounds to use for bcrypt hashing. Defaults to 12.
BCRYPT_ROUNDS = 12

# How long does the user have to activate their account?
ACCOUNT_ACTIVATION_DAYS = 7

# After login go to home page
LOGIN_REDIRECT_URL = '/'


# for the info app
INFO_CONTENT_DIRECTORY = os.path.join( base_dir, "external/wiki_content" )



# pagination related settings
PAGINATION_DEFAULT_PAGINATION      = 10
PAGINATION_DEFAULT_WINDOW          = 2
PAGINATION_DEFAULT_ORPHANS         = 2
PAGINATION_INVALID_PAGE_RAISES_404 = True


# haystack config - interface to Xapian search engine
HAYSTACK_SITECONF      = 'mzalendo.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH   = os.path.abspath( base_dir + "/../mzalendo_xapian" )

# Admin autocomplete
AJAX_LOOKUP_CHANNELS = {
    'person_name'       : dict(model='core.person',        search_field='legal_name'),
    'organisation_name' : dict(model='core.organisation',  search_field='name'),
    'place_name'        : dict(model='core.place',         search_field='name'),
    'title_name'        : dict(model='core.positiontitle', search_field='name'),
}

# Mapit config
MAPIT_URL = config.get('MAPIT_URL')

# misc settings
HTTPLIB2_CACHE_DIR = os.path.abspath( base_dir + '/httplib2_cache' )
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')
