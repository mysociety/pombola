from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from sorl.thumbnail import ImageField

from warnings import warn

class Image(models.Model):

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # store the actual image
    image = ImageField( upload_to="images" )

    # added
    source = models.CharField(max_length=400)
    # user
    
    is_primary = models.BooleanField( default=False )
    
    def save(self, *args, **kwargs):
        """
        Only one image should be marked as is_primary for an object.
        """
        
        # other images for this object
        siblings = Image.objects.filter(
            content_type = self.content_type,
            object_id    = self.object_id,
        )
        
        # check that we are not first entry for content_object
        if not siblings.count():
            self.is_primary = True

        super(Image, self).save(*args, **kwargs)

        # If we are true then make sure all others are false
        if self.is_primary is True:

            primary_siblings = siblings.exclude( is_primary = False ).exclude( id = self.id )

            for sibling in primary_siblings:
                sibling.is_primary = False
                sibling.save()


class HasImageMixin():

    def primary_image(self):
        primary = [i for i in self.images.all() if i.is_primary]
        if primary:
            return primary[0].image
        return None
