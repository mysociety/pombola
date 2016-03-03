from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.apps import apps

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

# This is a validator you can use on any model's slug field to check
# that its slug isn't already being redirected. To use it you should
# use functools.partial to supply the model class.

def validate_slug_not_redirecting(app_label, model_name, slug):
    """A function for building validator functions for any model's slug field

    You can use this to build a validator for any model's slug field
    to check that you're not trying to use a slug that's already
    redirecting to some other instance of the model.  It's easiest to
    do this with functools.partial, e.g.:

        validators=[partial(validate_slug_not_redirecting, 'core', 'Person')]
    """

    model = apps.get_model(app_label, model_name)
    matching_redirects = SlugRedirect.objects.filter(
        content_type=ContentType.objects.get_for_model(model),
        old_object_slug=slug
    )
    if matching_redirects:
        message = 'There is already slug redirection in place for {0}: {1}'
        raise ValidationError(
            message.format(slug, matching_redirects[0])
        )
