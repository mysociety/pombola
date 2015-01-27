from django.conf.urls import patterns, url

from pombola.bills.views import IndexView, BillListView

urlpatterns = patterns('pombola.bills.views',
    url( r'^$', IndexView.as_view(), name="index" ),
    url( r'^(?P<session_slug>[\w\-]+)/$', BillListView.as_view(), name="list" ),
)
