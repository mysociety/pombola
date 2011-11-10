from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns( 'comments2.views',
    url(r'^for/(?P<module_name>[a-z]+)/(?P<slug>[\w\-]+)/add/', 'add' ),
    url(r'^for/(?P<module_name>[a-z]+)/(?P<slug>[\w\-]+)/',     'list_for' ),

    url(r'^flag/(?P<comment_id>\d+)/', 'flag' ),

    url(r'^view/(?P<comment_id>\d+)/', 'view', name='comments-view' ),

    # url(r'^post/$',          'post_comment',       name='comments-post-comment'),
    # url(r'^posted/$',        'comment_done',       name='comments-comment-done'),
    # url(r'^flag/(\d+)/$',    'moderation.flag',             name='comments-flag'),
    # url(r'^flagged/$',       'moderation.flag_done',        name='comments-flag-done'),
    # url(r'^delete/(\d+)/$',  'moderation.delete',           name='comments-delete'),
    # url(r'^deleted/$',       'moderation.delete_done',      name='comments-delete-done'),
    # url(r'^approve/(\d+)/$', 'moderation.approve',          name='comments-approve'),
    # url(r'^approved/$',      'moderation.approve_done',     name='comments-approve-done'),

)
