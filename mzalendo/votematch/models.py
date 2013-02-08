from django.db import models
from model_utils.models import TimeStampedModel
from markitup.fields import MarkupField
from random import choice

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


class Statement(TimeStampedModel):
    """ eg 'Cannabis SHOULD be legalised' """
    quiz = models.ForeignKey('Quiz')
    text = models.TextField()


class Party(TimeStampedModel):
    """ eg 'Mitt Romney' or 'Lib Dems' """
    quiz = models.ForeignKey('Quiz')
    name = models.TextField()
    summary = MarkupField()


class Stance(TimeStampedModel):
    """eg 'LibDems' <strongly agree> with 'Cannabis should be legalised' """
    statement = models.ForeignKey('Statement')
    party = models.ForeignKey('Party')
    agreement = models.IntegerField(choices=agreement_choices)


class Submission(TimeStampedModel):
    """ a single submission of answers for the quiz, and some demographic data """
    quiz = models.ForeignKey('Quiz')    
    token = models.TextField(default=generate_token, unique=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    expected_result = models.ForeignKey('Party')


class Answer(TimeStampedModel):
    """A visitor's agreement with a given statement"""
    submission = models.ForeignKey('Submission')
    statement  = models.ForeignKey('Statement')
    agreement = models.IntegerField(choices=agreement_choices)
    
    
     