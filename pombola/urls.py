import re

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

from rest_framework import routers

urlpatterns = []


# Country app. In order to let the country app inject its own pages we list it
# first and send all urls through it. If it does not match anything routing
# continues as normal.
#
# Note that anything the country app catches it has to actually process, Django
# does not appear to support fallthrough from controllers:
# http://stackoverflow.com/questions/4495763/fallthrough-in-django-urlconf
if settings.COUNTRY_APP:
    urlpatterns += (
        url(r'^', include('pombola.' + settings.COUNTRY_APP + '.urls')),
    )

# Add the API urls:
api_router = routers.DefaultRouter()
if settings.ENABLED_FEATURES['hansard']:
    from pombola.hansard.api.views import (
        EntryViewSet, SittingViewSet, SourceViewSet, VenueViewSet
    )
    api_router.register(r'hansard/entries', EntryViewSet)
    api_router.register(r'hansard/sittings', SittingViewSet, base_name='sitting')
    api_router.register(r'hansard/sources', SourceViewSet)
    api_router.register(r'hansard/venues', VenueViewSet)

urlpatterns += (
    url(r'^api/(?P<version>v0.1)/', include(api_router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)

from ajax_select import urls as ajax_select_urls
urlpatterns += (
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/lookups/', include(ajax_select_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete_light/', include('autocomplete_light.urls')),
)

# mapit
urlpatterns += (
    url(r'^mapit/', include('mapit.urls')),
)

# Info pages
urlpatterns += (
    url(r'^info/', include('info.urls.pages')),
    url(r'^blog/', include('info.urls.blog')),
)

# File archive
urlpatterns += (
    url(r'^file_archive/', include('file_archive.urls')),
)

# SayIt - speeches
#if settings.ENABLED_FEATURES['speeches']:
#    urlpatterns += (
#        url(r'^speeches/', include('speeches.urls', namespace='speeches', app_name='speeches-default')),
#    )

# Hansard pages
if settings.ENABLED_FEATURES['hansard']:
    urlpatterns += (
        url(r'^hansard/', include('pombola.hansard.urls', namespace='hansard', app_name='hansard')),
    )

# Project pages
if settings.ENABLED_FEATURES['projects']:
    urlpatterns += (
        url(r'^projects/', include('pombola.projects.urls')),
    )

# ajax preview of the markdown
urlpatterns += (
    url(r'^markitup/', include('markitup.urls')),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# needed for the selenium tests.
if settings.IN_TEST_MODE:
    static_url = re.escape(settings.STATIC_URL.lstrip('/'))
    urlpatterns += (
        url(r'^%s(?P<path>.*)$' % static_url, serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    )

# search
urlpatterns += (
    url(r'^search/', include('pombola.search.urls')),
)

# wordcloud
if settings.ENABLED_FEATURES['wordcloud']:
    urlpatterns += (
        url(r'^wordcloud/', include('pombola.wordcloud.urls')),

        # Temporarily keep tagcloud version of the url as well.
        url(r'^tagcloud/', include('pombola.wordcloud.urls')),
    )

# feedback
urlpatterns += (
    url(r'^feedback/', include('pombola.feedback.urls')),
)

# map
urlpatterns += (
    url(r'^map/', include('pombola.map.urls')),
)

# votematch
if settings.ENABLED_FEATURES['votematch']:
    urlpatterns += (
        url(r'^votematch/', include('pombola.votematch.urls')),
    )


# # spinner - uncomment if needed. Not needed just to display spinner on the
# # homepage using carousel.
# if settings.ENABLED_FEATURES['spinner']:
#     urlpatterns += (
#         url(r'^spinner/', include('pombola.spinner.urls')),
#     )

# bills
if settings.ENABLED_FEATURES['bills']:
    urlpatterns += (
        url(r'^bills/', include('pombola.bills.urls', namespace='bills', app_name='bills')),
    )


# Everything else goes to core
urlpatterns += (
    url(r'^', include('pombola.core.urls')),
)
