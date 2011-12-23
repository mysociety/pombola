from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

from models import Feedback
from forms import FeedbackForm

@csrf_protect
def add(request):
    """Gather feedback for a page, and if it is ok show a thanks message and link back to the page."""

    submit_was_success = False
    return_to_url      = None

    # If it is a post request try to create the feedback
    if request.method == 'POST':
        form = FeedbackForm( request.POST )
        if form.is_valid():
            feedback = Feedback()
            feedback.url      = form.cleaned_data['url']
            feedback.comment  = form.cleaned_data['comment']

            if request.user.is_authenticated():
                feedback.user = request.user

            feedback.save()

            submit_was_success = True
            return_to_url = feedback.url or None
        
    else:
        # use GET to grab the url if set
        form = FeedbackForm(initial=request.GET)
        
    
    return render_to_response(
        'feedback/add.html',
        {
            'form':               form,
            'submit_was_success': submit_was_success,
            'return_to_url':      return_to_url,
        },
        context_instance=RequestContext(request)
    )
