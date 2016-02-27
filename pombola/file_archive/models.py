from django.db import models

import datetime



class File(models.Model):    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    slug = models.SlugField( unique=True )
    file = models.FileField( upload_to='file_archive' )

    def __unicode__(self):
        return self.slug

    @models.permalink
    def get_absolute_url(self):
        return ( 'file_archive', [ self.slug ] )

