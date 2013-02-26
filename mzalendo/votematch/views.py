import models

from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.template   import RequestContext
from django.core.exceptions import ObjectDoesNotExist


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
    


# Mapping of the difference to the scores. This is to allow us to compare the
# stances from the party and the user.
#
# Attempts to create a score that mixes the size of the disagreement with the
# strength of the stance. Hence if either party are neutral the score is zero,
# if either party holds a feling the score scales up to a maximum of +-9.
#
# Done as a nested hash for now with the structure:
#   hash[party_stance][user stance]
#
stance_to_score_mapping = {
       -2:     { -2:  9,  -1:  3,  0: 0,  1: -3,  2: -9 },
       -1:     { -2:  4,  -1:  2,  0: 0,  1: -2,  2: -4 },
        0:     { -2:  0,  -1:  0,  0: 0,  1:  0,  2:  0 },
        1:     { -2: -4,  -1: -2,  0: 0,  1:  2,  2:  4 },
        2:     { -2: -9,  -1: -3,  0: 0,  1:  3,  2:  9 },
}

def submission_detail (request, slug, token):

    # TODO - we're not checking that the quiz slug is correct. We don't really
    # care - but should probably check just to be correct.

    submission = get_object_or_404(
        models.Submission,
        token = token
    )
    
    quiz = submission.quiz

    results = []
    for party in quiz.party_set.all():
        total_score = 0

        for statement in quiz.statement_set.all():
            try:
                answer = submission.answer_set.get(statement=statement)
                stance = party.stance_set.get(statement=statement)
                score = stance_to_score_mapping[stance.agreement][answer.agreement]
                total_score += score
            except ObjectDoesNotExist:
                # One of the stances is missing. no change to score.
                total_score += 0

        results.append({
            'score':          total_score,
            'party':          party,
        })

    # Useful for manually testing different scores.
    # results[0]['score'] = 4
    # results[1]['score'] = 0

    # sort the results by the score. Lower score means better average match
    results.sort(key=lambda x: -x['score'])

    # get the max abs(score), and for each result store the percentage of it
    max_score = max( [abs(x['score']) for x in results] )
    for result in results:
        result['score_percentage'] = abs(result['score']) / float(max_score) * 100

    return render_to_response(
       'votematch/submission_detail.html',
       {
           'object':     submission,
           'submission': submission,
           'quiz':       quiz,
           'results':    results,
       },
       context_instance=RequestContext(request)
    )
