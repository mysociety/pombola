from django.conf.urls.defaults import patterns, include, url

import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('core.views',
    # Homepage
    url(r'^$', 'home', name='home'),

    # objects
    url(r'^person/(?P<slug>[-\w]+)/',       'person',       name='person'),
    url(r'^place/(?P<slug>[-\w]+)/',        'place',        name='place'),
    url(r'^organisation/(?P<slug>[-\w]+)/', 'organisation', name='organisation'),
)


# Admin
urlpatterns += patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

# server static files if needed
if settings.SERVE_STATIC_FILES:
    urlpatterns += patterns('',
        (   r'^static/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }
        ),
    )
