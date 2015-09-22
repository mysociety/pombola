from pombola.hansard.constants import NAME_SUBSTRING_MATCH

COUNTRY_APP = 'kenya'

OPTIONAL_APPS = [
    'pombola.hansard',
    'pombola.projects',
    'pombola.place_data',
    'pombola.votematch',
    'pombola.bills',
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
    'shujaaz': {
        'source_filenames': (
            'shujaaz/css/bootstrap.css',
            'shujaaz/css/bootstrap-responsive.css',
            'shujaaz/css/flat-ui.css',
            'shujaaz/css/icon-font.css',

            'shujaaz/css/style.css',
        ),
        'output_filename': 'css/shujaaz.css',
    },
}

COUNTRY_JS = {
    'experiments': {
        'source_filenames': (
            'js/click-tracking.js',
            'js/riveted.js',
        ),
        'output_filename': 'js/experiments.js',
        'template_name': 'pipeline/js-array.html',
    },
    'shujaaz-lt-ie8': {
        'source_filenames': (
            'shujaaz/js/icon-font-ie7.js',
        ),
        'output_filename': 'js/shujaaz-lt-ie8.js',
    },
    'shujaaz': {
        'source_filenames': (
            'shujaaz/js/jquery-1.8.3.js',
            'shujaaz/js/bootstrap.js',
            'shujaaz/js/jquery.scrollTo-1.4.3.1.js',
            'shujaaz/js/jquery.parallax-1.1.3.js',
            'shujaaz/js/startup-kit.js',
            'shujaaz/js/script.js',
        ),
        'output_filename': 'js/shujaaz.js',
    },
}

HANSARD_NAME_MATCHING_ALGORITHM = NAME_SUBSTRING_MATCH
