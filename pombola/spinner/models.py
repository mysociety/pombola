from django.db import models

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from django.template.loader import get_template, TemplateDoesNotExist
from django.utils.text import slugify

from sorl.thumbnail import ImageField


class SlideQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class SlideManager(models.Manager):
    def get_queryset(self):
        return SlideQuerySet(self.model, using=self._db)

    # Commented out as unused, but possibly useful in future

    # def random_slide(self):
    #     try:
    #         return self.all().active().order_by('?')[0]
    #     except IndexError:
    #         # There are no slides to can be returned.
    #         return None
    #
    # def slide_after(self, slide=None):
    #     """
    #     Return the slide after this one, or first slide if None, or None if no
    #     slides active. Handles looping at the end.
    #     """
    #
    #     # We only care about the active slides.
    #     all_active = self.all().active().order_by('sort_order', 'id')
    #
    #     # If there is no slide to compare to just return the first one, or None
    #     if slide:
    #
    #         # Filter for those of equal or greater sort_order.
    #         slides = all_active.filter(sort_order__gte=slide.sort_order)
    #
    #         # If the first one has a higher sort_order return it
    #         if slides.count():
    #             if slides[0].sort_order != slide.sort_order:
    #                 return slides[0]
    #             else:
    #                 id_filtered = slides.filter(id__gt=slide.id)
    #                 if id_filtered.count():
    #                     # We have a slide of equal sort_order, but greater id.
    #                     return id_filtered[0]
    #
    #     # Could not find a slide above. Return first one we can find, or None.
    #     try:
    #         return all_active[0]
    #     except IndexError:
    #         return None


class Slide(models.Model):

    template_name_str_template = "spinner/slides/%s.html"

    sort_order = models.IntegerField()
    is_active = models.BooleanField(default=True)

    # link to other objects using the ContentType system
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = SlideManager()

    def __unicode__(self):
        return u"Slide of '{0}'".format( self.content_object )

    @property
    def template_class(self):
        content_type = self.content_type
        return slugify("%s_%s" % (content_type.app_label, self.content_type))

    @property
    def required_template_name(self):
        return self.template_name_str_template % self.template_class

    @property
    def template_name(self):
        template_name = self.required_template_name

        try:
            # Use the following line to check that there is a template that can be used, otherwise use the default template.
            get_template(template_name)
            return template_name
        except TemplateDoesNotExist:
            return self.template_name_str_template % "default"


    class Meta(object):
        ordering = ( 'sort_order', 'id' )


class ImageContent(models.Model):
    """
    Model for image content for the spinner.
    """
    image = ImageField(upload_to="spinner_images")
    caption = models.CharField(max_length=300)
    description = models.CharField(max_length=250, blank=True)
    url = models.URLField()

    def __unicode__(self):
        return self.caption

    class Meta(object):
        verbose_name_plural = 'images'


class QuoteContent(models.Model):
    """
    Model for image content for the spinner.
    """
    quote = models.TextField()
    attribution = models.CharField(max_length=300)
    url = models.URLField()

    def __unicode__(self):
        return self.quote

    class Meta(object):
        verbose_name_plural = 'quotes'

