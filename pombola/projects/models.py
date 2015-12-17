import datetime

from django.contrib.gis.db import models

from pombola.core.models import Place


class Project(models.Model):
    created = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now)

    cdf_index = models.IntegerField(unique=True)

    constituency = models.ForeignKey(Place)

    project_name = models.CharField(max_length=400)
    location_name = models.CharField(max_length=400)

    sector = models.CharField(max_length=400)
    mtfe_sector = models.CharField(max_length=400)
    econ1 = models.CharField(max_length=400)
    econ2 = models.CharField(max_length=400)

    activity_to_be_done = models.CharField(max_length=400)
    expected_output = models.CharField(max_length=400)
    status = models.CharField(max_length=400)
    remarks = models.CharField(max_length=400)

    estimated_cost = models.FloatField()
    total_cost = models.FloatField()

    first_funding_year = models.IntegerField(blank=True, null=True)

    location = models.PointField(srid=4326)

    class Meta():
        # NOTE - the templates rely on this default ordering. Really we should
        # use a custom manager and query_set and 'use_for_related_fields = True'
        # but currently Django is broken:
        # https://code.djangoproject.com/ticket/14891
        # The other work-around of creating a method on the place to access the
        # correct manager for the projects is likely to cause confusion.
        ordering = ['-total_cost'] # <--- DO NOT CHANGE
