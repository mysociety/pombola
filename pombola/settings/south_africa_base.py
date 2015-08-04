from .apps import *

COUNTRY_APP = 'south_africa'

OPTIONAL_APPS = (
    'speeches',
    'za_hansard',
    'pombola.interests_register',
    'pombola.spinner',
)

OPTIONAL_APPS += APPS_REQUIRED_BY_SPEECHES

SPEECH_SUMMARY_LENGTH = 30

BLOG_RSS_FEED = ''

BREADCRUMB_URL_NAME_MAPPINGS = {
    'info': ['Information', '/info/'],
    'organisation': ['People', '/organisation/all/'],
    'person': ['Politicians', '/person/all/'],
    'place': ['Places', '/place/all/'],
    'search': ['Search', '/search/'],
    'mp-corner': ['MP Corner', '/blog/category/mp-corner'],
    'newsletter': ['MONITOR Newsletter', '/info/newsletter'],
}

TWITTER_USERNAME = 'PeoplesAssem_SA'
TWITTER_WIDGET_ID = '431408035739607040'

MAP_BOUNDING_BOX_NORTH = -22.06
MAP_BOUNDING_BOX_EAST = 32.95
MAP_BOUNDING_BOX_SOUTH = -35.00
MAP_BOUNDING_BOX_WEST = 16.30

MAPIT_COUNTRY = 'ZA'

COUNTRY_CSS = {
    'south-africa': {
        'source_filenames': (
            'sass/south-africa.scss',
            'css/jquery.ui.datepicker.css',
        ),
        'output_filename': 'css/south-africa.css'
    }
}

COUNTRY_JS = {
    'tabs': {
        'source_filenames': (
            'js/tabs.js',
        ),
        'output_filename': 'js/tabs.js',
        'template_name': 'pipeline/js-array.html',
    },
    'za-map-drilldown': {
        'source_filenames': (
            'js/za-map-drilldown.js',
        ),
        'output_filename': 'js/za-map-drilldown.js',
        'template_name': 'pipeline/js-array.html',
    },
    'za-map-drilldown': {
        'source_filenames': (
            'js/election_countdown.js',
        ),
        'output_filename': 'js/election_countdown.js',
        'template_name': 'pipeline/js-array.html',
    },
    'advanced-search': {
        'source_filenames': (
            'js/libs/jquery.ui.datepicker.js',
            'js/advanced-search.js',
        ),
        'output_filename': 'js/advanced-search.js',
        'template_name': 'pipeline/js-array.html',
    },
    'interests-filter': {
        'source_filenames' : (
            'js/interests-filter.js',
        ),
        'output_filename': 'js/interests-filter.js',
        'template_name': 'pipeline/js-array.html',
    }
}

INFO_PAGES_ALLOW_RAW_HTML = True
