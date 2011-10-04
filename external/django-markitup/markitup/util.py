import posixpath
from django.conf import settings as django_settings
from markitup import settings

def absolute_url(path, prefix=None):
    if prefix is None:
        prefix = django_settings.STATIC_URL
    if path.startswith(u'http://') or path.startswith(u'https://') or path.startswith(u'/'):
        return path
    return posixpath.join(prefix, path)
