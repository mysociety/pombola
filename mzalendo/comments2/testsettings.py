import os

DEBUG = TEMPLATE_DEBUG = True
DATABASES= {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   '/tmp/test_comments2.db',    
    },
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'comments2',
]

ROOT_URLCONF = ['comments2.urls']
TEMPLATE_DIRS = os.path.join(os.path.dirname(__file__), 'tests', 'templates')

# There are some models that are just for testing, so they are not included in
# the South migrations.
SOUTH_TESTS_MIGRATE = False
