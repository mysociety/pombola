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
    
