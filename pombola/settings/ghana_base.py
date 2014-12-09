
INSTALLED_APPS = (
    'django_bcrypt',

    'registration_defaults',
    'registration',
    
    'social_auth',

    'mapit',

    'helpers',

    'user_profile',
    'file_archive',
)



hansard
projects
place_data


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


# haystack config - interface to Xapian search engine
HAYSTACK_SITECONF      = 'mzalendo.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH   = os.path.join( root_dir, "mzalendo_xapian" )

AJAX_SELECT_BOOTSTRAP = False
AJAX_SELECT_INLINES   = None # we add the js and css ourselves in the header

if config.get('EMAIL_SETTINGS', None):
    EMAIL_HOST = config.get('EMAIL_HOST', '')
    EMAIL_HOST_USER = config.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = config.get('EMAIL_HOST_PASSWORD', '')
    port = config.get('EMAIL_PORT', None)
    if port:
        EMAIL_PORT = port
    EMAIL_USE_TLS = config.get('EMAIL_USE_TLS', False)

