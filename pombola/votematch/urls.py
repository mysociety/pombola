from django.conf.urls import patterns, url

from django.views.generic import ListView, TemplateView

from .models import Quiz


urlpatterns = patterns( 'pombola.votematch.views',

    # .../                # list of quizzes
    url( r'^$', ListView.as_view(model=Quiz), name='votematch-quiz-list' ),

    # .../scoring/        # How the scores are calculated
    url( r'^scoring/$', TemplateView.as_view(template_name='votematch/scoring.html'), name='votematch-scoring' ),

    # .../<slug>/         # individual quiz form (submit on POST)
    url( r'^(?P<slug>[-\w]+)/$', 'quiz_detail', name='votematch-quiz' ),

    # .../<slug>/<token>/ # individual result
    # Can't use a detail view as that wants a pk or a slug. Does not like 'token'...
    url( r'^(?P<slug>[-\w]+)/(?P<token>[-\w]+)/$', 'submission_detail', name='votematch-submission' ),
)
