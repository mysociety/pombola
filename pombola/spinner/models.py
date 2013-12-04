from django.db import models

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from sorl.thumbnail import ImageField


class Slide(models.Model):
    sort_order = models.IntegerField()
    is_active = models.BooleanField(default=True)

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"Slide of '{}'".format(str(self.content_object))

    class Meta(object):
        ordering = ( 'sort_order', 'id' )


class ImageContent(models.Model):
    """
    Model for image content for the spinner.
    """
    image = ImageField(upload_to="spinner_images")
    caption = models.CharField(max_length=300)
    url = models.URLField()

    def __unicode__(self):
        return self.caption

    class Meta(object):
        verbose_name_plural = 'images'
