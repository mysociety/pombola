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

        # get the demographic details 
        try:
            age = int(request.POST.get('age'))
        except ValueError:
            # some silly value entered
            age = None
                
        expected_result_id = request.POST.get('expected_result')
        expected_result = None
        if expected_result_id:
            try:
                expected_result = quiz.party_set.filter(id=expected_result_id)[0]
            except:
                # ignore errors - not really important and not worth reporting back to user.
                pass

        # get all the answers
        if len(answers):
            submission = models.Submission.objects.create(
                quiz            = quiz,
                age             = age,
                expected_result = expected_result
            )
            
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
    -2: -3,
    -1: -1,
     0:  0,
     1:  1,
     2:  3,
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

    # now to work out which party most closely matches the answers given. We
    # could store this in the submission model, but it is easier just to
    # recalculate it as that avoids having to be smart when statements are
    # added or removed, or the stances are changed.

    # create a hash to store the running tally in. Initialize all values to zero.
    differences_to_party = {}
    for party in parties:
        differences_to_party[party.id] = []

    # for each row store the differences (if there was an answer)
    for row in rows:
        answer = row['answer']
        for stance in row['party_stances']:
            if stance and answer:
                answer_score = agreement_fiddle_factor[ answer.agreement ]
                stance_score = agreement_fiddle_factor[ stance.agreement ]
                differences_to_party[stance.party.id].append( abs(answer_score - stance_score) )

    # create a score per party - which is average of differences
    party_scores = {}
    for party in parties:
        differences = differences_to_party[party.id]
        party_scores[party.id] = average(differences)
        
    # calculate the average score that can be used to sort of center results
    average_score = average(party_scores.values())
    
    # create an arry with the parties in order
    party_results = []
    for party in sorted( list(parties), key=lambda p: party_scores[p.id] ):
        party_results.append({
            'party': party,
            'score': - party_scores[party.id] + average_score, # fudged to give appearance of a spread over center
        })


    return render_to_response(
        'votematch/submission_detail.html',
        {
            'object':     submission,
            'submission': submission,
            'quiz':       quiz,
            'parties':    parties,
            'rows':       rows,
            'party_results': party_results,
        },
        context_instance=RequestContext(request)
    )

def average(l):
    return sum(l) / float(len(l))