import datetime

from django.db import models
from django.contrib.auth.models import User


class Feedback(models.Model):
    """A very simple model to store feedback from users (either logged in or anonymous)"""
    
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user    = models.ForeignKey( User, blank=True, null=True )
    email   = models.EmailField( blank=True, help_text="Please let us have your email address so that we can get back to you." )
    url     = models.URLField( blank=True )
    comment = models.CharField(max_length=2000)
    
    status = models.CharField(
        max_length = 20,
        default = 'pending',
        choices = (
            ( 'pending',        'Pending' ),
            ( 'rejected',       'Rejected' ),
            ( 'applied',        'Applied' ),
            ( 'non-actionable', 'Non-actionable' ),
            ( 'spammy',         'Possible Spam'),
        ),
    )
    
    response = models.TextField( blank=True )

    def __unicode__(self):
        return self.comment[:100]
    
    class Meta:
       ordering = ["created", ]
       verbose_name_plural = 'feedback'
       

