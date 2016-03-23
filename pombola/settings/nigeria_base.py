COUNTRY_APP = 'nigeria'

OPTIONAL_APPS = ['pombola.spinner']

TWITTER_USERNAME = 'NGShineyoureye'
TWITTER_WIDGET_ID = '354909651910918144'

BLOG_RSS_FEED = 'http://eienigeria.org/rss.xml'

MAP_BOUNDING_BOX_NORTH = 14.1
MAP_BOUNDING_BOX_EAST = 14.7
MAP_BOUNDING_BOX_SOUTH = 4
MAP_BOUNDING_BOX_WEST = 2.5

MAPIT_COUNTRY = 'NG'

COUNTRY_CSS = {
    'nigeria': {
        'source_filenames': (
            # .scss files for Nigeria
            'sass/nigeria.scss',
        ),
        'output_filename': 'css/nigeria.css'
    }
}

PG_DUMP_EXTRA_TABLES_TO_IGNORE = [
    # In the past I think the hansard application was in use
    # for Nigeria, so these tables are present (and contain
    # data), but the hansard app is no longer used for
    # Nigeria.  So, it's best to ignore these tables to make
    # the dump smaller.  place_data and projects are similarly
    # no longer used (but those applications' tables are empty
    # anyway)
    'hansard_alias',
    'hansard_entry',
    'hansard_sitting',
    'hansard_source',
    'hansard_venue',
    'place_data_entry',
    'projects_project',
]
PG_DUMP_EXTRA_EXPECTED_TABLES = [
    'spinner_imagecontent',
    'spinner_quotecontent',
    'spinner_slide',
]
