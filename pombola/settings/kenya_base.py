COUNTRY_APP = 'kenya'

OPTIONAL_APPS = [
    'pombola.hansard',
    'pombola.projects',
    'pombola.place_data',
    'pombola.votematch',
]

TWITTER_USERNAME = 'MzalendoWatch'
TWITTER_WIDGET_ID = '354553209517404160'

BLOG_RSS_FEED = 'http://www.mzalendo.com/feed/'

MAP_BOUNDING_BOX_NORTH = 5.06
MAP_BOUNDING_BOX_EAST = 41.91
MAP_BOUNDING_BOX_SOUTH = -4.73
MAP_BOUNDING_BOX_WEST = 33.83

MAPIT_COUNTRY = 'KE'

COUNTRY_CSS = {
    'kenya': {
        'source_filenames': (
            # .scss files for Kenya
            'scss/kenya.scss',
            # .css files for Kenya
            'css/jquery.countdown-v1.6.0.css',
            'css/jquery-ui-1.8.17.custom.css',
            'css/admin.css',
        ),
        'output_filename': 'css/kenya.css'
    },
    'election-2013': {
        'source_filenames': (
            'kenya/election-homepage/base.css',
            'kenya/election-homepage/style.css',
        ),
        'output_filename': 'css/election-2013.css'
    },
    'intro': {
        'source_filenames': {
            'kenya/intro/intro.css',
        },
        'output_filename': 'css/kenya-intro.css'
    }
}

COUNTRY_JS = {}
# COUNTRY_JS = {
#     'kenya': {
#         'source_filenames': (
#             'js/click-tracking.js',
#         ),
#         'output_filename': 'js/kenya.js'
#     }
# }
