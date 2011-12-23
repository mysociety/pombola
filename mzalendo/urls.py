from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import direct_to_template


# Admin section
from django.contrib import admin
admin.autodiscover()
from ajax_select import urls as ajax_select_urls
urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/lookups/', include(ajax_select_urls)),
    url(r'^admin/', include(admin.site.urls)),
)


# Accounts
urlpatterns += patterns('',
    (r'^accounts/', include('registration.backends.default.urls')),
)

# Comments
urlpatterns += patterns('',    
    (r'^comments/', include('comments2.urls')),
)

# Info pages
urlpatterns += patterns('',
    (r'^info/', include('info.urls')),
)

# Hansard pages
urlpatterns += patterns('',
    (r'^hansard/', include('hansard.urls', namespace='hansard', app_name='hansard')),
)

# Project pages
urlpatterns += patterns('',
    (r'^projects/', include('projects.urls')),
)

# serve some pages directly from templates
urlpatterns += patterns('',
    url(r'^privacy/$', direct_to_template, {'template': 'privacy.html'}, name='privacy'),
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

# social auth
urlpatterns += patterns('',
    url(r'^social/', include('social_auth.urls')),
)

# search
urlpatterns += patterns('',
    (r'^search/', include('search.urls')),
)

# search
urlpatterns += patterns('',
    (r'^feedback/', include('feedback.urls')),
)

# Everything else goes to core
urlpatterns += patterns('',
    (r'^', include('core.urls')),
)
