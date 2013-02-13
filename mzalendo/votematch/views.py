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
    

# convert the db stored agreement values into something that is more
# representative of the relative weightings that they actually carry.
agreement_fiddle_factor = {
    -2: -9,
    -1: -3,
     0:  0,
     1:  3,
     3:  9,
}

def submission_detail (request, slug, token):

    # TODO - we're not checking that the quiz slug is correct. We don't really
    # care - but should probably check just to be correct.

    submission = get_object_or_404(
        models.Submission,
        token = token
    )
    
    quiz = submission.quiz
    
    # NB - this code written after bumping into numerous issues stemming from
    # Django's insistance that templates not have useful features like
    # variables, or variable key lookups in dictionaries. Hence subsequent
    # comments may be a bit brusque.
    
    # This code could be moved to the Submission model, but I think as it
    # is just to produce the data that the template needs, in a form that the
    # template needs, it is probably better off here in the view.

    # put all the parties in a list. We need to fix their order because we can
    # key into a data structure in the template so need to prepare everything
    # here in the order that the table will need it. Tight coupling between
    # template and logic? Why yes!
    parties = quiz.party_set.all().order_by('name')

    # In the template the table will have rows with like:
    #
    #   statement text  |  submission answer  |  parties[0] stance  |  ....
    # 
    # so create an array of items that will be needed to create these rows.
    rows = []
    for statement in quiz.statement_set.all().order_by('text'):
        entry = {}
        entry['statement'] = statement

        # get the answer, or None if user has not answered
        try:
            entry['answer'] = submission.answer_set.get(statement=statement)
        except models.Answer.DoesNotExist:
            entry['answer'] = None
        
        # Get the stance for each party in the parties list. This becomes an
        # array in which the order is important.
        entry['party_stances'] = []
        for party in parties:
            try:
                stance = party.stance_set.get(statement=statement)
            except models.Stance.DoesNotExist:
                stance = None
            entry['party_stances'].append(stance)

        # just for giggles the above lines would have been this in Perl:
        # $entry{party_stances} = [ map { $party->stance_set->get({ statement => $statement}); } @parties ];

        rows.append(entry)


    return render_to_response(
        'votematch/submission_detail.html',
        {
            'object':     submission,
            'submission': submission,
            'quiz':       quiz,
            'parties':    parties,
            'rows':       rows,
        },
        context_instance=RequestContext(request)
    )
    