from django.conf.urls import url

from . import views


write_message_wizard = views.WriteInPublicNewMessage.as_view(url_name='writeinpublic-new-message-step')

urlpatterns = (
    url(
        r'^message/(?P<message_id>\d+)/$',
        views.WriteInPublicMessage.as_view(),
        name='writeinpublic-message'
    ),
    url(
        r'^(?P<step>.+)/$',
        write_message_wizard,
        name='writeinpublic-new-message-step',
    ),
    url(
        r'^$',
        write_message_wizard,
        name='writeinpublic-new-message',
    ),
)
