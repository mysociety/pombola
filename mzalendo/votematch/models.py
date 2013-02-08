from django.db import models
from model_utils.models import TimeStampedModel
# Create your models here.


class Quiz(TimeStampedModel):
    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="created from name")


class Statement(TimeStampedModel):
    quiz = models.ForeignKey('Quiz')
    text = models.TextField()





