from os.path import dirname, join
MIU_TEST_ROOT = dirname(__file__)

INSTALLED_APPS = [
    "markitup",
    "tests"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3"
        }
    }

STATIC_URL = "/static/"

ROOT_URLCONF = "tests.urls"

MARKITUP_FILTER = ("tests.filter.testfilter", {"arg": "replacement"})
