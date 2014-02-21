from .apps import *

COUNTRY_APP = 'south_africa'

OPTIONAL_APPS = (
    'speeches',
    'za_hansard',
    'pombola.interests_register',
    'pombola.spinner',
)

OPTIONAL_APPS += APPS_REQUIRED_BY_SPEECHES

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

INFO_POSTS_PER_LIST_PAGE = 4
