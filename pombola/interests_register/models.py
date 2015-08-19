from django.db import models
from django.utils.text import slugify

from pombola.core.models import PopoloPerson


# TODO
#
# - add a source for the data, possibly as a field on the Release?
# - resolve how to differentiate between items that are one-offs (like gift to person) and ongoing (like employment or land ownership). Concern is that one-offs may get lost if only the latest release is shown, or duplicated if they are included in several releases.


class CreateSlugOnSaveIfNeededModel(models.Model):

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(CreateSlugOnSaveIfNeededModel, self).save(*args, **kwargs)

    class Meta(object):
        abstract = True


class Category(CreateSlugOnSaveIfNeededModel):
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(unique=True)

    sort_order = models.IntegerField()

    def __unicode__(self):
        return self.name

    class Meta(object):
        ordering = ('sort_order', 'name')
        verbose_name_plural = 'categories'


class Release(CreateSlugOnSaveIfNeededModel):
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(unique=True)
    date = models.DateField()

    def __unicode__(self):
        return self.name

    class Meta(object):
        ordering = ('date', 'name')


class Entry(models.Model):
    person = models.ForeignKey(PopoloPerson, related_name='interests_register_entries')
    category = models.ForeignKey(Category, related_name="entries")
    release  = models.ForeignKey(Release, related_name="entries")

    sort_order = models.IntegerField()

    def __unicode__(self):
        return u'Entry for {0} in {1} ({2})'.format(self.person, self.category, self.release)

    class Meta(object):
        ordering = ('person__legal_name', '-release__date', 'category__sort_order', 'category__name', 'sort_order')
        verbose_name_plural = 'entries'


class EntryLineItem(models.Model):
    entry     = models.ForeignKey(Entry, related_name="line_items")
    key       = models.CharField(max_length=240)
    value     = models.TextField()

    def __unicode__(self):
        return u"{0}: {1}".format(self.key, self.value)

