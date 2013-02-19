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

        differences = { 0:0, 1:0, 2:0, 3:0, 4:0, 'x':0 }
        statement_count  = quiz.statement_set.count()
        difference_count = 0
        difference_total = 0
        percent_per_diff = 100.0 / statement_count
        for statement in quiz.statement_set.all():
            
            # calculate difference between the answer and stance
            try:
                answer = submission.answer_set.get(statement=statement)
                stance = party.stance_set.get(statement=statement)
                diff = abs( answer.agreement - stance.agreement)
                difference_count += 1
                difference_total += diff ** 1.5  # make bigger differences count more
                differences[diff] += percent_per_diff
            except ObjectDoesNotExist:
                differences['x'] += percent_per_diff

        if difference_count:
            score = difference_total / float(difference_count)
        else:
            score = 0
        
        results.append({
            'score':       score,
            'sort_score':  score or 1000000,
            'differences': differences,
            'party':       party,
        })
        
    # sort the results by the score. Lower score means better average match
    results.sort(key=lambda x: x['sort_score'])

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
