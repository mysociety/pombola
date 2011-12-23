import datetime

from django.db import models
from django.contrib.auth.models import User


class Feedback(models.Model):
    """A very simple model to store feedback from users (either logged in or anonymous)"""
    
    
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    user    = models.ForeignKey( User, blank=True, null=True )
    url     = models.URLField( blank=True )
    comment = models.TextField()

    def __unicode__(self):
        return self.comment[:100]
    
    class Meta:
       ordering = ["created", ]
       verbose_name_plural = 'feedback'
       

