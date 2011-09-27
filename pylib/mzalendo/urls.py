from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

import settings


# Admin section
from django.contrib import admin
admin.autodiscover()
urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)


# Accounts
urlpatterns += patterns('',
    (r'^accounts/', include('registration.backends.default.urls')),
)

# Comments
urlpatterns += patterns('',    
    (r'^comments/', include('mz_comments.urls')),
)

# Info pages
urlpatterns += patterns('',
    (r'^info/', include('info.urls')),
)

# Hansard pages
urlpatterns += patterns('',
    (r'^hansard/', include('hansard.urls')),
)

# Project pages
urlpatterns += patterns('',
    (r'^projects/', include('projects.urls')),
)

# serve some pages directly from templates
urlpatterns += patterns('',
    url(r'^privacy/$', direct_to_template, {'template': 'privacy.html'}, name='privacy'),
)

# serve media_root files if needed (/static served in dev by runserver)
if settings.SERVE_STATIC_FILES:
    urlpatterns += patterns('',
        (   r'^media_root/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }
        ),
    )

# Everything else goes to core
urlpatterns += patterns('',
    (r'^', include('core.urls')),
)
