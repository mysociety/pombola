import datetime

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

from core.models import Place


class Project(models.Model):
    created = models.DateTimeField( auto_now_add=True, default=datetime.datetime.now(), )
    updated = models.DateTimeField( auto_now=True,     default=datetime.datetime.now(), )    

    cdf_index = models.IntegerField( unique=True)

    constituency = models.ForeignKey(Place)

    project_name  = models.CharField(max_length=400)
    location_name = models.CharField(max_length=400)

    sector      = models.CharField(max_length=400)
    mtfe_sector = models.CharField(max_length=400)
    econ1       = models.CharField(max_length=400)
    econ2       = models.CharField(max_length=400)

    activity_to_be_done = models.CharField(max_length=400)
    expected_output     = models.CharField(max_length=400)
    status              = models.CharField(max_length=400)
    remarks             = models.CharField(max_length=400)

    estimated_cost = models.FloatField()
    total_cost     = models.FloatField()

    location = models.PointField()
        

