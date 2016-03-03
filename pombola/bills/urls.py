from django.conf.urls import url

from pombola.bills.views import IndexView, BillListView


urlpatterns = [
    url( r'^$', IndexView.as_view(), name="index" ),
    url( r'^(?P<session_slug>[\w\-]+)/$', BillListView.as_view(), name="list" ),
]
