from django.conf.urls import url

from . import views


write_message_wizard = views.SAWriteInPublicNewMessage.as_view(url_name='sa-writeinpublic-new-message-step')

urlpatterns = (
    url(
        r'^message/(?P<message_id>\d+)/$',
        views.SAWriteInPublicMessage.as_view(),
        name='sa-writeinpublic-message'
    ),
    url(
        r'^(?P<step>.+)/$',
        write_message_wizard,
        name='sa-writeinpublic-new-message-step',
    ),
    url(
        r'^$',
        write_message_wizard,
        name='sa-writeinpublic-new-message',
    ),
)
