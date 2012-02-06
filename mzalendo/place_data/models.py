from django.db import models

from mzalendo.core import models as core_models

# For the moment we'll do a very basic table which just
# has a column for each type of data we currently know.
# Later we could switch to doing something like the commented out
# more general stuff at the bottom of this file.

class Entry(models.Model):
    place = models.OneToOneField(core_models.Place, related_name='placedata')

    population_male = models.PositiveIntegerField()
    population_female = models.PositiveIntegerField()
    population_total = models.PositiveIntegerField()

    households_total = models.PositiveIntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=2)

# class DataCategory(models.Model):
#     DATA_TYPE_CHOICES = (
#         ('value_int', 'Integer'),
#         ('value_decimal', 'Decimal'),
#         )

#     slug = models.SlugField(max_length=100, unique=True)
#     name = models.CharField(max_length=100)
#     data_type = models.SlugField(choices=DATA_TYPE_CHOICES)

# class DataEntry(models.Model):
#     category = models.ForeignKey(DataCategory)

#     content_type = models.ForeignKey(ContentType)
#     object_id = models.PositiveIntegerField()
#     content_object = generic.GenericForeignKey('content_type', 'object_id')

#     # Only one of these should be filled in, and which one you should
#     # Be able to tell from the category
#     value_int = models.BigIntegerField(null=True, blank=True)
#     value_decimal = models.DecimalField(null=True, blank=True)
