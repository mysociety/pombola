from django.db import models

from sorl.thumbnail import ImageField


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
