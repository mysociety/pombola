import datetime
import re
from warnings import warn

# from django.contrib.contenttypes import generic
# from django.contrib.contenttypes.models import ContentType
# from django.core.urlresolvers import reverse
from django.db import models
# from django.db.models import Q

# Note - the name 'chunk' is deliberately bad. This code is mainly intended to
# be a quick proof-of-concept. It should be refactored into something more
# robust and better structured.

class Chunk(models.Model):

    type_choices = (
        ('heading', 'Heading'),
        ('speech',  'Speech'),
        ('unknown', 'Unknown'),
        ('event',   'Description of event'),
    )

    type         = models.CharField(max_length=20, choices=type_choices)
    date         = models.DateField()
    session      = models.CharField(max_length=2, choices=(('am', 'Morning'),('pm','Afternoon')))
    page         = models.IntegerField()
    text_counter = models.IntegerField()
    speaker      = models.CharField(max_length=200, blank=True)
    content      = models.TextField()
    source       = models.CharField(max_length=500)

    def __unicode__(self):
        return self.content[:100]

    class Meta:
        pass
        # ordering = ["slug"]      

