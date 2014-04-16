import datetime
import os

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

from pombola.core.models import SlugRedirect


class File(models.Model):    
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now, )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now, )

    slug = models.SlugField( unique=True )
    file = models.FileField( upload_to='file_archive' )

    def __unicode__(self):
        return self.slug

    def save(self, *args, **kwargs):
        ideal_slug = slugify(os.path.basename(
            os.path.splitext(self.file.name)[0]))
        if not ideal_slug:
            raise Exception(
                u'Creating a slug from {0} failed'.format(self.file.name))
        if self.slug and (ideal_slug != self.slug):
            # Then if there was an old slug, try to create a redirect
            # for it:
            SlugRedirect.objects.create(
                content_type=ContentType.objects.get_for_model(File),
                old_object_slug=self.slug,
                new_object_id=self.id,
                new_object=self)
        self.slug = ideal_slug
        return super(File, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ( 'file_archive', [ self.slug ] )
