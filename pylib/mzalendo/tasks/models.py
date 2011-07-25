from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Task(models.Model):

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    task_code     = models.SlugField(max_length=100)

    created       = models.DateTimeField(auto_now_add=True)
    defer_until   = models.DateTimeField(auto_now_add=True)
    attempt_count = models.PositiveIntegerField(default=0)
    
    log  = models.TextField()
    note = models.TextField(blank=True, help_text="publicaly visible, use to clarify contact detail")

    def __unicode__(self):
        return "%s for %s" % ( self.task_code, self.content_object )

    class Meta:
       ordering = ["content_type", "object_id", "task_code", ]      
