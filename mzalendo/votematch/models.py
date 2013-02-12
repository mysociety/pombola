from django.db import models
from model_utils.models import TimeStampedModel
from markitup.fields import MarkupField
from random import choice

from django.core.urlresolvers import reverse

agreement_choices = (
    (-2, 'strongly disagree'),
    (-1, 'disagree'),
    ( 0, 'neutral'),
    ( 1, 'agree'),
    ( 2, 'strongly agree'),
)

def generate_token():
    chars  = 'abcdef0123456789'
    length = 8
    return ''.join([choice(chars) for i in range(length)])


class Quiz(TimeStampedModel):
    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")

    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('votematch-quiz', kwargs={'slug':self.slug})

    class Meta:
        verbose_name_plural = "quizzes"


class Statement(TimeStampedModel):
    """ eg 'Cannabis SHOULD be legalised' """
    quiz = models.ForeignKey('Quiz')
    text = models.TextField()

    def __unicode__(self):
        return "%s (%s)" % ( self.text, self.quiz )


class Party(TimeStampedModel):
    """ eg 'Mitt Romney' or 'Lib Dems' """
    quiz = models.ForeignKey('Quiz')
    name = models.TextField()
    summary = MarkupField()

    def __unicode__(self):
        return "%s (%s)" % ( self.name, self.quiz )

    class Meta:
        verbose_name_plural = "parties"


class Stance(TimeStampedModel):
    """eg 'LibDems' <strongly agree> with 'Cannabis should be legalised' """
    statement = models.ForeignKey('Statement')
    party = models.ForeignKey('Party')
    agreement = models.IntegerField(choices=agreement_choices)

    def __unicode__(self):
        return "%s - %s - %s" % ( self.party.name, self.get_agreement_display(), self.statement.text )


class Submission(TimeStampedModel):
    """ a single submission of answers for the quiz, and some demographic data """
    quiz            = models.ForeignKey('Quiz')    
    token           = models.TextField(default=generate_token, unique=True)
    age             = models.PositiveIntegerField(blank=True, null=True)
    expected_result = models.ForeignKey('Party', blank=True, null=True)

    def __unicode__(self):
        return "%s (%s)" % ( self.token, self.quiz )
    
    def get_absolute_url(self):
        return reverse(
            'votematch-submission',
            kwargs = {
                'slug':  self.quiz.slug,
                'token': self.token
            }
        )

    

class Answer(TimeStampedModel):
    """A visitor's agreement with a given statement"""
    submission = models.ForeignKey('Submission')
    statement  = models.ForeignKey('Statement')
    agreement  = models.IntegerField(choices=agreement_choices)
    
    def __unicode__(self):
        return "%s - %s - %s" % ( self.submission, self.get_agreement_display(), self.statement.text )
    
     