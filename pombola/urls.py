import re

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = []


# Country app. In order to let the country app inject its own pages we list it
# first and send all urls through it. If it does not match anything routing
# continues as normal.
#
# Note that anything the country app catches it has to actually process, Django
# does not appear to support fallthrough from controllers:
# http://stackoverflow.com/questions/4495763/fallthrough-in-django-urlconf
if settings.COUNTRY_APP:
    urlpatterns += patterns('',
        (r'^', include('pombola.' + settings.COUNTRY_APP + '.urls')),)

# Needs to occur _before_ admin.autodiscover()
import autocomplete_light
autocomplete_light.autodiscover()

# Admin section
from django.contrib import admin
admin.autodiscover()

from ajax_select import urls as ajax_select_urls
urlpatterns += patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/lookups/', include(ajax_select_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete_light/', include('autocomplete_light.urls')),
)

# mapit
urlpatterns += patterns('',
    (r'^mapit/', include('mapit.urls')),
)

# Info pages
urlpatterns += patterns('',
    (r'^info/', include('pombola.info.urls.pages')),
    (r'^blog/', include('pombola.info.urls.blog')),
)

# File archive
urlpatterns += patterns('',
    (r'^file_archive/', include('pombola.file_archive.urls')),
)

# SayIt - speeches
#if settings.ENABLED_FEATURES['speeches']:
#    urlpatterns += patterns('',
#        (r'^speeches/', include('speeches.urls', namespace='speeches', app_name='speeches-default')),
#    )

# Hansard pages
if settings.ENABLED_FEATURES['hansard']:
    urlpatterns += patterns('',
        (r'^hansard/', include('pombola.hansard.urls', namespace='hansard', app_name='hansard')),
    )

# oject pages
if settings.ENABLED_FEATURES['projects']:
    urlpatterns += patterns('',
        (r'^projects/', include('pombola.projects.urls')),
    )

# ajax preview of the markdown
urlpatterns += patterns('',
    url(r'^markitup/', include('markitup.urls'))
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# needed for the selenium tests.
if settings.IN_TEST_MODE:
    static_url = re.escape(settings.STATIC_URL.lstrip('/'))
    urlpatterns += patterns('',
        url(r'^%s(?P<path>.*)$' % static_url, 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
    )

# search
urlpatterns += patterns('',
    (r'^search/', include('pombola.search.urls')),
)

# feedback
urlpatterns += patterns('',
    (r'^feedback/', include('pombola.feedback.urls')),
)

# map
urlpatterns += patterns('',
    (r'^map/', include('pombola.map.urls')),
)

# votematch
if settings.ENABLED_FEATURES['votematch']:
    urlpatterns += patterns('',
        (r'^votematch/', include('pombola.votematch.urls')),
    )


# # spinner - uncomment if needed. Not needed just to display spinner on the
# # homepage using carousel.
# if settings.ENABLED_FEATURES['spinner']:
#     urlpatterns += patterns('',
#         (r'^spinner/', include('pombola.spinner.urls')),
#     )


# Everything else goes to core
urlpatterns += patterns('',
    (r'^', include('pombola.core.urls')),
)

