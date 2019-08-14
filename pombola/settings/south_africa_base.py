from .apps import *  # noqa

COUNTRY_APP = 'south_africa'

OPTIONAL_APPS = APPS_REQUIRED_BY_SPEECHES + (
    'speeches',
    'pombola.za_hansard',
    'pombola.interests_register',
    'pombola.spinner',
    'pombola.writeinpublic',
    'formtools',
    'pombola.surveys',
)

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
        ),
        'output_filename': 'css/south-africa.css'
    },
    'datatables': {
        'source_filenames': (
            'css/libs/datatables-1.10.10.css',
        ),
        'output_filename': 'css/datatables.css'
    },
    'chosen': {
        'source_filenames': {
            'css/libs/chosen/chosen.css',
        },
        'output_filename': 'css/chosen.css'
    },
}

COUNTRY_JS = {
    'tabs': {
        'source_filenames': (
            'js/tabs.js',
        ),
        'output_filename': 'js/tabs.js',
    },
    'rep-locator': {
        'source_filenames': (
            'js/rep-locator.js',
        ),
        'output_filename': 'js/rep-locator.js',
    },
    'za-map-drilldown': {
        'source_filenames': (
            'js/za-map-drilldown.js',
        ),
        'output_filename': 'js/za-map-drilldown.js',
    },
    'election-countdown': {
        'source_filenames': (
            'js/election_countdown.js',
        ),
        'output_filename': 'js/election_countdown.js',
    },
    'advanced-search': {
        'source_filenames': (
            'js/advanced-search.js',
        ),
        'output_filename': 'js/advanced-search.js',
    },
    'interests-filter': {
        'source_filenames' : (
            'js/interests-filter.js',
        ),
        'output_filename': 'js/interests-filter.js',
    },
    'attendance-table': {
        'source_filenames': (
            'js/libs/datatables-1.10.10.js',
            'js/attendance-table.js',
        ),
        'output_filename': 'js/attendance-table.js',
    },
    'lazy-loaded-images': {
        'source_filenames': (
            'js/libs/blazy.js',
            'js/lazy-loaded-images.js',
        ),
        'output_filename': 'js/lazy-loaded-images.js',
    },
    'mp-profiles-live-filter': {
        'source_filenames': (
            'js/libs/fuse-2.2.0.js',
            'js/mp-profiles-live-filter.js',
        ),
        'output_filename': 'js/mp-profiles-live-filter.js',
    },
    'person-messages-ajax': {
        'source_filenames': (
            'js/person-messages-ajax.js',
        ),
        'output_filename': 'js/person-messages-ajax.js'
    },
    'writeinpublic': {
        'source_filenames': (
            'js/libs/chosen.jquery.js',
            'js/writeinpublic.js',
        ),
        'output_filename': 'js/writeinpublic.js'
    },
}

INFO_PAGES_ALLOW_RAW_HTML = True

PAGINATION_DEFAULT_WINDOW = 3
