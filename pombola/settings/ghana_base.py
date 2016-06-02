COUNTRY_APP = 'ghana'

MAPIT_COUNTRY = 'GH'

MAP_BOUNDING_BOX_NORTH = 11.1750297
MAP_BOUNDING_BOX_EAST = 1.2079193
MAP_BOUNDING_BOX_SOUTH = 4.5874166
MAP_BOUNDING_BOX_WEST = -3.260786

OPTIONAL_APPS = (
    'pombola.hansard',
    'pombola.projects',
    'pombola.place_data',
    'pombola.votematch',
    'pombola.wordcloud',

    # Pombola has now dropped registration, so leave these out:
    # 'registration_defaults',
    # 'registration',

    # Social authentication doesn't seem to be used in Odekro currently:
    # 'social_auth',

    'bootstrap_pagination',
)

COUNTRY_CSS = {
    'ghana': {
        'source_filenames': (
            'css/bootstrap.css',
            'css/bootstrap-theme.css',
            'css/bootstrap-select.css',
            'css/jqcloud.css',
            'css/odekro.css',
        ),
        'output_filename': 'css/ghana.css',
    },
}

COUNTRY_JS = {
    'ghana': {
        'source_filenames': (
            'js/jquery-1.11.3.js',
            'js/bootstrap.js',
            'js/bootstrap-select.js',
            'js/jqcloud-1.0.4.js',
        ),
        'output_filename': 'js/ghana.js',
    },
}

# How long does the user have to activate their account?
ACCOUNT_ACTIVATION_DAYS = 7

# After login go to home page
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL    = '/accounts/login/?social_error=1'

# These are social auth related settings; we've removed that for the
# moment, but these should be reinstated if it's put back:

# # Social auth related
# AUTHENTICATION_BACKENDS = (
#     'social_auth.backends.twitter.TwitterBackend',
#     'social_auth.backends.facebook.FacebookBackend',
#     'django.contrib.auth.backends.ModelBackend',
# )
#
# # This is empty by default and will be progressively filled if the required
# # details are available in the external config
# SOCIAL_AUTH_ENABLED_BACKENDS = []

# TWITTER_CONSUMER_KEY         = config.get('TWITTER_CONSUMER_KEY')
# TWITTER_CONSUMER_SECRET      = config.get('TWITTER_CONSUMER_SECRET')
# if TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET:
#     SOCIAL_AUTH_ENABLED_BACKENDS.append('twitter')
#
# FACEBOOK_APP_ID              = config.get('FACEBOOK_APP_ID')
# FACEBOOK_API_SECRET          = config.get('FACEBOOK_API_SECRET')
# if FACEBOOK_APP_ID and FACEBOOK_API_SECRET:
#     SOCIAL_AUTH_ENABLED_BACKENDS.append('facebook')
#
# SOCIAL_AUTH_CHANGE_SIGNAL_ONLY = True
# SOCIAL_AUTH_PIPELINE = (
#     'social_auth.backends.pipeline.social.social_auth_user',
#     'social_auth.backends.pipeline.associate.associate_by_email',
#     'social_auth.backends.pipeline.user.get_username',
#     'social_auth.backends.pipeline.user.create_user',
#     'social_auth.backends.pipeline.social.associate_user',
#     'social_auth.backends.pipeline.social.load_extra_data',
#     # 'social_auth.backends.pipeline.user.update_user_details',
#     'user_profile.pipeline.update_user_details',
# )
TWITTER_ACCOUNT_NAME = "odekro"
FACEBOOK_ACCOUNT_NAME = "odekro"
