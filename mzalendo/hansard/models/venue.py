from django.db import models

class Venue(models.Model):
    """
    Venues for the sittings
    """

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200, unique=True)
    
    class Meta:
        app_label = 'hansard'
        ordering = [ 'slug' ]

    def __unicode__(self):
        return self.name
