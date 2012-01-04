# Django settings for mzalendo project.

import os
import shutil
import sys
import logging
import setup_env
import yaml

# We need to work out if we are in test mode so that the various directories can
# be changed so that the tests do not clobber the dev environment (eg media
# files, xapian search index, cached hansard downloads).

# Tried various suggestions but most did not work. Eg detecting the 'outbox'
# attribute on django.core.mail does not work as it is created after settings.py
# is read.

# This is absolutely horrid code - assumes that you only ever run tests via
# './manage.py test'. It does work though...
# TODO - replace this with something much more robust
IN_TEST_MODE = sys.argv[1:2] == ['test']

# Work out where we are to set up the paths correctly and load config
base_dir = os.path.abspath( os.path.join( os.path.split(__file__)[0], '..' ) )
root_dir = os.path.abspath( os.path.join( base_dir, '..' ) )

# print "base_dir: " + base_dir
# print "root_dir: " + root_dir

# Change the root dir in testing, and delete it to ensure that we have a clean
# slate. Also rint out a little warning - adds clutter to the test output but
# better than letting a site go live and not notice that the test mode has been
# detected by mistake
if IN_TEST_MODE:
    root_dir += '/testing'
    if os.path.exists( root_dir ):
        shutil.rmtree( root_dir )
    print "Running in test mode! (testing root_dir is '%s')" % root_dir
    

# load the mySociety config
config_file = os.path.join( base_dir, 'conf', 'general.yml' )
config = yaml.load( open(config_file, 'r') )

if int(config.get('STAGING')):
    STAGING = True
else:
    STAGING = False

# switch on all debug when staging
DEBUG          = STAGING
TEMPLATE_DEBUG = STAGING

# TODO - should we delegate this to web server (issues with admin css etc)?
SERVE_STATIC_FILES = STAGING

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = (
    (config.get('MANAGERS_NAME'), config.get('MANAGERS_EMAIL')),
)

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
MEDIA_ROOT = os.path.normpath( os.path.join( root_dir, "media_root/") )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media_root/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.normpath( os.path.join( root_dir, "collected_static/") )

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# integer which when updated causes the caches to fetch new content. See note in
# 'base.html' for a better alternative in Django 1.4
STATIC_GENERATION_NUMBER = 5

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


# Always use the TemporaryFileUploadHandler as it allows us to access the
# uploaded file on disk more easily. Currently used by the CSV upload in
# scorecards admin.
FILE_UPLOAD_HANDLERS = (
    # "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)


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
    os.path.join( base_dir, "mzalendo/templates" ),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",    
    "django.contrib.messages.context_processors.messages",
    "social_auth.context_processors.social_auth_by_type_backends",
    "mzalendo.core.context_processors.add_settings",    
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_bcrypt',
    
    'registration_defaults',
    'registration',
    
    'django.contrib.admin',
    'django.contrib.admindocs',

    'south',
    'pagination',
    'ajax_select',
    'markitup',
    'social_auth',

    'comments2',

    'images',
    'sorl.thumbnail',
    
    'haystack',

    'helpers',
    'info',
    'tasks',
    'hansard',
    'feedback',
    'projects',
    'scorecards',
    'search',
    'user_profile',
    'core',

    'place_data', # TODO - remove entry and app once migrations have run on all servers
    
)

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

# Configure the Hansard app
HANSARD_CACHE = os.path.join( base_dir, "../hansard_cache" )
KENYA_PARSER_PDF_TO_HTML_HOST = config.get('KENYA_PARSER_PDF_TO_HTML_HOST')

# User profile related
AUTH_PROFILE_MODULE = 'user_profile.UserProfile'

# Social auth related
AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# This is empty by default and will be progressively filled if the required
# details are available in the external config
SOCIAL_AUTH_ENABLED_BACKENDS = []

TWITTER_CONSUMER_KEY         = config.get('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET      = config.get('TWITTER_CONSUMER_SECRET')
if TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET:
    SOCIAL_AUTH_ENABLED_BACKENDS.append('twitter')

FACEBOOK_APP_ID              = config.get('FACEBOOK_APP_ID')
FACEBOOK_API_SECRET          = config.get('FACEBOOK_API_SECRET')
if FACEBOOK_APP_ID and FACEBOOK_API_SECRET:
    SOCIAL_AUTH_ENABLED_BACKENDS.append('facebook')

SOCIAL_AUTH_CHANGE_SIGNAL_ONLY = True
SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    # 'social_auth.backends.pipeline.user.update_user_details',
    'user_profile.pipeline.update_user_details',
)

# Appears to have no effect - see https://github.com/omab/django-social-auth/issues/175
# Using a workaround of passing a parameter to the login url instead.
# SOCIAL_AUTH_ERROR_KEY = 'social_errors'

# social test related
TEST_TWITTER_USERNAME = config.get('TEST_TWITTER_USERNAME', None)
TEST_TWITTER_PASSWORD = config.get('TEST_TWITTER_PASSWORD', None)
TEST_TWITTER_REAL_NAME = config.get('TEST_TWITTER_REAL_NAME', None)


# This is in an odd place, but at least we know it will get loaded if it is here
# try:
#     import south
#     from south.modelsinspector import add_introspection_rules
#     add_introspection_rules([], ["^social_auth\.fields\.JSONField"])
# except:
#     pass

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
LOGIN_ERROR_URL    = '/accounts/login/?social_error=1'


# pagination related settings
PAGINATION_DEFAULT_PAGINATION      = 10
PAGINATION_DEFAULT_WINDOW          = 2
PAGINATION_DEFAULT_ORPHANS         = 2
PAGINATION_INVALID_PAGE_RAISES_404 = True


# haystack config - interface to Xapian search engine
HAYSTACK_SITECONF      = 'mzalendo.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH   = os.path.join( root_dir, "mzalendo_xapian" )

# Admin autocomplete
AJAX_LOOKUP_CHANNELS = {
    'person_name'       : dict(model='core.person',        search_field='legal_name'),
    'organisation_name' : dict(model='core.organisation',  search_field='name'),
    'place_name'        : dict(model='core.place',         search_field='name'),
    'title_name'        : dict(model='core.positiontitle', search_field='name'),
}
AJAX_SELECT_BOOTSTRAP = False
AJAX_SELECT_INLINES   = None # we add the js and css ourselves in the header

# Mapit config
MAPIT_URL = config.get('MAPIT_URL')

# misc settings
HTTPLIB2_CACHE_DIR = os.path.join( root_dir, 'httplib2_cache' )
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')


# Markitup settings
MARKITUP_FILTER = ('markdown.markdown', {'safe_mode': True})
MARKITUP_SET = 'markitup/sets/markdown'


# There are some models that are just for testing, so they are not included in
# the South migrations.
SOUTH_TESTS_MIGRATE = False


# Settings for the selenium tests
TEST_RUNNER   = 'django_selenium.selenium_runner.SeleniumTestRunner'
SELENIUM_PATH = config.get( 'SELENIUM_PATH', None )


