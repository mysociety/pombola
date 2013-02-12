from django.conf.urls.defaults import patterns, include, url

from django.views.generic import ListView, DetailView

from .models import Quiz, Submission



urlpatterns = patterns( 'votematch.views',

    # .../                # list of quizzes
    url( r'^$', ListView.as_view(model=Quiz), name='votematch-quiz-list' ),

    # .../<slug>/         # individual quiz form (submit on POST)
    url( r'^(?P<slug>[-\w]+)/$', 'quiz_detail', name='votematch-quiz' ),

    # .../<slug>/<token>/ # individual result
    # Can't use a detail view as that wants a pk or a slug. Does not like 'token'...
    url( r'^(?P<slug>[-\w]+)/(?P<token>[-\w]+)/$', 'submission_detail', name='votematch-submission' ),
)


