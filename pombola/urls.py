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
urlpatterns += patterns('',
    (r'^', include( 'pombola.' + settings.COUNTRY_APP + '.urls' ) ),
)


# Admin section
from django.contrib import admin
admin.autodiscover()
from ajax_select import urls as ajax_select_urls
urlpatterns += patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/lookups/', include(ajax_select_urls)),
    url(r'^admin/', include(admin.site.urls)),
)

# include the set_language redirector
urlpatterns += patterns('',
    (r'^i18n/', include('django.conf.urls.i18n')),
)

# mapit
urlpatterns += patterns('',    
    (r'^mapit/', include('mapit.urls')),
)

# Info pages
urlpatterns += patterns('',
    (r'^info/', include('pombola.info.urls')),
)

# File archive
urlpatterns += patterns('',
    (r'^file_archive/', include('pombola.file_archive.urls')),
)

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

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# needed for the selenium tests.
if settings.SERVE_STATIC_FILES:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
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


# Everything else goes to core
urlpatterns += patterns('',
    (r'^', include('pombola.core.urls')),
)

