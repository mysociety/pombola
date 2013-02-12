import models

from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext

def quiz_detail (request, slug):
    quiz = get_object_or_404(
        models.Quiz,
        slug=slug
    )
    
    return render_to_response(
        'votematch/quiz_detail.html',
        {
            'object':     quiz,
            'choices':    models.agreement_choices,
        },
        context_instance=RequestContext(request)
    )
    

def submission_detail (request, slug, token):

    # TODO - we're not checking that the quiz slug is correct. We don't really
    # care - but should probably check just to be correct.

    submission = get_object_or_404(
        models.Submission,
        token = token
    )

    return render_to_response(
        'votematch/submission_detail.html',
        {
            'object':     submission,
        },
        context_instance=RequestContext(request)
    )
    