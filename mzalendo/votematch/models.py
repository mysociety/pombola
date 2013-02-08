from django.db import models
from model_utils.models import TimeStampedModel
from markitup.fields import MarkupField


agreement_choices = (
    (-2, 'strongly disagree'),
    (-1, 'disagree'),
    ( 0, 'neutral'),
    ( 1, 'agree'),
    ( 2, 'strongly agree'),
)

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

