from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

# This is based on
# https://github.com/dracos/Theatricalia/blob/master/merged/models.py
# but adapted for redirecting from an old slug rather than ID.

class SlugRedirect(models.Model):
    """A model to represent a redirect from an old slug

    This is particular useful if you're merging two records, but you
    don't want the old URL to break.  It's also useful if you need to
    change a slug.
    """

    content_type = models.ForeignKey(ContentType)
    old_object_slug = models.CharField(max_length=200)
    new_object_id = models.PositiveIntegerField()
    new_object = GenericForeignKey('content_type', 'new_object_id')

    created = models.DateTimeField( auto_now_add=True )
    updated = models.DateTimeField( auto_now=True )

    def __unicode__(self):
        return u'slug "%s" -> %s' % (self.old_object_slug, self.new_object)

    class Meta:
        unique_together = ("content_type", "old_object_slug")
