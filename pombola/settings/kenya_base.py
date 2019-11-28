from pombola.hansard.constants import NAME_SUBSTRING_MATCH
from pombola.config import config

COUNTRY_APP = 'kenya'

OPTIONAL_APPS = [
    'pombola.hansard',
    'pombola.projects',
    'pombola.place_data',
    'pombola.votematch',
    'pombola.bills',
    'pombola.wordcloud',
    'pombola.sms',
]

TWITTER_USERNAME = 'MzalendoWatch'
TWITTER_WIDGET_ID = '354553209517404160'

BLOG_RSS_FEED = 'https://www.mzalendo.com/feed/'

MAP_BOUNDING_BOX_NORTH = 5.06
MAP_BOUNDING_BOX_EAST = 41.91
MAP_BOUNDING_BOX_SOUTH = -4.73
MAP_BOUNDING_BOX_WEST = 33.83

MAPIT_COUNTRY = 'KE'

COUNTRY_CSS = {
    'kenya': {
        'source_filenames': (
            # .scss files for Kenya
            'sass/kenya.scss',
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
        'source_filenames': (
            'kenya/intro/intro.css',
        ),
        'output_filename': 'css/kenya-intro.css'
    },
}

COUNTRY_JS = {
    'experiments': {
        'source_filenames': (
            'js/click-tracking.js',
            'js/riveted.js',
        ),
        'output_filename': 'js/experiments.js',
    },
    'select2-matchers': {
        'source_filenames': (
            'js/select2-optgroup-matcher.js',
        ),
        'output_filename': 'select2-matchers',
    },
    'facebook-experiment': {
        'source_filenames': (
            'js/select2-optgroup-matcher.js',
            'js/facebook-experiment.js',
        ),
        'output_filename': 'js/facebook-experiment.js',
    },
    'collapse-responsibilities': {
        'source_filenames': (
            'js/collapse-responsibilities.js',
        ),
        'output_filename': 'js/collapse-responsibilities.js',
    },
    'sms-carousel': {
        'source_filenames': (
            'js/sms-carousel.js',
        ),
        'output_filename': 'js/sms-carousel.js',
    },
    'featured-person': {
        'source_filenames': (
            'js/featured-person.js',
        ),
        'output_filename': 'js/featured-person.js',
    },
    'lazy-loaded-images': {
        'source_filenames': (
            'js/libs/blazy.js',
            'js/lazy-loaded-images.js',
        ),
        'output_filename': 'js/lazy-loaded-images.js',
    },
}

HANSARD_NAME_MATCHING_ALGORITHM = NAME_SUBSTRING_MATCH

SURVEYGIZMO_API_TOKEN = config.get('SURVEYGIZMO_API_TOKEN')
SURVEYGIZMO_API_SECRET = config.get('SURVEYGIZMO_API_SECRET')
