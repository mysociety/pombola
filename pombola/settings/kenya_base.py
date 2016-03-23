from pombola.hansard.constants import NAME_SUBSTRING_MATCH

COUNTRY_APP = 'kenya'

OPTIONAL_APPS = [
    'pombola.hansard',
    'pombola.projects',
    'pombola.place_data',
    'pombola.votematch',
    'pombola.bills',
    'pombola.wordcloud',
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
    'women-wordcloud': {
        'source_filenames': (
            'css/jqcloud.css',
        ),
        'output_filename': 'women-wordcloud.js',
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
    'women-wordcloud': {
        'source_filenames': (
            'js/jqcloud-1.0.4.js',
            'js/women-hansard-words.js',
            'js/women-wordcloud.js',
        ),
        'output_filename': 'js/women-wordcloud.js',
        'template_name': 'pipeline/js-array.html',
    },
}

HANSARD_NAME_MATCHING_ALGORITHM = NAME_SUBSTRING_MATCH

PG_DUMP_EXTRA_TABLES_TO_IGNORE = []
PG_DUMP_EXTRA_EXPECTED_TABLES = [
    # hansard, place_data, projects, votematch, wordcloud, bills
    'hansard_alias',
    'hansard_entry',
    'hansard_sitting',
    'hansard_source',
    'hansard_venue',
    'place_data_entry',
    'projects_project',
    'votematch_answer',
    'votematch_party',
    'votematch_quiz',
    'votematch_stance',
    'votematch_statement',
    'bills_bill',
]
