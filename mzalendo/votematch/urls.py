from django.conf.urls.defaults import patterns, include, url

from django.views.generic import ListView, DetailView

from .models import Quiz



urlpatterns = patterns( '',

    # .../                # list of quizzes
    url( r'^$', ListView.as_view(model=Quiz), name='votematch-quiz-list' ),

    # .../<slug>/         # individual quiz form (submit on POST)
    url( r'^(?P<slug>[-\w]+)/$', DetailView.as_view(model=Quiz), name='votematch-quiz' ),

    # .../<slug>/<token>/ # individual result

)


