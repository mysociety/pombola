import models

from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext


def quiz_detail (request, slug):

    quiz = get_object_or_404(
        models.Quiz,
        slug=slug
    )
    
    # If this is a POST then extract all the answers
    if request.method == 'POST':

        # get the answers. Use the current set of statements to look for
        # submitted values. Ignore anything that is not expected.
        answers    = {}
        statements = {}
        for statement in quiz.statement_set.all():
            statements[statement.id] = statement
            val = request.POST.get( 'statement-' + str(statement.id) )
            if len( val ): # ignore "" which is used for 'don't know' defaults
                answers[statement.id] = int(val)
                
        if len(answers):
            submission = models.Submission.objects.create(quiz=quiz)
            
            for statement_id, answer in answers.iteritems():
                submission.answer_set.create(
                    statement = statements[statement_id],
                    agreement = answer
                )

            return redirect(submission)


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
    