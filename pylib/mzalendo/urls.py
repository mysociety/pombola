from django.conf.urls.defaults import patterns, include, url

import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('core.views',
    # Homepage
    url(r'^$', 'home', name='home'),

    # Lists
    url(r'^person/all/',       'person_list',       name='person_list'),
    url(r'^place/all/',        'place_list',        name='place_list'),
    url(r'^organisation/all/', 'organisation_list', name='organisation_list'),
    
    # Objects
    url(r'^person/(?P<slug>[-\w]+)/',       'person',       name='person'),
    url(r'^place/(?P<slug>[-\w]+)/',        'place',        name='place'),
    url(r'^position/(?P<slug>[-\w]+)/',     'position',     name='position'),


    url(r'^organisation/is/(?P<slug>[-\w]+)/', 'organisation_kind', name='organisation_kind'),
    url(r'^organisation/(?P<slug>[-\w]+)/', 'organisation', name='organisation'),

    url(r'^search/', 'search', name='search'),

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

# Admin
urlpatterns += patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

# serve media_root files if needed (/static served in dev by runserver)
if settings.SERVE_STATIC_FILES:
    urlpatterns += patterns('',
        (   r'^media_root/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }
        ),
    )


